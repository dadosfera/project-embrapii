import json
from datetime import date
from functools import lru_cache
from time import monotonic
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, HTTPException, Query

from backend.database import DatabaseError, Q, fetch_all, fetch_one, get_engine


router = APIRouter(
    prefix="/api/leitos",
    tags=["Leitos"],
)


MODOS_VALIDOS = {
    "ultima_competencia",
    "ultima_instituicao",
}


CACHE_TTL_SEGUNDOS = 900


def _cache_bucket() -> int:
    """
    Cria uma janela de cache de 15 minutos.

    Mantém comportamento equivalente ao ttl=900 usado
    na versão Streamlit, sem adicionar dependências.
    """
    return int(
        monotonic()
        // CACHE_TTL_SEGUNDOS
    )


def _database_error(exc: Exception) -> HTTPException:
    return HTTPException(
        status_code=503,
        detail=f"Erro ao consultar o banco: {exc}",
    )


def _validar_modo(modo: str) -> str:
    modo_normalizado = modo.strip()

    if modo_normalizado not in MODOS_VALIDOS:
        raise HTTPException(
            status_code=400,
            detail=(
                "Modo inválido. Use 'ultima_competencia' "
                "ou 'ultima_instituicao'."
            ),
        )

    return modo_normalizado


def _cte_snapshot_leitos(modo: str, engine: str) -> str:
    """
    Replica a lógica documentada no spec.md.

    ultima_competencia:
      usa a competência mais recente existente na base.

    ultima_instituicao:
      usa a última posição conhecida de cada instituição.

    `DISTINCT ON` do PG vira `QUALIFY ROW_NUMBER()` no Snowflake
    ((instituicao_id, data_de_competencia) é único em leitos).
    """
    modo = _validar_modo(modo)

    colunas = """
        l.instituicao_id,
        l.data_de_competencia,
        l.quantidade_leitos_gerais,
        l.quantidade_leitos_sus,
        l.quantidade_leitos_uti,
        l.quantidade_leitos_uti_sus,
        l.quantidade_leitos_uti_adulto,
        l.quantidade_leitos_uti_sus_adulto,
        l.quantidade_leitos_uti_pediatrico,
        l.quantidade_leitos_uti_sus_pediatrico,
        l.quantidade_leitos_uti_neonatal,
        l.quantidade_leitos_uti_sus_neonatal,
        l.quantidade_leitos_uti_queimado,
        l.quantidade_leitos_uti_sus_queimado,
        l.quantidade_leitos_uti_coronariana,
        l.quantidade_leitos_uti_sus_coronariana
    """

    if engine == "snowflake":
        filtro_competencia = ""
        cte_competencia = ""
        if modo == "ultima_competencia":
            cte_competencia = """
            competencia_maxima AS (
                SELECT
                    MAX(data_de_competencia) AS competencia
                FROM leitos
            ),
            """
            filtro_competencia = """
                JOIN competencia_maxima cm
                    ON cm.competencia = l.data_de_competencia"""
        return f"""
            {cte_competencia}
            snapshot_leitos AS (
                SELECT
                    {colunas}
                FROM leitos l{filtro_competencia}
                QUALIFY ROW_NUMBER() OVER (
                    PARTITION BY l.instituicao_id
                    ORDER BY l.data_de_competencia DESC
                ) = 1
            )
        """

    if modo == "ultima_competencia":
        return f"""
            competencia_maxima AS (
                SELECT
                    MAX(data_de_competencia) AS competencia
                FROM leitos
            ),

            snapshot_leitos AS (
                SELECT DISTINCT ON (l.instituicao_id)
                    {colunas}
                FROM leitos l
                JOIN competencia_maxima cm
                    ON cm.competencia = l.data_de_competencia
                ORDER BY
                    l.instituicao_id,
                    l.data_de_competencia DESC
            )
        """

    return f"""
        snapshot_leitos AS (
            SELECT DISTINCT ON (l.instituicao_id)
                {colunas}
            FROM leitos l
            ORDER BY
                l.instituicao_id,
                l.data_de_competencia DESC
        )
    """


def _filtro_uf(
    uf: str,
) -> Tuple[str, Dict]:
    uf_normalizada = uf.strip().upper()

    if not uf_normalizada:
        return "", {}

    return (
        " AND mun.sigla_uf = %(uf)s",
        {"uf": uf_normalizada},
    )


def _json_do_snowflake(
    engine: str,
    linha: Dict[str, Any],
    colunas: Tuple[str, ...],
) -> Dict[str, Any]:
    """
    No Postgres, json_agg/row_to_json chegam já decodificados pelo
    psycopg. No Snowflake, ARRAY/OBJECT chegam como texto JSON.
    Devolve uma cópia (a linha pode estar no cache de queries).
    """
    if engine != "snowflake":
        return linha

    return {
        chave: (
            json.loads(valor)
            if chave in colunas and isinstance(valor, str)
            else valor
        )
        for chave, valor in linha.items()
    }


@router.get("/intervalo")
def get_intervalo_competencias():
    # Q(pg, sf): altere as duas versões juntas
    query = Q(
        pg="""
        SELECT
            MIN(data_de_competencia) AS data_minima,
            MAX(data_de_competencia) AS data_maxima
        FROM leitos;
    """,
        sf="""
        SELECT
            MIN(data_de_competencia) AS data_minima,
            MAX(data_de_competencia) AS data_maxima
        FROM leitos
        """,
    )

    try:
        return fetch_one(query) or {
            "data_minima": None,
            "data_maxima": None,
        }
    except (DatabaseError, RuntimeError) as exc:
        raise _database_error(exc) from exc


@router.get("/ufs")
def get_ufs():
    # Q(pg, sf): altere as duas versões juntas
    query = Q(
        pg="""
        SELECT DISTINCT
            mun.sigla_uf AS uf

        FROM leitos l

        JOIN instituicao i
            ON i.instituicao_id = l.instituicao_id

        LEFT JOIN endereco e
            ON e.endereco_id = i.endereco_id

        LEFT JOIN municipio mun
            ON mun.codigo_do_municipio = e.municipio_id

        WHERE mun.sigla_uf IS NOT NULL
          AND BTRIM(mun.sigla_uf) <> ''

        ORDER BY uf;
    """,
        sf="""
        SELECT DISTINCT
            mun.sigla_uf AS uf

        FROM leitos l

        JOIN instituicao i
            ON i.instituicao_id = l.instituicao_id

        LEFT JOIN endereco e
            ON e.endereco_id = i.endereco_id

        LEFT JOIN municipio mun
            ON mun.codigo_do_municipio = e.municipio_id

        WHERE mun.sigla_uf IS NOT NULL
          AND TRIM(mun.sigla_uf) <> ''

        ORDER BY uf
        """,
    )

    try:
        return fetch_all(query)
    except (DatabaseError, RuntimeError) as exc:
        raise _database_error(exc) from exc


