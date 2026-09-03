"""
Script de enriquecimento (etapa 2): identifica subsidiarias de grupos
estrangeiros, mesmo quando a empresa tem CNPJ e domicilio legal no
Brasil.

Diferenca em relacao ao enrich_cnpj.py (etapa 1):
  - A etapa 1 classifica NACIONAL/ESTRANGEIRO pelo domicilio legal da
    propria empresa (natureza juridica). Isso captura poucos casos,
    porque a grande maioria das multinacionais opera no Brasil atraves
    de uma subsidiaria com CNPJ e domicilio proprios (ex: "ASTRAZENECA
    DO BRASIL LTDA"), que e, legalmente, uma empresa brasileira.
  - Esta etapa 2 olha o QUADRO DE SOCIOS (QSA) de cada empresa ja
    classificada e verifica se algum socio e uma "Pessoa Juridica
    Domiciliada no Exterior" (codigo de qualificacao 22, conforme a
    tabela oficial da Receita Federal). Isso identifica a matriz
    estrangeira quando ela e socia direta da empresa brasileira.

O que faz:
  1. Reaproveita os CNPJs ja presentes em cnpj_enriquecido (nao repete
     o trabalho da etapa 1).
  2. Para cada um, consulta a BrasilAPI novamente (o mesmo endpoint,
     que tambem retorna o campo "qsa" com o quadro de socios).
  3. Marca possui_socio_pj_exterior = true/false e guarda o(s) nome(s)
     do(s) socio(s) estrangeiro(s) encontrados.
  4. Atualiza a mesma tabela cnpj_enriquecido (nao cria tabela nova).

Uso:
  python enrich_socios.py

Requisitos:
  pip install psycopg requests python-dotenv --break-system-packages
"""

from __future__ import annotations

import os
import time
from pathlib import Path

import psycopg
import requests
from psycopg.rows import dict_row

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


RAIZ_PROJETO = Path(__file__).resolve().parent.parent
ENV_PATH = RAIZ_PROJETO / "backend" / ".env"

BRASILAPI_URL = "https://brasilapi.com.br/api/cnpj/v1/{cnpj}"

INTERVALO_ENTRE_CHAMADAS_SEGUNDOS = 10.0
MAX_TENTATIVAS = 4
BACKOFF_BASE_SEGUNDOS = 8.0

# Codigos oficiais (Receita Federal, Tabela de Qualificacao de
# Socio/Administrador) para socio Pessoa Juridica domiciliada no
# exterior. Confirmados na tabela oficial codigo->descricao:
#   37 - Socio Pessoa Juridica Domiciliado no Exterior
#         (sociedades limitadas, S.A., simples, etc.)
#   57 - Socio Comanditario Pessoa Juridica Domiciliado no Exterior
#         (sociedades em comandita simples)
CODIGOS_QUALIFICACAO_SOCIO_PJ_EXTERIOR = {37, 57}


def carregar_configuracao_banco() -> dict:
    if load_dotenv is not None and ENV_PATH.exists():
        load_dotenv(ENV_PATH)

    return {
        "host": os.environ["DB_HOST"],
        "port": os.environ["DB_PORT"],
        "dbname": os.environ["DB_NAME"],
        "user": os.environ["DB_USER"],
        "password": os.environ["DB_PASSWORD"],
    }


def preparar_colunas(conexao: psycopg.Connection) -> None:
    conexao.execute(
        """
        ALTER TABLE public.cnpj_enriquecido
            ADD COLUMN IF NOT EXISTS possui_socio_pj_exterior BOOLEAN,
            ADD COLUMN IF NOT EXISTS nome_socio_pj_exterior VARCHAR(500),
            ADD COLUMN IF NOT EXISTS socios_consultado_em TIMESTAMP,
            ADD COLUMN IF NOT EXISTS socios_erro_consulta VARCHAR(300);
        """
    )
    conexao.commit()


def buscar_cnpjs_pendentes(conexao: psycopg.Connection) -> list[str]:
    """
    CNPJs que ja tem dados basicos (etapa 1 concluida com sucesso) e
    ainda nao tiveram o quadro de socios verificado (ou que falharam
    na ultima tentativa).
    """
    query = """
        SELECT cnpj
        FROM public.cnpj_enriquecido
        WHERE erro_consulta IS NULL
          AND (
              socios_consultado_em IS NULL
              OR socios_erro_consulta IS NOT NULL
          )
        ORDER BY cnpj;
    """

    with conexao.cursor(row_factory=dict_row) as cursor:
        cursor.execute(query)
        linhas = cursor.fetchall()

    return [linha["cnpj"] for linha in linhas]


