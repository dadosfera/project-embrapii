"""
Script de enriquecimento de CNPJs de fabricante/fornecedor.

O que faz:
  1. Le os CNPJs distintos das tabelas `fabricante` e `fornecedor`.
  2. Consulta cada CNPJ na BrasilAPI (gratuita, sem necessidade de chave),
     que agrega os dados abertos da Receita Federal.
  3. Classifica cada CNPJ como NACIONAL ou ESTRANGEIRO com base em:
       - codigo_natureza_juridica (217x = filial de empresa estrangeira,
         221x = empresa domiciliada no exterior)
       - codigo_pais / pais_exterior (preenchido quando a empresa e
         domiciliada fora do Brasil)
  4. Grava o resultado numa tabela nova `cnpj_enriquecido`, sem alterar
     nenhuma tabela existente.

Uso:
  python enrich_cnpj.py

Requisitos:
  pip install psycopg requests python-dotenv --break-system-packages

Le as credenciais do banco do mesmo arquivo backend/.env usado pela API.
"""

from __future__ import annotations

import os
import re
import time
from pathlib import Path

import psycopg
import requests
from psycopg.rows import dict_row

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


# ============================================================
# Configuracao
# ============================================================

RAIZ_PROJETO = Path(__file__).resolve().parent.parent
ENV_PATH = RAIZ_PROJETO / "backend" / ".env"

BRASILAPI_URL = "https://brasilapi.com.br/api/cnpj/v1/{cnpj}"

# Intervalo entre chamadas, para nao sobrecarregar a API publica.
# Confirmado manualmente: 10s e estavel (5/5 sucessos em teste).
INTERVALO_ENTRE_CHAMADAS_SEGUNDOS = 10.0

# Tentativas em caso de erro temporario (429 / timeout / 5xx).
MAX_TENTATIVAS = 4
BACKOFF_BASE_SEGUNDOS = 8.0

# Codigos de natureza juridica que indicam empresa estrangeira,
# conforme a Tabela de Natureza Juridica do IBGE/Concla.
CODIGOS_NATUREZA_ESTRANGEIRA = {
    2178,  # Estabelecimento, no Brasil, de Sociedade Estrangeira
    2216,  # Empresa Domiciliada no Exterior
}


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


def normalizar_cnpj(cnpj: str | None) -> str | None:
    if not cnpj:
        return None
    apenas_digitos = re.sub(r"\D", "", cnpj)
    if len(apenas_digitos) != 14:
        return None
    return apenas_digitos


def criar_tabela_enriquecimento(conexao: psycopg.Connection) -> None:
    conexao.execute(
        """
        CREATE TABLE IF NOT EXISTS cnpj_enriquecido (
            cnpj                        VARCHAR(14) PRIMARY KEY,
            razao_social                VARCHAR(300),
            codigo_natureza_juridica    INTEGER,
            descricao_natureza_juridica VARCHAR(200),
            codigo_pais                 INTEGER,
            nome_pais                   VARCHAR(100),
            nacional_estrangeiro        VARCHAR(15) NOT NULL,
            situacao_cadastral          VARCHAR(50),
            consultado_em               TIMESTAMP NOT NULL DEFAULT now(),
            erro_consulta                VARCHAR(300)
        );
        """
    )
    conexao.commit()


def buscar_cnpjs_pendentes(conexao: psycopg.Connection) -> list[str]:
    """
    Retorna os CNPJs de fabricante/fornecedor que ainda nao foram
    consultados (ou que falharam na ultima tentativa).
    """
    query = """
        WITH cnpjs_origem AS (
            SELECT DISTINCT cnpj_fabricante AS cnpj
            FROM fabricante
            WHERE cnpj_fabricante IS NOT NULL

            UNION

            SELECT DISTINCT cnpj_fornecedor AS cnpj
            FROM fornecedor
            WHERE cnpj_fornecedor IS NOT NULL
        )
        SELECT o.cnpj
        FROM cnpjs_origem o
        LEFT JOIN cnpj_enriquecido e
            ON e.cnpj = o.cnpj
        WHERE e.cnpj IS NULL
           OR e.erro_consulta IS NOT NULL;
    """

    with conexao.cursor(row_factory=dict_row) as cursor:
        cursor.execute(query)
        linhas = cursor.fetchall()

    cnpjs = set()
    for linha in linhas:
        cnpj_normalizado = normalizar_cnpj(linha["cnpj"])
        if cnpj_normalizado:
            cnpjs.add(cnpj_normalizado)

    return sorted(cnpjs)


def classificar_nacionalidade(dados: dict) -> str:
    codigo_natureza = dados.get("codigo_natureza_juridica")
    codigo_pais = dados.get("codigo_pais")
    cidade_exterior = dados.get("nome_cidade_no_exterior") or ""

    if codigo_natureza in CODIGOS_NATUREZA_ESTRANGEIRA:
        return "ESTRANGEIRO"

    if codigo_pais not in (None, "", 0) or cidade_exterior.strip():
        return "ESTRANGEIRO"

    return "NACIONAL"