@router.get("/kpis")
def get_kpis(
    modo: str = Query(default="ultima_competencia"),
    uf: str = Query(default=""),
):
    engine = get_engine()
    cte = _cte_snapshot_leitos(modo, engine)
    filtro_uf, parametros = _filtro_uf(uf)

    # Q(pg, sf): altere as duas versões juntas
    query = Q(
        pg=f"""
        WITH {cte}

        SELECT
            COALESCE(
                SUM(s.quantidade_leitos_gerais),
                0
            ) AS leitos_gerais,

            COALESCE(
                SUM(s.quantidade_leitos_sus),
                0
            ) AS leitos_sus,

            COALESCE(
                SUM(s.quantidade_leitos_uti),
                0
            ) AS leitos_uti,

            COALESCE(
                SUM(s.quantidade_leitos_uti_sus),
                0
            ) AS leitos_uti_sus,

            COUNT(
                DISTINCT s.instituicao_id
            ) AS instituicoes_com_registro,

            MIN(
                s.data_de_competencia
            ) AS competencia_minima,

            MAX(
                s.data_de_competencia
            ) AS competencia_maxima

        FROM snapshot_leitos s

        JOIN instituicao i
            ON i.instituicao_id = s.instituicao_id

        LEFT JOIN endereco e
            ON e.endereco_id = i.endereco_id

        LEFT JOIN municipio mun
            ON mun.codigo_do_municipio = e.municipio_id

        WHERE 1 = 1
        {filtro_uf};
    """,
        sf=f"""
        WITH {cte}

        SELECT
            COALESCE(
                SUM(s.quantidade_leitos_gerais),
                0
            ) AS leitos_gerais,

            COALESCE(
                SUM(s.quantidade_leitos_sus),
                0
            ) AS leitos_sus,

            COALESCE(
                SUM(s.quantidade_leitos_uti),
                0
            ) AS leitos_uti,

            COALESCE(
                SUM(s.quantidade_leitos_uti_sus),
                0
            ) AS leitos_uti_sus,

            COUNT(
                DISTINCT s.instituicao_id
            ) AS instituicoes_com_registro,

            MIN(
                s.data_de_competencia
            ) AS competencia_minima,

            MAX(
                s.data_de_competencia
            ) AS competencia_maxima

        FROM snapshot_leitos s

        JOIN instituicao i
            ON i.instituicao_id = s.instituicao_id

        LEFT JOIN endereco e
            ON e.endereco_id = i.endereco_id

        LEFT JOIN municipio mun
            ON mun.codigo_do_municipio = e.municipio_id

        WHERE 1 = 1
        {filtro_uf}
        """,
    )

    try:
        return fetch_one(query, parametros) or {
            "leitos_gerais": 0,
            "leitos_sus": 0,
            "leitos_uti": 0,
            "leitos_uti_sus": 0,
            "instituicoes_com_registro": 0,
            "competencia_minima": None,
            "competencia_maxima": None,
        }
    except (DatabaseError, RuntimeError) as exc:
        raise _database_error(exc) from exc


@router.get("/por-uf")
def get_leitos_por_uf(
    modo: str = Query(default="ultima_competencia"),
    uf: str = Query(default=""),
):
    engine = get_engine()
    cte = _cte_snapshot_leitos(modo, engine)
    filtro_uf, parametros = _filtro_uf(uf)

    # Q(pg, sf): altere as duas versões juntas
    query = Q(
        pg=f"""
        WITH {cte}

        SELECT
            COALESCE(
                NULLIF(
                    BTRIM(mun.sigla_uf),
                    ''
                ),
                'Nao informado'
            ) AS uf,

            COALESCE(
                SUM(s.quantidade_leitos_gerais),
                0
            ) AS leitos_gerais,

            COALESCE(
                SUM(s.quantidade_leitos_sus),
                0
            ) AS leitos_sus,

            COALESCE(
                SUM(s.quantidade_leitos_uti),
                0
            ) AS leitos_uti,

            COALESCE(
                SUM(s.quantidade_leitos_uti_sus),
                0
            ) AS leitos_uti_sus,

            COUNT(
                DISTINCT s.instituicao_id
            ) AS instituicoes

        FROM snapshot_leitos s

        JOIN instituicao i
            ON i.instituicao_id = s.instituicao_id

        LEFT JOIN endereco e
            ON e.endereco_id = i.endereco_id

        LEFT JOIN municipio mun
            ON mun.codigo_do_municipio = e.municipio_id

        WHERE 1 = 1
        {filtro_uf}

        GROUP BY
            COALESCE(
                NULLIF(
                    BTRIM(mun.sigla_uf),
                    ''
                ),
                'Nao informado'
            )

        ORDER BY
            leitos_gerais DESC;
    """,
        sf=f"""
        WITH {cte}

        SELECT
            COALESCE(
                NULLIF(
                    TRIM(mun.sigla_uf),
                    ''
                ),
                'Nao informado'
            ) AS uf,

            COALESCE(
                SUM(s.quantidade_leitos_gerais),
                0
            ) AS leitos_gerais,

            COALESCE(
                SUM(s.quantidade_leitos_sus),
                0
            ) AS leitos_sus,

            COALESCE(
                SUM(s.quantidade_leitos_uti),
                0
            ) AS leitos_uti,

            COALESCE(
                SUM(s.quantidade_leitos_uti_sus),
                0
            ) AS leitos_uti_sus,

            COUNT(
                DISTINCT s.instituicao_id
            ) AS instituicoes

        FROM snapshot_leitos s

        JOIN instituicao i
            ON i.instituicao_id = s.instituicao_id

        LEFT JOIN endereco e
            ON e.endereco_id = i.endereco_id

        LEFT JOIN municipio mun
            ON mun.codigo_do_municipio = e.municipio_id

        WHERE 1 = 1
        {filtro_uf}

        GROUP BY
            COALESCE(
                NULLIF(
                    TRIM(mun.sigla_uf),
                    ''
                ),
                'Nao informado'
            )

        ORDER BY
            leitos_gerais DESC
        """,
    )

    try:
        return fetch_all(query, parametros)
    except (DatabaseError, RuntimeError) as exc:
        raise _database_error(exc) from exc


