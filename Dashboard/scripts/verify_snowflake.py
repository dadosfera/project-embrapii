#!/usr/bin/env python3
"""Confere a cópia no Snowflake contra o Postgres, coluna a coluna, sem trazer linhas.

Uso: scripts/tunnel.sh &  ;  .venv/bin/python scripts/verify_snowflake.py [--only t1,t2]

Para cada tabela (fora o estoque), uma única consulta por lado calcula: count(*), count(col) de toda coluna,
sum/min/max das numéricas, min/max das datas/timestamps, sum(length(col)) dos textos e a contagem de TRUE dos
booleanos. Numéricos exatos e textos comparam por igualdade; só somas de float usam tolerância relativa.
Para `instituicao_estoca_produto` (recorte) calcula o mesmo SÓ no Snowflake — não há consulta ao Postgres —
e informa NULLs e vazios por coluna de texto. Sai com código != 0 se algo divergir.
"""
from __future__ import annotations

import argparse
import datetime as dt
import math
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend import snowflake_conn  # noqa: E402
from backend.database import get_connection  # noqa: E402

STOCK = "instituicao_estoca_produto"
NUMERIC = {"integer", "smallint", "bigint", "numeric", "real", "double precision"}
FLOAT = {"real", "double precision"}
TEMPORAL = {"date", "timestamp without time zone", "timestamp with time zone"}
TEXT = {"text", "character varying", "character"}


def pg_columns(cur, table: str):
    cur.execute(
        """SELECT column_name, data_type FROM information_schema.columns
           WHERE table_schema = 'public' AND table_name = %(t)s ORDER BY ordinal_position""",
        {"t": table},
    )
    return [(r["column_name"], r["data_type"]) for r in cur.fetchall()]


def sf_columns(table: str):
    """Colunas do Snowflake mapeadas para a família de tipo do Postgres (usado só no estoque)."""
    rows = snowflake_conn.run(
        """SELECT COLUMN_NAME, DATA_TYPE, NUMERIC_SCALE FROM INFORMATION_SCHEMA.COLUMNS
           WHERE TABLE_SCHEMA = 'EMBRAPII_DATASUS' AND TABLE_NAME = %(t)s ORDER BY ORDINAL_POSITION""",
        {"t": table.upper()},
    )
    fam = {"NUMBER": "numeric", "FLOAT": "double precision", "DATE": "date", "TEXT": "text",
           "BOOLEAN": "boolean", "TIMESTAMP_NTZ": "timestamp without time zone",
           "TIMESTAMP_LTZ": "timestamp with time zone", "TIMESTAMP_TZ": "timestamp with time zone"}
    return [(r["COLUMN_NAME"].lower(), fam.get(r["DATA_TYPE"], "text")) for r in rows]


def aggregates(cols, engine: str, text_extras: bool = False):
    """Lista de (alias, expressão, tipo_pg) — mesmos aliases nos dois engines."""
    q = (lambda c: f'"{c}"') if engine == "postgres" else (lambda c: c)
    out = [("n_rows", "count(*)", "bigint")]
    for i, (c, t) in enumerate(cols):
        col = q(c)
        out.append((f"c{i}_count", f"count({col})", "bigint"))
        if t in NUMERIC:
            out += [(f"c{i}_sum", f"sum({col})", t), (f"c{i}_min", f"min({col})", t),
                    (f"c{i}_max", f"max({col})", t)]
        elif t in TEMPORAL:
            out += [(f"c{i}_min", f"min({col})", t), (f"c{i}_max", f"max({col})", t)]
        elif t == "boolean":
            out.append((f"c{i}_true", f"sum(case when {col} then 1 else 0 end)", "bigint"))
        else:
            out.append((f"c{i}_len", f"sum(length({col}))", "bigint"))
            if text_extras:
                out.append((f"c{i}_empty", f"sum(case when {col} = '' then 1 else 0 end)", "bigint"))
    return out


def select_sql(table: str, aggs) -> str:
    return "SELECT " + ", ".join(f"{expr} AS {alias}" for alias, expr, _ in aggs) + f" FROM {table}"


