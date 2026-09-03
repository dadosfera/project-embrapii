from datetime import date, timedelta

import psycopg
from fastapi import APIRouter, HTTPException, Query

from backend.database import fetch_all, fetch_one


router = APIRouter(
    prefix="/api/compras",
    tags=["Compras"],
)


TIPOS_COMPRA = {
    "ADMINISTRATIVA",
    "JUDICIAL",
}


def _database_error(exc: Exception) -> HTTPException:
    return HTTPException(
        status_code=503,
        detail=f"Erro ao consultar o PostgreSQL: {exc}",
    )


def _montar_filtros(
    data_inicio: date,
    data_fim: date,
    catmat_id: int | None,
    tipo_compra: str,
) -> tuple[str, dict]:
    """
    Reproduz os filtros usados pela página Streamlit de compras.

    A data final é inclusiva.
    """
    if data_fim < data_inicio:
        raise HTTPException(
            status_code=400,
            detail="A data final não pode ser anterior à data inicial.",
        )

    tipo = tipo_compra.strip().upper()

    if tipo and tipo not in TIPOS_COMPRA:
        raise HTTPException(
            status_code=400,
            detail="Tipo da compra inválido.",
        )

    filtros = [
        "c.data_de_compra >= %(data_inicio)s",
        "c.data_de_compra < %(data_fim_exclusiva)s",
    ]

    parametros: dict = {
        "data_inicio": data_inicio,
        "data_fim_exclusiva": data_fim + timedelta(days=1),
    }

    if catmat_id is not None:
        filtros.append(
            """
            c.produto_id IN (
                SELECT p.produto_id
                FROM produto p
                WHERE p.catmat_id = %(catmat_id)s
            )
            """
        )
        parametros["catmat_id"] = catmat_id

    if tipo:
        filtros.append(
            "c.tipo_da_compra = %(tipo_compra)s"
        )
        parametros["tipo_compra"] = tipo

    return " AND ".join(filtros), parametros


def _params_comuns(
    data_inicio: date,
    data_fim: date,
    catmat_id: int | None,
    tipo_compra: str,
):
    return _montar_filtros(
        data_inicio=data_inicio,
        data_fim=data_fim,
        catmat_id=catmat_id,
        tipo_compra=tipo_compra,
    )


@router.get("/kpis")
def get_kpis_compras(
    data_inicio: date,
    data_fim: date,
    catmat_id: int | None = Query(default=None, ge=1),
    tipo_compra: str = Query(default=""),
):
    where_sql, parametros = _params_comuns(
        data_inicio,
        data_fim,
        catmat_id,
        tipo_compra,
    )

    query = f"""
        SELECT
            COALESCE(
                SUM(c.preco_total),
                0
            ) AS valor_total,

            COUNT(*) AS numero_compras,

            COALESCE(
                SUM(c.quantidade_de_itens),
                0
            ) AS quantidade_itens,

            COUNT(
                DISTINCT c.fornecedor_id
            ) AS numero_fornecedores,

            COUNT(
                DISTINCT c.fabricante_id
            ) AS numero_fabricantes,

            COUNT(
                DISTINCT c.mantenedora_id
            ) AS numero_mantenedoras

        FROM mantenedora_compra_produto c

        WHERE {where_sql};
    """

    try:
        return fetch_one(query, parametros) or {
            "valor_total": 0,
            "numero_compras": 0,
            "quantidade_itens": 0,
            "numero_fornecedores": 0,
            "numero_fabricantes": 0,
            "numero_mantenedoras": 0,
        }
    except (psycopg.Error, RuntimeError) as exc:
        raise _database_error(exc) from exc