@router.get("/tipos-uti")
def get_tipos_uti(
    modo: str = Query(default="ultima_competencia"),
    uf: str = Query(default=""),
):
    engine = get_engine()
    cte = _cte_snapshot_leitos(modo, engine)
    filtro_uf, parametros = _filtro_uf(uf)

    # Q(pg, sf): altere as duas versões juntas
    query = Q(
        pg=f"""
        WITH {cte},

        agregado AS (
            SELECT
                COALESCE(
                    SUM(s.quantidade_leitos_uti_adulto),
                    0
                ) AS adulto,

                COALESCE(
                    SUM(s.quantidade_leitos_uti_sus_adulto),
                    0
                ) AS sus_adulto,

                COALESCE(
                    SUM(s.quantidade_leitos_uti_pediatrico),
                    0
                ) AS pediatrico,

                COALESCE(
                    SUM(s.quantidade_leitos_uti_sus_pediatrico),
                    0
                ) AS sus_pediatrico,

                COALESCE(
                    SUM(s.quantidade_leitos_uti_neonatal),
                    0
                ) AS neonatal,

                COALESCE(
                    SUM(s.quantidade_leitos_uti_sus_neonatal),
                    0
                ) AS sus_neonatal,

                COALESCE(
                    SUM(s.quantidade_leitos_uti_queimado),
                    0
                ) AS queimado,

                COALESCE(
                    SUM(s.quantidade_leitos_uti_sus_queimado),
                    0
                ) AS sus_queimado,

                COALESCE(
                    SUM(s.quantidade_leitos_uti_coronariana),
                    0
                ) AS coronariana,

                COALESCE(
                    SUM(s.quantidade_leitos_uti_sus_coronariana),
                    0
                ) AS sus_coronariana

            FROM snapshot_leitos s

            JOIN instituicao i
                ON i.instituicao_id = s.instituicao_id

            LEFT JOIN endereco e
                ON e.endereco_id = i.endereco_id

            LEFT JOIN municipio mun
                ON mun.codigo_do_municipio = e.municipio_id

            WHERE 1 = 1
            {filtro_uf}
        )

        SELECT
            tipos.tipo_uti,
            tipos.total,
            tipos.sus

        FROM agregado a

        CROSS JOIN LATERAL (
            VALUES
                (
                    'Adulto',
                    a.adulto,
                    a.sus_adulto
                ),
                (
                    'Pediatrica',
                    a.pediatrico,
                    a.sus_pediatrico
                ),
                (
                    'Neonatal',
                    a.neonatal,
                    a.sus_neonatal
                ),
                (
                    'Queimados',
                    a.queimado,
                    a.sus_queimado
                ),
                (
                    'Coronariana',
                    a.coronariana,
                    a.sus_coronariana
                )
        ) AS tipos(
            tipo_uti,
            total,
            sus
        );
    """,
        sf=f"""
        WITH {cte},

        agregado AS (
            SELECT
                COALESCE(
                    SUM(s.quantidade_leitos_uti_adulto),
                    0
                ) AS adulto,

                COALESCE(
                    SUM(s.quantidade_leitos_uti_sus_adulto),
                    0
                ) AS sus_adulto,

                COALESCE(
                    SUM(s.quantidade_leitos_uti_pediatrico),
                    0
                ) AS pediatrico,

                COALESCE(
                    SUM(s.quantidade_leitos_uti_sus_pediatrico),
                    0
                ) AS sus_pediatrico,

                COALESCE(
                    SUM(s.quantidade_leitos_uti_neonatal),
                    0
                ) AS neonatal,

                COALESCE(
                    SUM(s.quantidade_leitos_uti_sus_neonatal),
                    0
                ) AS sus_neonatal,

                COALESCE(
                    SUM(s.quantidade_leitos_uti_queimado),
                    0
                ) AS queimado,

                COALESCE(
                    SUM(s.quantidade_leitos_uti_sus_queimado),
                    0
                ) AS sus_queimado,

                COALESCE(
                    SUM(s.quantidade_leitos_uti_coronariana),
                    0
                ) AS coronariana,

                COALESCE(
                    SUM(s.quantidade_leitos_uti_sus_coronariana),
                    0
                ) AS sus_coronariana

            FROM snapshot_leitos s

            JOIN instituicao i
                ON i.instituicao_id = s.instituicao_id

            LEFT JOIN endereco e
                ON e.endereco_id = i.endereco_id

            LEFT JOIN municipio mun
                ON mun.codigo_do_municipio = e.municipio_id

            WHERE 1 = 1
            {filtro_uf}
        )

        SELECT
            tipos.tipo_uti,
            tipos.total,
            tipos.sus

        FROM (
            SELECT 1 AS ordem, 'Adulto' AS tipo_uti, a.adulto AS total, a.sus_adulto AS sus
            FROM agregado a
            UNION ALL
            SELECT 2, 'Pediatrica', a.pediatrico, a.sus_pediatrico
            FROM agregado a
            UNION ALL
            SELECT 3, 'Neonatal', a.neonatal, a.sus_neonatal
            FROM agregado a
            UNION ALL
            SELECT 4, 'Queimados', a.queimado, a.sus_queimado
            FROM agregado a
            UNION ALL
            SELECT 5, 'Coronariana', a.coronariana, a.sus_coronariana
            FROM agregado a
        ) AS tipos

        ORDER BY
            tipos.ordem
        """,
    )

    try:
        return fetch_all(query, parametros)
    except (DatabaseError, RuntimeError) as exc:
        raise _database_error(exc) from exc


