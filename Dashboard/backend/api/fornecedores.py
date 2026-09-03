from datetime import date

import psycopg
from fastapi import APIRouter, HTTPException, Query

from backend.database import fetch_all, fetch_one


router = APIRouter(
    prefix="/api/fornecedores",
    tags=["Fornecedores"],
)


def _database_error(exc: Exception) -> HTTPException:
    return HTTPException(
        status_code=503,
        detail=f"Erro ao consultar o PostgreSQL: {exc}",
    )


def _validar_datas(data_inicio: date, data_fim: date) -> None:
    if data_fim < data_inicio:
        raise HTTPException(
            status_code=400,
            detail="A data final não pode ser anterior à data inicial.",
        )


@router.get("/mapa-por-uf")
def get_mapa_fornecedores_por_uf(
    data_inicio: date,
    data_fim: date,
):
    """
    Para cada UF (localizacao da mantenedora que comprou), soma a
    quantidade de itens e o valor comprado, classificando por origem
    do fornecedor em 4 categorias:

      NACIONAL          - domicilio legal no Brasil e sem socio PJ
                           domiciliado no exterior conhecido.
      ESTRANGEIRO        - a propria empresa e domiciliada fora do
                           Brasil (natureza juridica 217/221).
      GRUPO_ESTRANGEIRO  - empresa com CNPJ e domicilio brasileiros,
                           mas com socio Pessoa Juridica domiciliado
                           no exterior (subsidiaria de multinacional).
      DESCONHECIDO       - ainda nao classificado ou consulta falhou.

    UFs sem nenhuma compra no periodo nao aparecem no resultado.
    """
    _validar_datas(data_inicio, data_fim)

    query = """
        WITH compras_classificadas AS (
            SELECT
                COALESCE(
                    NULLIF(BTRIM(mun.sigla_uf), ''),
                    'Nao informado'
                ) AS uf,

                CASE
                    WHEN ce.nacional_estrangeiro = 'ESTRANGEIRO'
                        THEN 'ESTRANGEIRO'
                    WHEN ce.possui_socio_pj_exterior IS TRUE
                        THEN 'GRUPO_ESTRANGEIRO'
                    WHEN ce.nacional_estrangeiro = 'NACIONAL'
                         AND ce.possui_socio_pj_exterior IS FALSE
                        THEN 'NACIONAL'
                    ELSE 'DESCONHECIDO'
                END AS origem,

                c.quantidade_de_itens,
                c.preco_total

            FROM mantenedora_compra_produto c

            JOIN mantenedora m
                ON m.mantenedora_id = c.mantenedora_id

            LEFT JOIN municipio mun
                ON mun.codigo_do_municipio = m.municipio_id

            LEFT JOIN fornecedor f
                ON f.fornecedor_id = c.fornecedor_id

            LEFT JOIN cnpj_enriquecido ce
                ON ce.cnpj = BTRIM(f.cnpj_fornecedor)

            WHERE c.data_de_compra >= %(data_inicio)s
              AND c.data_de_compra < %(data_fim_exclusiva)s
        )
        SELECT
            uf,

            COALESCE(SUM(quantidade_de_itens) FILTER (
                WHERE origem = 'NACIONAL'
            ), 0) AS quantidade_nacional,

            COALESCE(SUM(quantidade_de_itens) FILTER (
                WHERE origem = 'ESTRANGEIRO'
            ), 0) AS quantidade_estrangeiro,

            COALESCE(SUM(quantidade_de_itens) FILTER (
                WHERE origem = 'GRUPO_ESTRANGEIRO'
            ), 0) AS quantidade_grupo_estrangeiro,

            COALESCE(SUM(quantidade_de_itens) FILTER (
                WHERE origem = 'DESCONHECIDO'
            ), 0) AS quantidade_desconhecida,

            COALESCE(SUM(preco_total) FILTER (
                WHERE origem = 'NACIONAL'
            ), 0) AS valor_nacional,

            COALESCE(SUM(preco_total) FILTER (
                WHERE origem = 'ESTRANGEIRO'
            ), 0) AS valor_estrangeiro,

            COALESCE(SUM(preco_total) FILTER (
                WHERE origem = 'GRUPO_ESTRANGEIRO'
            ), 0) AS valor_grupo_estrangeiro,

            COALESCE(SUM(preco_total) FILTER (
                WHERE origem = 'DESCONHECIDO'
            ), 0) AS valor_desconhecido

        FROM compras_classificadas

        GROUP BY uf

        ORDER BY uf;
    """

    parametros = {
        "data_inicio": data_inicio,
        "data_fim_exclusiva": date.fromordinal(data_fim.toordinal() + 1),
    }

    try:
        linhas = fetch_all(query, parametros)
    except (psycopg.Error, RuntimeError) as exc:
        raise _database_error(exc) from exc

    resultado = []
    for linha in linhas:
        qtd_nacional = linha["quantidade_nacional"] or 0
        qtd_estrangeiro_total = (
            (linha["quantidade_estrangeiro"] or 0)
            + (linha["quantidade_grupo_estrangeiro"] or 0)
        )

        if qtd_nacional > qtd_estrangeiro_total:
            predominancia = "NACIONAL"
        elif qtd_estrangeiro_total > qtd_nacional:
            predominancia = "ESTRANGEIRO"
        else:
            predominancia = "EMPATE"

        resultado.append({**linha, "predominancia": predominancia})

    return resultado