@router.get("/por-mes")
def get_compras_por_mes(
    data_inicio: date,
    data_fim: date,
    catmat_id: int | None = Query(default=None, ge=1),
    tipo_compra: str = Query(default=""),
):
    where_sql, parametros = _params_comuns(
        data_inicio,
        data_fim,
        catmat_id,
        tipo_compra,
    )

    query = f"""
        SELECT
            DATE_TRUNC(
                'month',
                c.data_de_compra
            )::date AS mes,

            COALESCE(
                SUM(c.preco_total),
                0
            ) AS valor_total,

            COUNT(*) AS numero_compras,

            COALESCE(
                SUM(c.quantidade_de_itens),
                0
            ) AS quantidade_itens

        FROM mantenedora_compra_produto c

        WHERE {where_sql}

        GROUP BY
            DATE_TRUNC(
                'month',
                c.data_de_compra
            )

        ORDER BY mes;
    """

    try:
        return fetch_all(query, parametros)
    except (psycopg.Error, RuntimeError) as exc:
        raise _database_error(exc) from exc


@router.get("/fornecedores")
def get_top_fornecedores_compras(
    data_inicio: date,
    data_fim: date,
    catmat_id: int | None = Query(default=None, ge=1),
    tipo_compra: str = Query(default=""),
    limite: int = Query(default=15, ge=1, le=100),
):
    where_sql, parametros = _params_comuns(
        data_inicio,
        data_fim,
        catmat_id,
        tipo_compra,
    )
    parametros["limite"] = limite

    query = f"""
        SELECT
            COALESCE(
                NULLIF(
                    BTRIM(f.nome_fornecedor),
                    ''
                ),
                'Nao informado'
            ) AS fornecedor,

            COALESCE(
                SUM(c.preco_total),
                0
            ) AS valor_total,

            COUNT(*) AS numero_compras,

            COALESCE(
                SUM(c.quantidade_de_itens),
                0
            ) AS quantidade_itens

        FROM mantenedora_compra_produto c

        LEFT JOIN fornecedor f
            ON f.fornecedor_id = c.fornecedor_id

        WHERE {where_sql}

        GROUP BY
            COALESCE(
                NULLIF(
                    BTRIM(f.nome_fornecedor),
                    ''
                ),
                'Nao informado'
            )

        ORDER BY valor_total DESC NULLS LAST

        LIMIT %(limite)s;
    """

    try:
        return fetch_all(query, parametros)
    except (psycopg.Error, RuntimeError) as exc:
        raise _database_error(exc) from exc


@router.get("/fabricantes")
def get_top_fabricantes_compras(
    data_inicio: date,
    data_fim: date,
    catmat_id: int | None = Query(default=None, ge=1),
    tipo_compra: str = Query(default=""),
    limite: int = Query(default=15, ge=1, le=100),
):
    where_sql, parametros = _params_comuns(
        data_inicio,
        data_fim,
        catmat_id,
        tipo_compra,
    )
    parametros["limite"] = limite

    query = f"""
        SELECT
            COALESCE(
                NULLIF(
                    BTRIM(fab.nome_fabricante),
                    ''
                ),
                'Nao informado'
            ) AS fabricante,

            COALESCE(
                SUM(c.preco_total),
                0
            ) AS valor_total,

            COUNT(*) AS numero_compras,

            COALESCE(
                SUM(c.quantidade_de_itens),
                0
            ) AS quantidade_itens

        FROM mantenedora_compra_produto c

        LEFT JOIN fabricante fab
            ON fab.fabricante_id = c.fabricante_id

        WHERE {where_sql}

        GROUP BY
            COALESCE(
                NULLIF(
                    BTRIM(fab.nome_fabricante),
                    ''
                ),
                'Nao informado'
            )

        ORDER BY valor_total DESC NULLS LAST

        LIMIT %(limite)s;
    """

    try:
        return fetch_all(query, parametros)
    except (psycopg.Error, RuntimeError) as exc:
        raise _database_error(exc) from exc