def same(a, b, pg_type: str) -> bool:
    if a is None or b is None:
        return a is None and b is None
    if isinstance(a, dt.datetime) and isinstance(b, dt.datetime):
        if (a.tzinfo is None) != (b.tzinfo is None):
            return False
        return a == b  # aware × aware compara o instante
    if isinstance(a, (int, Decimal, float)) and isinstance(b, (int, Decimal, float)):
        if pg_type in FLOAT:
            return math.isclose(float(a), float(b), rel_tol=1e-9, abs_tol=1e-9)
        return Decimal(str(a)) == Decimal(str(b))
    return a == b


def verify_table(pg, table: str):
    with pg.cursor() as cur:
        cols = pg_columns(cur, table)
        pg_aggs = aggregates(cols, "postgres")
        cur.execute(select_sql(table, pg_aggs))
        pg_row = cur.fetchone()
    sf_aggs = aggregates(cols, "snowflake")
    sf_row = {k.lower(): v for k, v in snowflake_conn.run(select_sql(table.upper(), sf_aggs), {})[0].items()}
    names = {"n_rows": "count(*)"}
    for i, (c, _) in enumerate(cols):
        names.update({f"c{i}_{m}": f"{m}({c})" for m in ("count", "sum", "min", "max", "true", "len")})
    bad = [(names[a], pg_row[a], sf_row[a]) for a, _, t in pg_aggs if not same(pg_row[a], sf_row[a], t)]
    return len(pg_aggs), pg_row["n_rows"], sf_row["n_rows"], bad


def stock_report():
    cols = sf_columns(STOCK)
    aggs = aggregates(cols, "snowflake", text_extras=True)
    row = {k.lower(): v for k, v in snowflake_conn.run(select_sql(STOCK.upper(), aggs), {})[0].items()}
    n = row["n_rows"]
    print(f"\n{STOCK} (só Snowflake, recorte): {n} linhas")
    print(f"  {'coluna':34} {'tipo':28} {'NULL':>10} {'vazio':>8}  min / max / sum")
    for i, (c, t) in enumerate(cols):
        nulls = n - row[f"c{i}_count"]
        empty = row.get(f"c{i}_empty", "")
        extra = " / ".join(str(row[f"c{i}_{m}"]) for m in ("min", "max", "sum") if f"c{i}_{m}" in row)
        print(f"  {c:34} {t:28} {nulls:>10} {empty!s:>8}  {extra}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    args = ap.parse_args()
    tables = [t for t in (ROOT / "scripts" / "tables.txt").read_text().split() if t != STOCK]
    if args.only:
        wanted = [t for t in args.only.split(",") if t]
        unknown = sorted(set(wanted) - set(tables) - {STOCK})
        if unknown:
            sys.exit(f"--only com tabelas desconhecidas: {unknown}")
        tables = [t for t in tables if t in wanted]
    snowflake_conn.run("USE SCHEMA EMBRAPII_DATASUS", {})

    failed = []
    print(f"{'tabela':30} {'agregados':>9} {'linhas pg':>11} {'linhas sf':>11}  resultado")
    with get_connection() as pg:
        pg.autocommit = True
        with pg.cursor() as cur:
            cur.execute("SET TIME ZONE 'UTC'")
            cur.execute("SET statement_timeout = '10min'")
        for table in tables:
            n_aggs, n_pg, n_sf, bad = verify_table(pg, table)
            print(f"{table:30} {n_aggs:>9} {n_pg:>11} {n_sf:>11}  {'OK' if not bad else f'{len(bad)} DIVERGE'}")
            for metric, a, b in bad:
                print(f"    {metric}: pg={a!r} sf={b!r}")
            if bad:
                failed.append(table)
    if not args.only or STOCK in args.only.split(","):
        stock_report()
    if failed:
        sys.exit(f"\ndivergências em: {failed}")
    print("\nverificação OK")


if __name__ == "__main__":
    main()