@router.get("/evolucao")
def get_evolucao(
    data_inicio: date,
    data_fim: date,
    uf: str = Query(default=""),
):
    if data_fim < data_inicio:
        raise HTTPException(
            status_code=400,
            detail="A data final não pode ser anterior à data inicial.",
        )

    filtro_uf, parametros_uf = _filtro_uf(uf)

    parametros = {
        "data_inicio": data_inicio,
        "data_fim": data_fim,
        **parametros_uf,
    }

    # Q(pg, sf): altere as duas versões juntas
    query = Q(
        pg=f"""
        SELECT
            l.data_de_competencia AS competencia,

            COALESCE(
                SUM(l.quantidade_leitos_gerais),
                0
            ) AS leitos_gerais,

            COALESCE(
                SUM(l.quantidade_leitos_sus),
                0
            ) AS leitos_sus,

            COALESCE(
                SUM(l.quantidade_leitos_uti),
                0
            ) AS leitos_uti,

            COALESCE(
                SUM(l.quantidade_leitos_uti_sus),
                0
            ) AS leitos_uti_sus,

            COUNT(
                DISTINCT l.instituicao_id
            ) AS instituicoes

        FROM leitos l

        JOIN instituicao i
            ON i.instituicao_id = l.instituicao_id

        LEFT JOIN endereco e
            ON e.endereco_id = i.endereco_id

        LEFT JOIN municipio mun
            ON mun.codigo_do_municipio = e.municipio_id

        WHERE l.data_de_competencia >= %(data_inicio)s
          AND l.data_de_competencia <= %(data_fim)s
          {filtro_uf}

        GROUP BY
            l.data_de_competencia

        ORDER BY
            l.data_de_competencia;
    """,
        sf=f"""
        SELECT
            l.data_de_competencia AS competencia,

            COALESCE(
                SUM(l.quantidade_leitos_gerais),
                0
            ) AS leitos_gerais,

            COALESCE(
                SUM(l.quantidade_leitos_sus),
                0
            ) AS leitos_sus,

            COALESCE(
                SUM(l.quantidade_leitos_uti),
                0
            ) AS leitos_uti,

            COALESCE(
                SUM(l.quantidade_leitos_uti_sus),
                0
            ) AS leitos_uti_sus,

            COUNT(
                DISTINCT l.instituicao_id
            ) AS instituicoes

        FROM leitos l

        JOIN instituicao i
            ON i.instituicao_id = l.instituicao_id

        LEFT JOIN endereco e
            ON e.endereco_id = i.endereco_id

        LEFT JOIN municipio mun
            ON mun.codigo_do_municipio = e.municipio_id

        WHERE l.data_de_competencia >= %(data_inicio)s
          AND l.data_de_competencia <= %(data_fim)s
          {filtro_uf}

        GROUP BY
            l.data_de_competencia

        ORDER BY
            l.data_de_competencia
        """,
    )

    try:
        return fetch_all(query, parametros)
    except (DatabaseError, RuntimeError) as exc:
        raise _database_error(exc) from exc


@router.get("/instituicoes")
def get_instituicoes(
    modo: str = Query(default="ultima_competencia"),
    uf: str = Query(default=""),
    limite: int = Query(default=100, ge=1, le=100),
):
    engine = get_engine()
    cte = _cte_snapshot_leitos(modo, engine)
    filtro_uf, parametros = _filtro_uf(uf)
    parametros["limite"] = limite

    # Q(pg, sf): altere as duas versões juntas
    query = Q(
        pg=f"""
        WITH {cte}

        SELECT
            s.instituicao_id,

            COALESCE(
                NULLIF(
                    BTRIM(i.nome_instituicao),
                    ''
                ),
                'Instituicao nao informada'
            ) AS instituicao,

            COALESCE(
                NULLIF(
                    BTRIM(mun.municipio),
                    ''
                ),
                'Nao informado'
            ) AS municipio,

            COALESCE(
                NULLIF(
                    BTRIM(mun.sigla_uf),
                    ''
                ),
                'Nao informado'
            ) AS uf,

            s.data_de_competencia AS competencia,

            COALESCE(
                s.quantidade_leitos_gerais,
                0
            ) AS leitos_gerais,

            COALESCE(
                s.quantidade_leitos_sus,
                0
            ) AS leitos_sus,

            COALESCE(
                s.quantidade_leitos_uti,
                0
            ) AS leitos_uti,

            COALESCE(
                s.quantidade_leitos_uti_sus,
                0
            ) AS leitos_uti_sus

        FROM snapshot_leitos s

        JOIN instituicao i
            ON i.instituicao_id = s.instituicao_id

        LEFT JOIN endereco e
            ON e.endereco_id = i.endereco_id

        LEFT JOIN municipio mun
            ON mun.codigo_do_municipio = e.municipio_id

        WHERE 1 = 1
        {filtro_uf}

        ORDER BY
            s.quantidade_leitos_gerais DESC NULLS LAST,
            instituicao,
            s.instituicao_id

        LIMIT %(limite)s;
    """,
        sf=f"""
        WITH {cte}

        SELECT
            s.instituicao_id,

            COALESCE(
                NULLIF(
                    TRIM(i.nome_instituicao),
                    ''
                ),
                'Instituicao nao informada'
            ) AS instituicao,

            COALESCE(
                NULLIF(
                    TRIM(mun.municipio),
                    ''
                ),
                'Nao informado'
            ) AS municipio,

            COALESCE(
                NULLIF(
                    TRIM(mun.sigla_uf),
                    ''
                ),
                'Nao informado'
            ) AS uf,

            s.data_de_competencia AS competencia,

            COALESCE(
                s.quantidade_leitos_gerais,
                0
            ) AS leitos_gerais,

            COALESCE(
                s.quantidade_leitos_sus,
                0
            ) AS leitos_sus,

            COALESCE(
                s.quantidade_leitos_uti,
                0
            ) AS leitos_uti,

            COALESCE(
                s.quantidade_leitos_uti_sus,
                0
            ) AS leitos_uti_sus

        FROM snapshot_leitos s

        JOIN instituicao i
            ON i.instituicao_id = s.instituicao_id

        LEFT JOIN endereco e
            ON e.endereco_id = i.endereco_id

        LEFT JOIN municipio mun
            ON mun.codigo_do_municipio = e.municipio_id

        WHERE 1 = 1
        {filtro_uf}

        ORDER BY
            s.quantidade_leitos_gerais DESC NULLS LAST,
            instituicao,
            s.instituicao_id

        LIMIT %(limite)s
        """,
    )

    try:
        return fetch_all(query, parametros)
    except (DatabaseError, RuntimeError) as exc:
        raise _database_error(exc) from exc


