from datetime import date
from functools import lru_cache
from time import monotonic

import psycopg
from fastapi import APIRouter, HTTPException, Query

from backend.database import fetch_all, fetch_one


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
        detail=f"Erro ao consultar o PostgreSQL: {exc}",
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


def _cte_snapshot_leitos(modo: str) -> str:
    """
    Replica a lógica documentada no spec.md.

    ultima_competencia:
      usa a competência mais recente existente na base.

    ultima_instituicao:
      usa a última posição conhecida de cada instituição.
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
) -> tuple[str, dict]:
    uf_normalizada = uf.strip().upper()

    if not uf_normalizada:
        return "", {}

    return (
        " AND mun.sigla_uf = %(uf)s",
        {"uf": uf_normalizada},
    )


@router.get("/intervalo")
def get_intervalo_competencias():
    query = """
        SELECT
            MIN(data_de_competencia) AS data_minima,
            MAX(data_de_competencia) AS data_maxima
        FROM leitos;
    """

    try:
        return fetch_one(query) or {
            "data_minima": None,
            "data_maxima": None,
        }
    except (psycopg.Error, RuntimeError) as exc:
        raise _database_error(exc) from exc


@router.get("/ufs")
def get_ufs():
    query = """
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
    """

    try:
        return fetch_all(query)
    except (psycopg.Error, RuntimeError) as exc:
        raise _database_error(exc) from exc


@router.get("/kpis")
def get_kpis(
    modo: str = Query(default="ultima_competencia"),
    uf: str = Query(default=""),
):
    cte = _cte_snapshot_leitos(modo)
    filtro_uf, parametros = _filtro_uf(uf)

    query = f"""
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
    """

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
    except (psycopg.Error, RuntimeError) as exc:
        raise _database_error(exc) from exc


@router.get("/por-uf")
def get_leitos_por_uf(
    modo: str = Query(default="ultima_competencia"),
    uf: str = Query(default=""),
):
    cte = _cte_snapshot_leitos(modo)
    filtro_uf, parametros = _filtro_uf(uf)

    query = f"""
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
    """

    try:
        return fetch_all(query, parametros)
    except (psycopg.Error, RuntimeError) as exc:
        raise _database_error(exc) from exc


@router.get("/tipos-uti")
def get_tipos_uti(
    modo: str = Query(default="ultima_competencia"),
    uf: str = Query(default=""),
):
    cte = _cte_snapshot_leitos(modo)
    filtro_uf, parametros = _filtro_uf(uf)

    query = f"""
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
    """

    try:
        return fetch_all(query, parametros)
    except (psycopg.Error, RuntimeError) as exc:
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

    query = f"""
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
    """

    try:
        return fetch_all(query, parametros)
    except (psycopg.Error, RuntimeError) as exc:
        raise _database_error(exc) from exc


@router.get("/instituicoes")
def get_instituicoes(
    modo: str = Query(default="ultima_competencia"),
    uf: str = Query(default=""),
    limite: int = Query(default=100, ge=1, le=100),
):
    cte = _cte_snapshot_leitos(modo)
    filtro_uf, parametros = _filtro_uf(uf)
    parametros["limite"] = limite

    query = f"""
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
            instituicao

        LIMIT %(limite)s;
    """

    try:
        return fetch_all(query, parametros)
    except (psycopg.Error, RuntimeError) as exc:
        raise _database_error(exc) from exc


# ============================================================
# ENDPOINTS OTIMIZADOS PARA A INTERFACE REACT
# ============================================================

@lru_cache(maxsize=4)
def _buscar_opcoes_cache(
    cache_bucket: int,
):
    """
    Busca intervalo e UFs em uma única conexão.

    Para obter as UFs, parte das instituições e usa EXISTS
    sobre leitos. Isso evita multiplicar cada instituição por
    todo o histórico de competências.
    """
    _ = cache_bucket

    query = """
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
    """

    return fetch_one(query) or {
        "data_minima": None,
        "data_maxima": None,
        "ufs": [],
    }


@router.get("/opcoes")
def get_opcoes_leitos():
    """
    Retorna, em uma única chamada, o intervalo de competências
    e as UFs disponíveis. O resultado fica em cache por até
    15 minutos.
    """
    try:
        return _buscar_opcoes_cache(
            _cache_bucket(),
        )
    except (psycopg.Error, RuntimeError) as exc:
        raise _database_error(exc) from exc


def _query_painel(
    modo: str,
    uf: str,
) -> tuple[str, dict]:
    cte = _cte_snapshot_leitos(
        modo,
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

    query = f"""
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
                instituicao

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
                            ir.instituicao
                    )
                    FROM instituicoes_ranking ir
                ),
                '[]'::json
            ) AS instituicoes;
    """

    return query, parametros


@lru_cache(maxsize=128)
def _buscar_painel_cache(
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

    return resultado or {
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
            modo,
            uf.strip().upper(),
            data_inicio.isoformat(),
            data_fim.isoformat(),
            _cache_bucket(),
        )
    except (
        psycopg.Error,
        RuntimeError,
        ValueError,
    ) as exc:
        raise _database_error(exc) from exc
