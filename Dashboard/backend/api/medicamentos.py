from fastapi import APIRouter, HTTPException, Query
import psycopg

from backend.database import fetch_all, fetch_one


router = APIRouter(
    prefix="/api/medicamentos",
    tags=["Medicamentos"],
)


def _database_error(exc: Exception) -> HTTPException:
    return HTTPException(
        status_code=503,
        detail=f"Erro ao consultar o PostgreSQL: {exc}",
    )


@router.get("/busca")
def buscar_medicamentos(
    q: str = Query(
        ...,
        min_length=1,
        max_length=120,
        description="Nome/descrição do medicamento ou código CATMAT.",
    ),
    limite: int = Query(200, ge=1, le=200),
):
    """
    Equivalente ao list_catmat() do Streamlit.

    Pesquisa no catálogo CATMAT por descrição ou código.
    """
    query = """
        SELECT
            catmat_id,
            codigo_catmat,
            descricao_catmat
        FROM catmat
        WHERE
            descricao_catmat ILIKE %(termo)s
            OR codigo_catmat ILIKE %(termo)s
        ORDER BY
            descricao_catmat,
            codigo_catmat
        LIMIT %(limite)s;
    """

    try:
        return fetch_all(
            query,
            {
                "termo": f"%{q.strip()}%",
                "limite": limite,
            },
        )
    except (psycopg.Error, RuntimeError) as exc:
        raise _database_error(exc) from exc


@router.get("/{catmat_id}/produtos")
def listar_produtos_do_catmat(catmat_id: int):
    """
    Equivalente ao get_produtos_by_catmat() do Streamlit.
    """
    query = """
        SELECT
            produto_id,
            catmat_id,
            anvisa,
            generico,
            codigo_catmat
        FROM produto
        WHERE catmat_id = %(catmat_id)s
        ORDER BY produto_id;
    """

    try:
        return fetch_all(
            query,
            {"catmat_id": catmat_id},
        )
    except (psycopg.Error, RuntimeError) as exc:
        raise _database_error(exc) from exc


@router.get("/{catmat_id}/resumo")
def resumo_medicamento(catmat_id: int):
    """
    KPIs da página de medicamentos seguindo a mesma lógica
    do Streamlit.

    A última posição é obtida por instituição considerando
    todos os produto_id vinculados ao CATMAT.
    """
    query = """
        WITH produtos_catmat AS (
            SELECT produto_id
            FROM produto
            WHERE catmat_id = %(catmat_id)s
        ),
        estoque_atual AS (
            SELECT DISTINCT ON (iep.instituicao_id)
                iep.instituicao_id,
                iep.produto_id,
                iep.quantidade_do_item_em_estoque,
                iep.data_de_posicao_no_estoque,
                iep.data_de_validade,
                iep.numero_do_lote
            FROM instituicao_estoca_produto iep
            INNER JOIN produtos_catmat p
                ON p.produto_id = iep.produto_id
            ORDER BY
                iep.instituicao_id,
                iep.data_de_posicao_no_estoque DESC NULLS LAST,
                iep.instituicao_estoca_produto_id DESC
        ),
        resumo_estoque AS (
            SELECT
                COALESCE(
                    SUM(quantidade_do_item_em_estoque),
                    0
                ) AS estoque_total,
                COUNT(DISTINCT instituicao_id)
                    AS instituicoes_com_registro,
                COUNT(*) FILTER (
                    WHERE quantidade_do_item_em_estoque = 0
                ) AS instituicoes_estoque_zerado
            FROM estoque_atual
        ),
        resumo_compras AS (
            SELECT
                AVG(c.preco_unitario)
                    AS preco_medio_compra
            FROM mantenedora_compra_produto c
            INNER JOIN produtos_catmat p
                ON p.produto_id = c.produto_id
            WHERE c.preco_unitario IS NOT NULL
        )
        SELECT
            re.estoque_total,
            re.instituicoes_com_registro,
            re.instituicoes_estoque_zerado,
            rc.preco_medio_compra
        FROM resumo_estoque re
        CROSS JOIN resumo_compras rc;
    """

    try:
        result = fetch_one(
            query,
            {"catmat_id": catmat_id},
        )

        return result or {
            "estoque_total": 0,
            "instituicoes_com_registro": 0,
            "instituicoes_estoque_zerado": 0,
            "preco_medio_compra": None,
        }
    except (psycopg.Error, RuntimeError) as exc:
        raise _database_error(exc) from exc