# ============================================================
# ENDPOINTS OTIMIZADOS PARA A INTERFACE REACT
# ============================================================

@lru_cache(maxsize=4)
def _buscar_opcoes_cache(
    engine: str,
    cache_bucket: int,
):
    """
    Busca intervalo e UFs em uma única conexão.

    Para obter as UFs, parte das instituições e usa EXISTS
    sobre leitos. Isso evita multiplicar cada instituição por
    todo o histórico de competências.

    `engine` entra na chave do lru_cache: um processo não serve
    ao Snowflake o resultado em cache do Postgres (e vice-versa).
    """
    _ = cache_bucket

    # Q(pg, sf): altere as duas versões juntas
    query = Q(
        pg="""
        SELECT
            (
                SELECT MIN(
                    l.data_de_competencia
                )
                FROM leitos l
            ) AS data_minima,

            (
                SELECT MAX(
                    l.data_de_competencia
                )
                FROM leitos l
            ) AS data_maxima,

            COALESCE(
                (
                    SELECT json_agg(
                        lista.uf
                        ORDER BY lista.uf
                    )

                    FROM (
                        SELECT DISTINCT
                            mun.sigla_uf AS uf

                        FROM instituicao i

                        JOIN endereco e
                            ON e.endereco_id = i.endereco_id

                        JOIN municipio mun
                            ON mun.codigo_do_municipio = e.municipio_id

                        WHERE mun.sigla_uf IS NOT NULL
                          AND BTRIM(mun.sigla_uf) <> ''

                          AND EXISTS (
                              SELECT 1
                              FROM leitos l
                              WHERE l.instituicao_id = i.instituicao_id
                          )
                    ) lista
                ),
                '[]'::json
            ) AS ufs;
    """,
        sf="""
        SELECT
            (
                SELECT MIN(
                    l.data_de_competencia
                )
                FROM leitos l
            ) AS data_minima,

            (
                SELECT MAX(
                    l.data_de_competencia
                )
                FROM leitos l
            ) AS data_maxima,

            COALESCE(
                (
                    SELECT ARRAY_AGG(
                        lista.uf
                    ) WITHIN GROUP (
                        ORDER BY lista.uf
                    )

                    FROM (
                        SELECT DISTINCT
                            mun.sigla_uf AS uf

                        FROM instituicao i

                        JOIN endereco e
                            ON e.endereco_id = i.endereco_id

                        JOIN municipio mun
                            ON mun.codigo_do_municipio = e.municipio_id

                        WHERE mun.sigla_uf IS NOT NULL
                          AND TRIM(mun.sigla_uf) <> ''

                          AND EXISTS (
                              SELECT 1
                              FROM leitos l
                              WHERE l.instituicao_id = i.instituicao_id
                          )
                    ) lista
                ),
                ARRAY_CONSTRUCT()
            ) AS ufs
        """,
    )

    resultado = fetch_one(query)
    if resultado is None:
        return {
            "data_minima": None,
            "data_maxima": None,
            "ufs": [],
        }
    return _json_do_snowflake(engine, resultado, ("ufs",))


@router.get("/opcoes")
def get_opcoes_leitos():
    """
    Retorna, em uma única chamada, o intervalo de competências
    e as UFs disponíveis. O resultado fica em cache por até
    15 minutos.
    """
    try:
        return _buscar_opcoes_cache(
            get_engine(),
            _cache_bucket(),
        )
    except (DatabaseError, RuntimeError) as exc:
        raise _database_error(exc) from exc