def consultar_brasilapi(cnpj: str) -> dict:
    ultimo_erro: Exception | None = None

    for tentativa in range(1, MAX_TENTATIVAS + 1):
        try:
            resposta = requests.get(
                BRASILAPI_URL.format(cnpj=cnpj),
                timeout=15,
                headers={"User-Agent": "dashboard-ic-enriquecimento/1.0"},
            )

            if resposta.status_code == 404:
                raise ValueError("CNPJ nao encontrado na Receita Federal.")

            if resposta.status_code == 400:
                raise ValueError("CNPJ invalido ou mal formatado.")

            if resposta.status_code == 429:
                espera = BACKOFF_BASE_SEGUNDOS * tentativa
                print(f"  Limite de requisicoes atingido, aguardando {espera:.0f}s...")
                time.sleep(espera)
                continue

            resposta.raise_for_status()
            return resposta.json()

        except ValueError:
            # Erro definitivo (CNPJ invalido/nao encontrado): nao adianta tentar de novo.
            raise
        except requests.RequestException as exc:
            ultimo_erro = exc
            if tentativa < MAX_TENTATIVAS:
                espera = BACKOFF_BASE_SEGUNDOS * tentativa
                time.sleep(espera)

    raise RuntimeError(str(ultimo_erro) if ultimo_erro else "limite de requisicoes excedido repetidamente")


def salvar_resultado(
    conexao: psycopg.Connection,
    cnpj: str,
    dados: dict | None,
    erro: str | None,
) -> None:
    if erro is not None:
        conexao.execute(
            """
            INSERT INTO cnpj_enriquecido (cnpj, nacional_estrangeiro, erro_consulta, consultado_em)
            VALUES (%(cnpj)s, 'DESCONHECIDO', %(erro)s, now())
            ON CONFLICT (cnpj) DO UPDATE SET
                erro_consulta = EXCLUDED.erro_consulta,
                consultado_em = now();
            """,
            {"cnpj": cnpj, "erro": erro[:300]},
        )
        conexao.commit()
        return

    nacionalidade = classificar_nacionalidade(dados)

    conexao.execute(
        """
        INSERT INTO cnpj_enriquecido (
            cnpj,
            razao_social,
            codigo_natureza_juridica,
            descricao_natureza_juridica,
            codigo_pais,
            nome_pais,
            nacional_estrangeiro,
            situacao_cadastral,
            consultado_em,
            erro_consulta
        )
        VALUES (
            %(cnpj)s,
            %(razao_social)s,
            %(codigo_natureza_juridica)s,
            %(descricao_natureza_juridica)s,
            %(codigo_pais)s,
            %(nome_pais)s,
            %(nacional_estrangeiro)s,
            %(situacao_cadastral)s,
            now(),
            NULL
        )
        ON CONFLICT (cnpj) DO UPDATE SET
            razao_social                = EXCLUDED.razao_social,
            codigo_natureza_juridica    = EXCLUDED.codigo_natureza_juridica,
            descricao_natureza_juridica = EXCLUDED.descricao_natureza_juridica,
            codigo_pais                 = EXCLUDED.codigo_pais,
            nome_pais                   = EXCLUDED.nome_pais,
            nacional_estrangeiro        = EXCLUDED.nacional_estrangeiro,
            situacao_cadastral          = EXCLUDED.situacao_cadastral,
            consultado_em               = now(),
            erro_consulta               = NULL;
        """,
        {
            "cnpj": cnpj,
            "razao_social": dados.get("razao_social"),
            "codigo_natureza_juridica": dados.get("codigo_natureza_juridica"),
            "descricao_natureza_juridica": dados.get("natureza_juridica"),
            "codigo_pais": dados.get("codigo_pais"),
            "nome_pais": dados.get("nome_cidade_no_exterior") or None,
            "nacional_estrangeiro": nacionalidade,
            "situacao_cadastral": dados.get("descricao_situacao_cadastral"),
        },
    )
    conexao.commit()


def main() -> None:
    configuracao = carregar_configuracao_banco()

    with psycopg.connect(**configuracao) as conexao:
        criar_tabela_enriquecimento(conexao)

        cnpjs = buscar_cnpjs_pendentes(conexao)
        total = len(cnpjs)

        print(f"{total} CNPJ(s) para consultar.\n")

        for indice, cnpj in enumerate(cnpjs, start=1):
            print(f"[{indice}/{total}] Consultando {cnpj}...")

            try:
                dados = consultar_brasilapi(cnpj)
                salvar_resultado(conexao, cnpj, dados, erro=None)
                print(f"  -> {dados.get('razao_social')} "
                      f"({classificar_nacionalidade(dados)})")
            except Exception as exc:  # noqa: BLE001 - queremos seguir para o proximo CNPJ
                salvar_resultado(conexao, cnpj, dados=None, erro=str(exc))
                print(f"  -> Falhou: {exc}")

            time.sleep(INTERVALO_ENTRE_CHAMADAS_SEGUNDOS)

    print("\nConcluido.")


if __name__ == "__main__":
    main()