@router.get("/ranking")
def get_ranking_fornecedores(
    data_inicio: date,
    data_fim: date,
    uf: str = Query(default=""),
    limite: int = Query(default=100, ge=1, le=500),
):
    """
    Tabela de fornecedores no periodo, com valor total comprado,
    quantidade de itens e a classificacao nacional/estrangeiro.

    Se uf for informada, filtra pelas compras cuja mantenedora
    esta localizada naquela UF.
    """
    _validar_datas(data_inicio, data_fim)

    uf_normalizada = uf.strip().upper()
    filtro_uf = ""

    parametros = {
        "data_inicio": data_inicio,
        "data_fim_exclusiva": date.fromordinal(data_fim.toordinal() + 1),
        "limite": limite,
    }

    if uf_normalizada:
        filtro_uf = " AND COALESCE(NULLIF(BTRIM(mun.sigla_uf), ''), 'Nao informado') = %(uf)s"
        parametros["uf"] = uf_normalizada

    query = f"""
        SELECT
            COALESCE(
                NULLIF(BTRIM(f.nome_fornecedor), ''),
                'Nao informado'
            ) AS fornecedor,

            BTRIM(f.cnpj_fornecedor) AS cnpj,

            CASE
                WHEN ce.nacional_estrangeiro = 'ESTRANGEIRO'
                    THEN 'ESTRANGEIRO'
                WHEN ce.possui_socio_pj_exterior IS TRUE
                    THEN 'GRUPO_ESTRANGEIRO'
                WHEN ce.nacional_estrangeiro = 'NACIONAL'
                     AND ce.possui_socio_pj_exterior IS FALSE
                    THEN 'NACIONAL'
                ELSE 'DESCONHECIDO'
            END AS nacional_estrangeiro,

            ce.nome_socio_pj_exterior AS grupo_estrangeiro_socio,

            COALESCE(SUM(c.preco_total), 0) AS valor_total,

            COALESCE(SUM(c.quantidade_de_itens), 0) AS quantidade_itens,

            COUNT(*) AS numero_compras

        FROM mantenedora_compra_produto c

        JOIN mantenedora m
            ON m.mantenedora_id = c.mantenedora_id

        LEFT JOIN municipio mun
            ON mun.codigo_do_municipio = m.municipio_id

        LEFT JOIN fornecedor f
            ON f.fornecedor_id = c.fornecedor_id

        LEFT JOIN cnpj_enriquecido ce
            ON ce.cnpj = BTRIM(f.cnpj_fornecedor)

        WHERE c.data_de_compra >= %(data_inicio)s
          AND c.data_de_compra < %(data_fim_exclusiva)s
        {filtro_uf}

        GROUP BY
            COALESCE(NULLIF(BTRIM(f.nome_fornecedor), ''), 'Nao informado'),
            BTRIM(f.cnpj_fornecedor),
            ce.nacional_estrangeiro,
            ce.possui_socio_pj_exterior,
            ce.nome_socio_pj_exterior

        ORDER BY valor_total DESC NULLS LAST

        LIMIT %(limite)s;
    """

    try:
        return fetch_all(query, parametros)
    except (psycopg.Error, RuntimeError) as exc:
        raise _database_error(exc) from exc


@router.get("/top-por-uf")
def get_top_fornecedor_por_uf(
    data_inicio: date,
    data_fim: date,
):
    """
    Para cada UF, o fornecedor com maior valor total comprado
    no periodo (o "campeao" de cada estado).
    """
    _validar_datas(data_inicio, data_fim)

    query = """
        WITH compras_por_uf_fornecedor AS (
            SELECT
                COALESCE(
                    NULLIF(BTRIM(mun.sigla_uf), ''),
                    'Nao informado'
                ) AS uf,

                COALESCE(
                    NULLIF(BTRIM(f.nome_fornecedor), ''),
                    'Nao informado'
                ) AS fornecedor,

                COALESCE(ce.nacional_estrangeiro, 'DESCONHECIDO')
                    AS nacional_estrangeiro,

                SUM(c.preco_total) AS valor_total,
                SUM(c.quantidade_de_itens) AS quantidade_itens

            FROM mantenedora_compra_produto c

            JOIN mantenedora m
                ON m.mantenedora_id = c.mantenedora_id

            LEFT JOIN municipio mun
                ON mun.codigo_do_municipio = m.municipio_id

            LEFT JOIN fornecedor f
                ON f.fornecedor_id = c.fornecedor_id

            LEFT JOIN cnpj_enriquecido ce
                ON ce.cnpj = BTRIM(f.cnpj_fornecedor)

            WHERE c.data_de_compra >= %(data_inicio)s
              AND c.data_de_compra < %(data_fim_exclusiva)s

            GROUP BY uf, fornecedor, ce.nacional_estrangeiro
        ),

        ranqueado AS (
            SELECT
                *,
                ROW_NUMBER() OVER (
                    PARTITION BY uf
                    ORDER BY valor_total DESC NULLS LAST
                ) AS posicao
            FROM compras_por_uf_fornecedor
        )

        SELECT
            uf,
            fornecedor,
            nacional_estrangeiro,
            valor_total,
            quantidade_itens
        FROM ranqueado
        WHERE posicao = 1
        ORDER BY uf;
    """

    parametros = {
        "data_inicio": data_inicio,
        "data_fim_exclusiva": date.fromordinal(data_fim.toordinal() + 1),
    }

    try:
        return fetch_all(query, parametros)
    except (psycopg.Error, RuntimeError) as exc:
        raise _database_error(exc) from exc