def _query_painel(
    modo: str,
    uf: str,
    engine: str,
) -> Tuple[Q, Dict]:
    cte = _cte_snapshot_leitos(
        modo,
        engine,
    )

    uf_normalizada = (
        uf.strip().upper()
    )

    filtro_snapshot = ""
    filtro_evolucao = ""

    parametros: dict = {}

    if uf_normalizada:
        filtro_snapshot = (
            " AND sg.sigla_uf = %(uf)s"
        )
        filtro_evolucao = (
            " AND mun.sigla_uf = %(uf)s"
        )
        parametros["uf"] = (
            uf_normalizada
        )

    # Q(pg, sf): altere as duas versões juntas
    query = Q(
        pg=f"""
        WITH {cte},

        snapshot_geo AS (
            SELECT
                s.*,
                i.nome_instituicao,
                mun.municipio,
                mun.sigla_uf

            FROM snapshot_leitos s

            JOIN instituicao i
                ON i.instituicao_id = s.instituicao_id

            LEFT JOIN endereco e
                ON e.endereco_id = i.endereco_id

            LEFT JOIN municipio mun
                ON mun.codigo_do_municipio = e.municipio_id
        ),

        snapshot_filtrado AS (
            SELECT *
            FROM snapshot_geo sg
            WHERE 1 = 1
            {filtro_snapshot}
        ),

        kpis AS (
            SELECT
                COALESCE(
                    SUM(sf.quantidade_leitos_gerais),
                    0
                ) AS leitos_gerais,

                COALESCE(
                    SUM(sf.quantidade_leitos_sus),
                    0
                ) AS leitos_sus,

                COALESCE(
                    SUM(sf.quantidade_leitos_uti),
                    0
                ) AS leitos_uti,

                COALESCE(
                    SUM(sf.quantidade_leitos_uti_sus),
                    0
                ) AS leitos_uti_sus,

                COUNT(
                    DISTINCT sf.instituicao_id
                ) AS instituicoes_com_registro,

                MIN(
                    sf.data_de_competencia
                ) AS competencia_minima,

                MAX(
                    sf.data_de_competencia
                ) AS competencia_maxima

            FROM snapshot_filtrado sf
        ),

        por_uf AS (
            SELECT
                COALESCE(
                    NULLIF(
                        BTRIM(sf.sigla_uf),
                        ''
                    ),
                    'Nao informado'
                ) AS uf,

                COALESCE(
                    SUM(sf.quantidade_leitos_gerais),
                    0
                ) AS leitos_gerais,

                COALESCE(
                    SUM(sf.quantidade_leitos_sus),
                    0
                ) AS leitos_sus,

                COALESCE(
                    SUM(sf.quantidade_leitos_uti),
                    0
                ) AS leitos_uti,

                COALESCE(
                    SUM(sf.quantidade_leitos_uti_sus),
                    0
                ) AS leitos_uti_sus,

                COUNT(
                    DISTINCT sf.instituicao_id
                ) AS instituicoes

            FROM snapshot_filtrado sf

            GROUP BY
                COALESCE(
                    NULLIF(
                        BTRIM(sf.sigla_uf),
                        ''
                    ),
                    'Nao informado'
                )
        ),

        tipos_uti_agregado AS (
            SELECT
                COALESCE(
                    SUM(sf.quantidade_leitos_uti_adulto),
                    0
                ) AS adulto,

                COALESCE(
                    SUM(sf.quantidade_leitos_uti_sus_adulto),
                    0
                ) AS sus_adulto,

                COALESCE(
                    SUM(sf.quantidade_leitos_uti_pediatrico),
                    0
                ) AS pediatrico,

                COALESCE(
                    SUM(sf.quantidade_leitos_uti_sus_pediatrico),
                    0
                ) AS sus_pediatrico,

                COALESCE(
                    SUM(sf.quantidade_leitos_uti_neonatal),
                    0
                ) AS neonatal,

                COALESCE(
                    SUM(sf.quantidade_leitos_uti_sus_neonatal),
                    0
                ) AS sus_neonatal,

                COALESCE(
                    SUM(sf.quantidade_leitos_uti_queimado),
                    0
                ) AS queimado,

                COALESCE(
                    SUM(sf.quantidade_leitos_uti_sus_queimado),
                    0
                ) AS sus_queimado,

                COALESCE(
                    SUM(sf.quantidade_leitos_uti_coronariana),
                    0
                ) AS coronariana,

                COALESCE(
                    SUM(sf.quantidade_leitos_uti_sus_coronariana),
                    0
                ) AS sus_coronariana

            FROM snapshot_filtrado sf
        ),

        evolucao AS (
            SELECT
                l.data_de_competencia AS competencia,

                COALESCE(
                    SUM(l.quantidade_leitos_gerais),
                    0
                ) AS leitos_gerais,

                COALESCE(
                    SUM(l.quantidade_leitos_sus),
                    0
                ) AS leitos_sus,

                COALESCE(
                    SUM(l.quantidade_leitos_uti),
                    0
                ) AS leitos_uti,

                COALESCE(
                    SUM(l.quantidade_leitos_uti_sus),
                    0
                ) AS leitos_uti_sus,

                COUNT(
                    DISTINCT l.instituicao_id
                ) AS instituicoes

            FROM leitos l

            JOIN instituicao i
                ON i.instituicao_id = l.instituicao_id

            LEFT JOIN endereco e
                ON e.endereco_id = i.endereco_id

            LEFT JOIN municipio mun
                ON mun.codigo_do_municipio = e.municipio_id

            WHERE
                l.data_de_competencia
                    >= %(data_inicio)s

                AND l.data_de_competencia
                    <= %(data_fim)s

                {filtro_evolucao}

            GROUP BY
                l.data_de_competencia
        ),

        instituicoes_ranking AS (
            SELECT
                sf.instituicao_id,

                COALESCE(
                    NULLIF(
                        BTRIM(sf.nome_instituicao),
                        ''
                    ),
                    'Instituicao nao informada'
                ) AS instituicao,

                COALESCE(
                    NULLIF(
                        BTRIM(sf.municipio),
                        ''
                    ),
                    'Nao informado'
                ) AS municipio,

                COALESCE(
                    NULLIF(
                        BTRIM(sf.sigla_uf),
                        ''
                    ),
                    'Nao informado'
                ) AS uf,

                sf.data_de_competencia
                    AS competencia,

                COALESCE(
                    sf.quantidade_leitos_gerais,
                    0
                ) AS leitos_gerais,

                COALESCE(
                    sf.quantidade_leitos_sus,
                    0
                ) AS leitos_sus,

                COALESCE(
                    sf.quantidade_leitos_uti,
                    0
                ) AS leitos_uti,

                COALESCE(
                    sf.quantidade_leitos_uti_sus,
                    0
                ) AS leitos_uti_sus

            FROM snapshot_filtrado sf

            ORDER BY
                sf.quantidade_leitos_gerais
                    DESC NULLS LAST,
                instituicao,
                sf.instituicao_id

            LIMIT 100
        )

        SELECT
            (
                SELECT row_to_json(k)
                FROM kpis k
            ) AS kpis,

            COALESCE(
                (
                    SELECT json_agg(
                        p
                        ORDER BY
                            p.leitos_gerais DESC
                    )
                    FROM por_uf p
                ),
                '[]'::json
            ) AS por_uf,

            (
                SELECT json_build_array(
                    json_build_object(
                        'tipo_uti',
                        'Adulto',
                        'total',
                        t.adulto,
                        'sus',
                        t.sus_adulto
                    ),
                    json_build_object(
                        'tipo_uti',
                        'Pediatrica',
                        'total',
                        t.pediatrico,
                        'sus',
                        t.sus_pediatrico
                    ),
                    json_build_object(
                        'tipo_uti',
                        'Neonatal',
                        'total',
                        t.neonatal,
                        'sus',
                        t.sus_neonatal
                    ),
                    json_build_object(
                        'tipo_uti',
                        'Queimados',
                        'total',
                        t.queimado,
                        'sus',
                        t.sus_queimado
                    ),
                    json_build_object(
                        'tipo_uti',
                        'Coronariana',
                        'total',
                        t.coronariana,
                        'sus',
                        t.sus_coronariana
                    )
                )
                FROM tipos_uti_agregado t
            ) AS tipos_uti,

            COALESCE(
                (
                    SELECT json_agg(
                        ev
                        ORDER BY
                            ev.competencia
                    )
                    FROM evolucao ev
                ),
                '[]'::json
            ) AS evolucao,

            COALESCE(
                (
                    SELECT json_agg(
                        ir
                        ORDER BY
                            ir.leitos_gerais
                                DESC NULLS LAST,
                            ir.instituicao,
                            ir.instituicao_id
                    )
                    FROM instituicoes_ranking ir
                ),
                '[]'::json
            ) AS instituicoes;
    """,
        sf=f"""
        WITH {cte},

        snapshot_geo AS (
            SELECT
                s.*,
                i.nome_instituicao,
                mun.municipio,
                mun.sigla_uf

            FROM snapshot_leitos s

            JOIN instituicao i
                ON i.instituicao_id = s.instituicao_id

            LEFT JOIN endereco e
                ON e.endereco_id = i.endereco_id

            LEFT JOIN municipio mun
                ON mun.codigo_do_municipio = e.municipio_id
        ),

        snapshot_filtrado AS (
            SELECT *
            FROM snapshot_geo sg
            WHERE 1 = 1
            {filtro_snapshot}
        ),

        kpis AS (
            SELECT
                COALESCE(
                    SUM(sf.quantidade_leitos_gerais),
                    0
                ) AS leitos_gerais,

                COALESCE(
                    SUM(sf.quantidade_leitos_sus),
                    0
                ) AS leitos_sus,

                COALESCE(
                    SUM(sf.quantidade_leitos_uti),
                    0
                ) AS leitos_uti,

                COALESCE(
                    SUM(sf.quantidade_leitos_uti_sus),
                    0
                ) AS leitos_uti_sus,

                COUNT(
                    DISTINCT sf.instituicao_id
                ) AS instituicoes_com_registro,

                MIN(
                    sf.data_de_competencia
                ) AS competencia_minima,

                MAX(
                    sf.data_de_competencia
                ) AS competencia_maxima

            FROM snapshot_filtrado sf
        ),

        por_uf AS (
            SELECT
                COALESCE(
                    NULLIF(
                        TRIM(sf.sigla_uf),
                        ''
                    ),
                    'Nao informado'
                ) AS uf,

                COALESCE(
                    SUM(sf.quantidade_leitos_gerais),
                    0
                ) AS leitos_gerais,

                COALESCE(
                    SUM(sf.quantidade_leitos_sus),
                    0
                ) AS leitos_sus,

                COALESCE(
                    SUM(sf.quantidade_leitos_uti),
                    0
                ) AS leitos_uti,

                COALESCE(
                    SUM(sf.quantidade_leitos_uti_sus),
                    0
                ) AS leitos_uti_sus,

                COUNT(
                    DISTINCT sf.instituicao_id
                ) AS instituicoes

            FROM snapshot_filtrado sf

            GROUP BY
                COALESCE(
                    NULLIF(
                        TRIM(sf.sigla_uf),
                        ''
                    ),
                    'Nao informado'
                )
        ),

        tipos_uti_agregado AS (
            SELECT
                COALESCE(
                    SUM(sf.quantidade_leitos_uti_adulto),
                    0
                ) AS adulto,

                COALESCE(
                    SUM(sf.quantidade_leitos_uti_sus_adulto),
                    0
                ) AS sus_adulto,

                COALESCE(
                    SUM(sf.quantidade_leitos_uti_pediatrico),
                    0
                ) AS pediatrico,

                COALESCE(
                    SUM(sf.quantidade_leitos_uti_sus_pediatrico),
                    0
                ) AS sus_pediatrico,

                COALESCE(
                    SUM(sf.quantidade_leitos_uti_neonatal),
                    0
                ) AS neonatal,

                COALESCE(
                    SUM(sf.quantidade_leitos_uti_sus_neonatal),
                    0
                ) AS sus_neonatal,

                COALESCE(
                    SUM(sf.quantidade_leitos_uti_queimado),
                    0
                ) AS queimado,

                COALESCE(
                    SUM(sf.quantidade_leitos_uti_sus_queimado),
                    0
                ) AS sus_queimado,

                COALESCE(
                    SUM(sf.quantidade_leitos_uti_coronariana),
                    0
                ) AS coronariana,

                COALESCE(
                    SUM(sf.quantidade_leitos_uti_sus_coronariana),
                    0
                ) AS sus_coronariana

            FROM snapshot_filtrado sf
        ),

        evolucao AS (
            SELECT
                l.data_de_competencia AS competencia,

                COALESCE(
                    SUM(l.quantidade_leitos_gerais),
                    0
                ) AS leitos_gerais,

                COALESCE(
                    SUM(l.quantidade_leitos_sus),
                    0
                ) AS leitos_sus,

                COALESCE(
                    SUM(l.quantidade_leitos_uti),
                    0
                ) AS leitos_uti,

                COALESCE(
                    SUM(l.quantidade_leitos_uti_sus),
                    0
                ) AS leitos_uti_sus,

                COUNT(
                    DISTINCT l.instituicao_id
                ) AS instituicoes

            FROM leitos l

            JOIN instituicao i
                ON i.instituicao_id = l.instituicao_id

            LEFT JOIN endereco e
                ON e.endereco_id = i.endereco_id

            LEFT JOIN municipio mun
                ON mun.codigo_do_municipio = e.municipio_id

            WHERE
                l.data_de_competencia
                    >= %(data_inicio)s

                AND l.data_de_competencia
                    <= %(data_fim)s

                {filtro_evolucao}

            GROUP BY
                l.data_de_competencia
        ),

        instituicoes_ranking AS (
            SELECT
                sf.instituicao_id,

                COALESCE(
                    NULLIF(
                        TRIM(sf.nome_instituicao),
                        ''
                    ),
                    'Instituicao nao informada'
                ) AS instituicao,

                COALESCE(
                    NULLIF(
                        TRIM(sf.municipio),
                        ''
                    ),
                    'Nao informado'
                ) AS municipio,

                COALESCE(
                    NULLIF(
                        TRIM(sf.sigla_uf),
                        ''
                    ),
                    'Nao informado'
                ) AS uf,

                sf.data_de_competencia
                    AS competencia,

                COALESCE(
                    sf.quantidade_leitos_gerais,
                    0
                ) AS leitos_gerais,

                COALESCE(
                    sf.quantidade_leitos_sus,
                    0
                ) AS leitos_sus,

                COALESCE(
                    sf.quantidade_leitos_uti,
                    0
                ) AS leitos_uti,

                COALESCE(
                    sf.quantidade_leitos_uti_sus,
                    0
                ) AS leitos_uti_sus

            FROM snapshot_filtrado sf

            ORDER BY
                sf.quantidade_leitos_gerais
                    DESC NULLS LAST,
                instituicao,
                sf.instituicao_id

            LIMIT 100
        )

        SELECT
            (
                SELECT OBJECT_CONSTRUCT_KEEP_NULL(
                        'leitos_gerais', k.leitos_gerais,
                        'leitos_sus', k.leitos_sus,
                        'leitos_uti', k.leitos_uti,
                        'leitos_uti_sus', k.leitos_uti_sus,
                        'instituicoes_com_registro', k.instituicoes_com_registro,
                        'competencia_minima', k.competencia_minima,
                        'competencia_maxima', k.competencia_maxima
                    )
                FROM kpis k
            ) AS kpis,

            COALESCE(
                (
                    SELECT ARRAY_AGG(
                    OBJECT_CONSTRUCT_KEEP_NULL(
                        'uf', p.uf,
                        'leitos_gerais', p.leitos_gerais,
                        'leitos_sus', p.leitos_sus,
                        'leitos_uti', p.leitos_uti,
                        'leitos_uti_sus', p.leitos_uti_sus,
                        'instituicoes', p.instituicoes
                    )
                    ) WITHIN GROUP (
                        ORDER BY
                            p.leitos_gerais DESC
                    )
                    FROM por_uf p
                ),
                ARRAY_CONSTRUCT()
            ) AS por_uf,

            (
                SELECT ARRAY_CONSTRUCT(
                    OBJECT_CONSTRUCT_KEEP_NULL(
                        'tipo_uti', 'Adulto',
                        'total', t.adulto,
                        'sus', t.sus_adulto
                    ),
                    OBJECT_CONSTRUCT_KEEP_NULL(
                        'tipo_uti', 'Pediatrica',
                        'total', t.pediatrico,
                        'sus', t.sus_pediatrico
                    ),
                    OBJECT_CONSTRUCT_KEEP_NULL(
                        'tipo_uti', 'Neonatal',
                        'total', t.neonatal,
                        'sus', t.sus_neonatal
                    ),
                    OBJECT_CONSTRUCT_KEEP_NULL(
                        'tipo_uti', 'Queimados',
                        'total', t.queimado,
                        'sus', t.sus_queimado
                    ),
                    OBJECT_CONSTRUCT_KEEP_NULL(
                        'tipo_uti', 'Coronariana',
                        'total', t.coronariana,
                        'sus', t.sus_coronariana
                    )
                )
                FROM tipos_uti_agregado t
            ) AS tipos_uti,

            COALESCE(
                (
                    SELECT ARRAY_AGG(
                    OBJECT_CONSTRUCT_KEEP_NULL(
                        'competencia', ev.competencia,
                        'leitos_gerais', ev.leitos_gerais,
                        'leitos_sus', ev.leitos_sus,
                        'leitos_uti', ev.leitos_uti,
                        'leitos_uti_sus', ev.leitos_uti_sus,
                        'instituicoes', ev.instituicoes
                    )
                    ) WITHIN GROUP (
                        ORDER BY
                            ev.competencia
                    )
                    FROM evolucao ev
                ),
                ARRAY_CONSTRUCT()
            ) AS evolucao,

            COALESCE(
                (
                    SELECT ARRAY_AGG(
                    OBJECT_CONSTRUCT_KEEP_NULL(
                        'instituicao_id', ir.instituicao_id,
                        'instituicao', ir.instituicao,
                        'municipio', ir.municipio,
                        'uf', ir.uf,
                        'competencia', ir.competencia,
                        'leitos_gerais', ir.leitos_gerais,
                        'leitos_sus', ir.leitos_sus,
                        'leitos_uti', ir.leitos_uti,
                        'leitos_uti_sus', ir.leitos_uti_sus
                    )
                    ) WITHIN GROUP (
                        ORDER BY
                            ir.leitos_gerais
                                DESC NULLS LAST,
                            ir.instituicao,
                            ir.instituicao_id
                    )
                    FROM instituicoes_ranking ir
                ),
                ARRAY_CONSTRUCT()
            ) AS instituicoes
        """,
    )

    return query, parametros