def consultar_brasilapi(cnpj: str) -> dict:
    ultimo_erro: Exception | None = None

    for tentativa in range(1, MAX_TENTATIVAS + 1):
        try:
            resposta = requests.get(
                BRASILAPI_URL.format(cnpj=cnpj),
                timeout=15,
                headers={"User-Agent": "dashboard-ic-enriquecimento/1.0"},
            )

            if resposta.status_code in (400, 404):
                raise ValueError(
                    f"CNPJ invalido ou nao encontrado (status {resposta.status_code})."
                )

            if resposta.status_code == 429:
                espera = BACKOFF_BASE_SEGUNDOS * tentativa
                print(f"  Limite de requisicoes atingido, aguardando {espera:.0f}s...")
                time.sleep(espera)
                continue

            resposta.raise_for_status()
            return resposta.json()

        except ValueError:
            raise
        except requests.RequestException as exc:
            ultimo_erro = exc
            if tentativa < MAX_TENTATIVAS:
                espera = BACKOFF_BASE_SEGUNDOS * tentativa
                time.sleep(espera)

    raise RuntimeError(str(ultimo_erro) if ultimo_erro else "limite de requisicoes excedido repetidamente")


def extrair_socios_pj_exterior(dados: dict) -> list[str]:
    """
    Retorna os nomes dos socios que sao Pessoa Juridica Domiciliada no
    Exterior (codigo de qualificacao 22), com uma checagem textual de
    seguranca caso o codigo numerico nao venha preenchido.
    """
    qsa = dados.get("qsa") or []
    encontrados: list[str] = []

    for socio in qsa:
        codigo = socio.get("codigo_qualificacao_socio")
        qualificacao_texto = (socio.get("qualificacao_socio") or "").upper()

        e_pj_exterior = (
            codigo in CODIGOS_QUALIFICACAO_SOCIO_PJ_EXTERIOR
            or (
                "PESSOA JURIDICA" in qualificacao_texto
                and "EXTERIOR" in qualificacao_texto
            )
        )

        if e_pj_exterior:
            nome = (socio.get("nome_socio") or "").strip()
            if nome:
                encontrados.append(nome)

    return encontrados


def salvar_resultado(
    conexao: psycopg.Connection,
    cnpj: str,
    socios_encontrados: list[str] | None,
    erro: str | None,
) -> None:
    if erro is not None:
        conexao.execute(
            """
            UPDATE public.cnpj_enriquecido
            SET socios_erro_consulta = %(erro)s,
                socios_consultado_em = now()
            WHERE cnpj = %(cnpj)s;
            """,
            {"cnpj": cnpj, "erro": erro[:300]},
        )
        conexao.commit()
        return

    possui = bool(socios_encontrados)
    nomes = "; ".join(socios_encontrados or [])[:500] or None

    conexao.execute(
        """
        UPDATE public.cnpj_enriquecido
        SET possui_socio_pj_exterior = %(possui)s,
            nome_socio_pj_exterior = %(nomes)s,
            socios_consultado_em = now(),
            socios_erro_consulta = NULL
        WHERE cnpj = %(cnpj)s;
        """,
        {"cnpj": cnpj, "possui": possui, "nomes": nomes},
    )
    conexao.commit()


def main() -> None:
    configuracao = carregar_configuracao_banco()

    with psycopg.connect(**configuracao) as conexao:
        preparar_colunas(conexao)

        cnpjs = buscar_cnpjs_pendentes(conexao)
        total = len(cnpjs)

        print(f"{total} CNPJ(s) para verificar quadro de socios.\n")

        for indice, cnpj in enumerate(cnpjs, start=1):
            print(f"[{indice}/{total}] Consultando socios de {cnpj}...")

            try:
                dados = consultar_brasilapi(cnpj)
                socios_encontrados = extrair_socios_pj_exterior(dados)
                salvar_resultado(conexao, cnpj, socios_encontrados, erro=None)

                if socios_encontrados:
                    print(f"  -> Socio(s) PJ no exterior: {', '.join(socios_encontrados)}")
                else:
                    print("  -> Nenhum socio PJ no exterior.")

            except Exception as exc:  # noqa: BLE001
                salvar_resultado(conexao, cnpj, socios_encontrados=None, erro=str(exc))
                print(f"  -> Falhou: {exc}")

            time.sleep(INTERVALO_ENTRE_CHAMADAS_SEGUNDOS)

    print("\nConcluido.")


if __name__ == "__main__":
    main()