@router.get("/{catmat_id}/lotes-vencendo")
def lotes_vencendo(
    catmat_id: int,
    dias: int = Query(
        90,
        ge=1,
        le=365,
        description="Janela de validade em dias.",
    ),
):
    """
    Reproduz o alerta de validade do Streamlit.

    Primeiro mantém a última posição por instituição e, depois,
    filtra os registros com estoque positivo e validade dentro
    da janela informada.
    """
    query = """
        WITH produtos_catmat AS (
            SELECT produto_id
            FROM produto
            WHERE catmat_id = %(catmat_id)s
        ),
        estoque_atual AS (
            SELECT DISTINCT ON (iep.instituicao_id)
                iep.instituicao_id,
                iep.produto_id,
                iep.quantidade_do_item_em_estoque,
                iep.data_de_posicao_no_estoque,
                iep.data_de_validade,
                iep.numero_do_lote
            FROM instituicao_estoca_produto iep
            INNER JOIN produtos_catmat p
                ON p.produto_id = iep.produto_id
            ORDER BY
                iep.instituicao_id,
                iep.data_de_posicao_no_estoque DESC NULLS LAST,
                iep.instituicao_estoca_produto_id DESC
        )
        SELECT
            ea.instituicao_id,
            ea.produto_id,
            ea.numero_do_lote,
            ea.quantidade_do_item_em_estoque,
            ea.data_de_posicao_no_estoque,
            ea.data_de_validade
        FROM estoque_atual ea
        WHERE
            ea.data_de_validade IS NOT NULL
            AND ea.quantidade_do_item_em_estoque > 0
            AND ea.data_de_validade::date >= CURRENT_DATE
            AND ea.data_de_validade::date
                <= CURRENT_DATE
                + (%(dias)s * INTERVAL '1 day')
        ORDER BY ea.data_de_validade;
    """

    try:
        items = fetch_all(
            query,
            {
                "catmat_id": catmat_id,
                "dias": dias,
            },
        )

        return {
            "dias": dias,
            "quantidade_lotes": len(items),
            "items": items,
        }
    except (psycopg.Error, RuntimeError) as exc:
        raise _database_error(exc) from exc


@router.get("/{catmat_id}/estoque-por-uf")
def estoque_por_uf(catmat_id: int):
    """
    Equivalente ao get_estoque_por_uf() do Streamlit.

    Mantém a última posição por instituição e agrega estoque por UF.
    """
    query = """
        WITH produtos_catmat AS (
            SELECT produto_id
            FROM produto
            WHERE catmat_id = %(catmat_id)s
        ),
        ultima_posicao AS (
            SELECT DISTINCT ON (iep.instituicao_id)
                iep.instituicao_id,
                iep.quantidade_do_item_em_estoque
            FROM instituicao_estoca_produto iep
            INNER JOIN produtos_catmat p
                ON p.produto_id = iep.produto_id
            ORDER BY
                iep.instituicao_id,
                iep.data_de_posicao_no_estoque DESC NULLS LAST,
                iep.instituicao_estoca_produto_id DESC
        )
        SELECT
            v.sigla_unidade_federativa AS uf,
            COALESCE(
                SUM(up.quantidade_do_item_em_estoque),
                0
            ) AS estoque_total,
            COUNT(DISTINCT up.instituicao_id)
                AS num_instituicoes
        FROM ultima_posicao up
        INNER JOIN instituicao i
            ON i.instituicao_id = up.instituicao_id
        INNER JOIN v_endereco_completo v
            ON v.endereco_id = i.endereco_id
        GROUP BY v.sigla_unidade_federativa
        ORDER BY estoque_total DESC;
    """

    try:
        return fetch_all(
            query,
            {"catmat_id": catmat_id},
        )
    except (psycopg.Error, RuntimeError) as exc:
        raise _database_error(exc) from exc


@router.get("/{catmat_id}/compras/evolucao-preco")
def evolucao_preco_compra(catmat_id: int):
    """
    Média do preço unitário por data de compra.
    """
    query = """
        WITH produtos_catmat AS (
            SELECT produto_id
            FROM produto
            WHERE catmat_id = %(catmat_id)s
        )
        SELECT
            c.data_de_compra,
            AVG(c.preco_unitario) AS preco_medio
        FROM mantenedora_compra_produto c
        INNER JOIN produtos_catmat p
            ON p.produto_id = c.produto_id
        WHERE
            c.data_de_compra IS NOT NULL
            AND c.preco_unitario IS NOT NULL
        GROUP BY c.data_de_compra
        ORDER BY c.data_de_compra;
    """

    try:
        return fetch_all(
            query,
            {"catmat_id": catmat_id},
        )
    except (psycopg.Error, RuntimeError) as exc:
        raise _database_error(exc) from exc