@lru_cache(maxsize=128)
def _buscar_painel_cache(
    engine: str,
    modo: str,
    uf: str,
    data_inicio_iso: str,
    data_fim_iso: str,
    cache_bucket: int,
):
    _ = cache_bucket

    data_inicio = date.fromisoformat(
        data_inicio_iso,
    )
    data_fim = date.fromisoformat(
        data_fim_iso,
    )

    query, parametros = (
        _query_painel(
            modo,
            uf,
            engine,
        )
    )

    parametros.update({
        "data_inicio": data_inicio,
        "data_fim": data_fim,
    })

    resultado = fetch_one(
        query,
        parametros,
    )

    if resultado is not None:
        return _json_do_snowflake(
            engine,
            resultado,
            ("kpis", "por_uf", "tipos_uti", "evolucao", "instituicoes"),
        )

    return {
        "kpis": {
            "leitos_gerais": 0,
            "leitos_sus": 0,
            "leitos_uti": 0,
            "leitos_uti_sus": 0,
            "instituicoes_com_registro": 0,
            "competencia_minima": None,
            "competencia_maxima": None,
        },
        "por_uf": [],
        "tipos_uti": [],
        "evolucao": [],
        "instituicoes": [],
    }


@router.get("/painel")
def get_painel_leitos(
    data_inicio: date,
    data_fim: date,
    modo: str = Query(
        default="ultima_competencia",
    ),
    uf: str = Query(default=""),
):
    """
    Endpoint principal da página React.

    Mantém exatamente os mesmos conjuntos de dados exibidos,
    mas calcula o snapshot uma única vez e devolve todas as
    seções em uma resposta.
    """
    modo = _validar_modo(
        modo,
    )

    if data_fim < data_inicio:
        raise HTTPException(
            status_code=400,
            detail=(
                "A data final não pode ser "
                "anterior à data inicial."
            ),
        )

    try:
        return _buscar_painel_cache(
            get_engine(),
            modo,
            uf.strip().upper(),
            data_inicio.isoformat(),
            data_fim.isoformat(),
            _cache_bucket(),
        )
    except (
        DatabaseError,
        RuntimeError,
        ValueError,
    ) as exc:
        raise _database_error(exc) from exc