@router.get("/modalidades")
def get_compras_por_modalidade(
    data_inicio: date,
    data_fim: date,
    catmat_id: int | None = Query(default=None, ge=1),
    tipo_compra: str = Query(default=""),
):
    where_sql, parametros = _params_comuns(
        data_inicio,
        data_fim,
        catmat_id,
        tipo_compra,
    )

    query = f"""
        SELECT
            COALESCE(
                NULLIF(
                    BTRIM(c.modalidade_de_compra),
                    ''
                ),
                'Nao informado'
            ) AS modalidade,

            COALESCE(
                SUM(c.preco_total),
                0
            ) AS valor_total,

            COUNT(*) AS numero_compras,

            COALESCE(
                SUM(c.quantidade_de_itens),
                0
            ) AS quantidade_itens

        FROM mantenedora_compra_produto c

        WHERE {where_sql}

        GROUP BY
            COALESCE(
                NULLIF(
                    BTRIM(c.modalidade_de_compra),
                    ''
                ),
                'Nao informado'
            )

        ORDER BY valor_total DESC NULLS LAST;
    """

    try:
        return fetch_all(query, parametros)
    except (psycopg.Error, RuntimeError) as exc:
        raise _database_error(exc) from exc


@router.get("/tipos")
def get_compras_por_tipo(
    data_inicio: date,
    data_fim: date,
    catmat_id: int | None = Query(default=None, ge=1),
    tipo_compra: str = Query(default=""),
):
    where_sql, parametros = _params_comuns(
        data_inicio,
        data_fim,
        catmat_id,
        tipo_compra,
    )

    query = f"""
        SELECT
            COALESCE(
                NULLIF(
                    BTRIM(c.tipo_da_compra),
                    ''
                ),
                'Nao informado'
            ) AS tipo_compra,

            COALESCE(
                SUM(c.preco_total),
                0
            ) AS valor_total,

            COUNT(*) AS numero_compras,

            COALESCE(
                SUM(c.quantidade_de_itens),
                0
            ) AS quantidade_itens

        FROM mantenedora_compra_produto c

        WHERE {where_sql}

        GROUP BY
            COALESCE(
                NULLIF(
                    BTRIM(c.tipo_da_compra),
                    ''
                ),
                'Nao informado'
            )

        ORDER BY valor_total DESC NULLS LAST;
    """

    try:
        return fetch_all(query, parametros)
    except (psycopg.Error, RuntimeError) as exc:
        raise _database_error(exc) from exc


@router.get("/recentes")
def get_compras_recentes(
    data_inicio: date,
    data_fim: date,
    catmat_id: int | None = Query(default=None, ge=1),
    tipo_compra: str = Query(default=""),
    limite: int = Query(default=500, ge=1, le=500),
):
    where_sql, parametros = _params_comuns(
        data_inicio,
        data_fim,
        catmat_id,
        tipo_compra,
    )
    parametros["limite"] = limite

    query = f"""
        SELECT
            c.data_de_compra,
            cat.codigo_catmat,
            cat.descricao_catmat,
            c.modalidade_de_compra,
            c.tipo_da_compra,
            c.quantidade_de_itens,
            c.preco_unitario,
            c.preco_total,
            f.nome_fornecedor,
            fab.nome_fabricante,
            m.nome_mantenedora

        FROM mantenedora_compra_produto c

        LEFT JOIN produto p
            ON p.produto_id = c.produto_id

        LEFT JOIN catmat cat
            ON cat.catmat_id = p.catmat_id

        LEFT JOIN fornecedor f
            ON f.fornecedor_id = c.fornecedor_id

        LEFT JOIN fabricante fab
            ON fab.fabricante_id = c.fabricante_id

        LEFT JOIN mantenedora m
            ON m.mantenedora_id = c.mantenedora_id

        WHERE {where_sql}

        ORDER BY
            c.data_de_compra DESC NULLS LAST,
            c.mantenedora_compra_produto_id DESC

        LIMIT %(limite)s;
    """

    try:
        return fetch_all(query, parametros)
    except (psycopg.Error, RuntimeError) as exc:
        raise _database_error(exc) from exc