@router.get("/{catmat_id}/compras/fornecedores")
def compras_por_fornecedor(
    catmat_id: int,
    limite: int = Query(15, ge=1, le=100),
):
    """
    Gasto total por fornecedor, limitado aos 15 maiores por padrão.
    """
    query = """
        WITH produtos_catmat AS (
            SELECT produto_id
            FROM produto
            WHERE catmat_id = %(catmat_id)s
        )
        SELECT
            COALESCE(
                NULLIF(BTRIM(f.nome_fornecedor), ''),
                'Não informado'
            ) AS nome_fornecedor,
            COALESCE(
                SUM(c.preco_total),
                0
            ) AS valor_total
        FROM mantenedora_compra_produto c
        INNER JOIN produtos_catmat p
            ON p.produto_id = c.produto_id
        LEFT JOIN fornecedor f
            ON f.fornecedor_id = c.fornecedor_id
        GROUP BY
            COALESCE(
                NULLIF(BTRIM(f.nome_fornecedor), ''),
                'Não informado'
            )
        ORDER BY valor_total DESC NULLS LAST
        LIMIT %(limite)s;
    """

    try:
        return fetch_all(
            query,
            {
                "catmat_id": catmat_id,
                "limite": limite,
            },
        )
    except (psycopg.Error, RuntimeError) as exc:
        raise _database_error(exc) from exc


@router.get("/{catmat_id}/compras/fabricantes")
def compras_por_fabricante(
    catmat_id: int,
    limite: int = Query(15, ge=1, le=100),
):
    """
    Gasto total por fabricante, limitado aos 15 maiores por padrão.
    """
    query = """
        WITH produtos_catmat AS (
            SELECT produto_id
            FROM produto
            WHERE catmat_id = %(catmat_id)s
        )
        SELECT
            COALESCE(
                NULLIF(BTRIM(fab.nome_fabricante), ''),
                'Não informado'
            ) AS nome_fabricante,
            COALESCE(
                SUM(c.preco_total),
                0
            ) AS valor_total
        FROM mantenedora_compra_produto c
        INNER JOIN produtos_catmat p
            ON p.produto_id = c.produto_id
        LEFT JOIN fabricante fab
            ON fab.fabricante_id = c.fabricante_id
        GROUP BY
            COALESCE(
                NULLIF(BTRIM(fab.nome_fabricante), ''),
                'Não informado'
            )
        ORDER BY valor_total DESC NULLS LAST
        LIMIT %(limite)s;
    """

    try:
        return fetch_all(
            query,
            {
                "catmat_id": catmat_id,
                "limite": limite,
            },
        )
    except (psycopg.Error, RuntimeError) as exc:
        raise _database_error(exc) from exc


@router.get("/{catmat_id}/compras")
def historico_compras(
    catmat_id: int,
    limite: int = Query(500, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    """
    Equivalente ao get_compras() do Streamlit.

    Retorna os registros em ordem cronológica.
    """
    query = """
        WITH produtos_catmat AS (
            SELECT produto_id
            FROM produto
            WHERE catmat_id = %(catmat_id)s
        )
        SELECT
            c.data_de_compra,
            c.modalidade_de_compra,
            c.tipo_da_compra,
            c.quantidade_de_itens,
            c.preco_unitario,
            c.preco_total,
            f.nome_fornecedor,
            fab.nome_fabricante,
            m.nome_mantenedora
        FROM mantenedora_compra_produto c
        INNER JOIN produtos_catmat p
            ON p.produto_id = c.produto_id
        LEFT JOIN fornecedor f
            ON f.fornecedor_id = c.fornecedor_id
        LEFT JOIN fabricante fab
            ON fab.fabricante_id = c.fabricante_id
        LEFT JOIN mantenedora m
            ON m.mantenedora_id = c.mantenedora_id
        ORDER BY
            c.data_de_compra ASC NULLS LAST,
            c.mantenedora_compra_produto_id ASC
        LIMIT %(limite)s
        OFFSET %(offset)s;
    """

    try:
        items = fetch_all(
            query,
            {
                "catmat_id": catmat_id,
                "limite": limite,
                "offset": offset,
            },
        )

        return {
            "limite": limite,
            "offset": offset,
            "items": items,
        }
    except (psycopg.Error, RuntimeError) as exc:
        raise _database_error(exc) from exc