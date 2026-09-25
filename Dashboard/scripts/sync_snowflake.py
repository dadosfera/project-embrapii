#!/usr/bin/env python3
"""Copia as tabelas do Dashboard do Postgres da UFMG (datalake_db2, via túnel) para o Snowflake EMBRAPII_DATASUS.

Uso: scripts/tunnel.sh &  ;  .venv/bin/python scripts/sync_snowflake.py [--only t1,t2] [--resume]
Cada tabela: COPY (SELECT) TO STDOUT em CSV no servidor → CSV em disco → parquet com os tipos do Postgres →
PUT no stage → CREATE OR REPLACE TABLE ... USING TEMPLATE → COPY INTO → confere contagem.
Relatório em scripts/sync_report.json.

`instituicao_estoca_produto` (248 M linhas, 39 GB) é copiada recortada: só a posição mais recente de cada
(instituicao_id, produto_id). O DISTINCT ON roda uma única vez no servidor (no próprio COPY); a contagem de
origem dela é o total de linhas que o COPY exportou, e o tamanho da tabela cheia vem de pg_class.reltuples.
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
import time
from pathlib import Path

import pyarrow as pa
import pyarrow.csv as pacsv
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend import snowflake_conn  # noqa: E402
from backend.database import get_connection  # noqa: E402

REPORT = ROOT / "scripts" / "sync_report.json"
SCHEMA = "EMBRAPII_DATASUS"
MAX_BYTES = 5 * 1024**3
STATEMENT_TIMEOUT = "45min"
STOCK = "instituicao_estoca_produto"
STOCK_SQL = f"""
    SELECT DISTINCT ON (instituicao_id, produto_id) *
    FROM {STOCK}
    ORDER BY instituicao_id, produto_id,
             data_de_posicao_no_estoque DESC NULLS LAST,
             instituicao_estoca_produto_id DESC
"""


def source_sql(table: str) -> str:
    return STOCK_SQL if table == STOCK else f"SELECT * FROM {table}"


def pg_count(cur, table: str) -> int:
    """count(*) na origem. Nunca usado para o estoque (evita rodar o DISTINCT ON duas vezes)."""
    assert table != STOCK
    cur.execute(f"SELECT count(*) AS n FROM {table}")
    return cur.fetchone()["n"]


def catalog(cur, tables):
    """Tamanho e reltuples por relação (só catálogo, barato)."""
    cur.execute(
        """SELECT c.relname, pg_total_relation_size(c.oid) AS b, c.reltuples::bigint AS est
           FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
           WHERE n.nspname = 'public' AND c.relname = ANY(%(t)s)""",
        {"t": list(tables)},
    )
    return {r["relname"]: r for r in cur.fetchall()}


def arrow_type(data_type: str, precision, scale) -> pa.DataType:
    if data_type in ("integer", "smallint", "bigint"):
        return pa.int64()
    if data_type == "numeric":
        return pa.decimal128(precision, scale) if precision and precision <= 38 else pa.float64()
    if data_type in ("real", "double precision"):
        return pa.float64()
    if data_type == "date":
        return pa.date32()
    if data_type == "timestamp without time zone":
        return pa.timestamp("us")
    if data_type == "timestamp with time zone":
        return pa.timestamp("us", tz="UTC")
    if data_type == "boolean":
        return pa.bool_()
    return pa.string()


def column_types(cur, table: str) -> dict:
    """Tipos explícitos a partir do information_schema (o CSV sozinho perde datas, numeric e boolean)."""
    cur.execute(
        """SELECT column_name, data_type, numeric_precision, numeric_scale
           FROM information_schema.columns
           WHERE table_schema = 'public' AND table_name = %(t)s ORDER BY ordinal_position""",
        {"t": table},
    )
    return {r["column_name"]: arrow_type(r["data_type"], r["numeric_precision"], r["numeric_scale"])
            for r in cur.fetchall()}


def export_parquet(pg, table: str, types: dict, workdir: Path, out: Path) -> int:
    """Faz o COPY em streaming para um CSV em disco e converte para parquet. Devolve as linhas exportadas."""
    csv_path = workdir / f"{table}.csv"
    with pg.cursor() as cur:
        with open(csv_path, "wb") as f:
            with cur.copy(f"COPY ({source_sql(table)}) TO STDOUT WITH CSV HEADER") as cp:
                for chunk in cp:
                    f.write(chunk)
        copied = cur.rowcount
    tbl = pacsv.read_csv(
        csv_path,
        convert_options=pacsv.ConvertOptions(
            column_types=types,
            strings_can_be_null=True,
            # no CSV do Postgres, NULL é campo vazio sem aspas e '' é "" — manter a distinção
            quoted_strings_can_be_null=False,
            true_values=["t"],
            false_values=["f"],
        ),
    )
    csv_path.unlink()
    tbl = tbl.rename_columns([c.upper() for c in tbl.column_names])
    pq.write_table(tbl, out)
    if copied not in (-1, tbl.num_rows):
        raise RuntimeError(f"{table}: COPY reportou {copied} linhas, parquet tem {tbl.num_rows}")
    return tbl.num_rows


def load_snowflake(table: str, parquet: Path) -> int:
    t = table.upper()
    run = snowflake_conn.run
    run(f"REMOVE @EMBRAPII_SYNC/{t}/", {})
    run(f"PUT 'file://{parquet}' @EMBRAPII_SYNC/{t}/ OVERWRITE = TRUE AUTO_COMPRESS = FALSE", {})
    run(
        f"""CREATE OR REPLACE TABLE {t} USING TEMPLATE (
              SELECT ARRAY_AGG(OBJECT_CONSTRUCT(*)) WITHIN GROUP (ORDER BY ORDER_ID)
              FROM TABLE(INFER_SCHEMA(
                LOCATION => '@EMBRAPII_SYNC/{t}/', FILE_FORMAT => 'EMBRAPII_PARQUET')))""",
        {},
    )
    run(f"COPY INTO {t} FROM @EMBRAPII_SYNC/{t}/ FILE_FORMAT = (FORMAT_NAME = 'EMBRAPII_PARQUET') "
        "MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE PURGE = TRUE", {})
    return run(f"SELECT COUNT(*) AS N FROM {t}", {})[0]["N"]


def prepare_snowflake() -> None:
    run = snowflake_conn.run
    run(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}", {})
    run(f"USE SCHEMA {SCHEMA}", {})
    run("CREATE FILE FORMAT IF NOT EXISTS EMBRAPII_PARQUET TYPE = PARQUET USE_LOGICAL_TYPE = TRUE", {})
    run("CREATE STAGE IF NOT EXISTS EMBRAPII_SYNC FILE_FORMAT = EMBRAPII_PARQUET", {})


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--resume", action="store_true", help="pula tabelas já OK no relatório")
    args = ap.parse_args()
    tables = (ROOT / "scripts" / "tables.txt").read_text().split()
    if args.only:
        tables = [t for t in tables if t in args.only.split(",")]
    report = json.loads(REPORT.read_text()) if REPORT.exists() else {}

    prepare_snowflake()

    with get_connection() as pg:
        # autocommit: cada tabela é uma transação curta; não seguramos snapshot no banco compartilhado
        pg.autocommit = True
        with pg.cursor() as cur:
            cur.execute("SET TIME ZONE 'UTC'")
            cur.execute("SET datestyle = 'ISO, YMD'")
            cur.execute(f"SET statement_timeout = '{STATEMENT_TIMEOUT}'")
            cat = catalog(cur, tables)
        estimate = sum(r["b"] for t, r in cat.items() if t != STOCK)
        if estimate > MAX_BYTES:
            sys.exit(f"volume estimado {estimate / 1024**3:.1f} GB > 5 GB (sem contar o recorte do estoque)")
        for table in tables:
            if args.resume and report.get(table, {}).get("ok"):
                print(f"= {table} (já OK)")
                continue
            t0 = time.time()
            with pg.cursor() as cur:
                types = column_types(cur, table)
                src = None if table == STOCK else pg_count(cur, table)
            with tempfile.TemporaryDirectory() as d:
                out = Path(d) / f"{table}.parquet"
                exported = export_parquet(pg, table, types, Path(d), out)
                dst = load_snowflake(table, out)
            entry = {"source_rows": exported if table == STOCK else src, "exported_rows": exported,
                     "snowflake_rows": dst, "seconds": round(time.time() - t0, 1)}
            if table == STOCK:
                entry["recorte"] = "DISTINCT ON (instituicao_id, produto_id), posição mais recente"
                entry["source_total_estimate"] = cat.get(STOCK, {}).get("est")
            entry["ok"] = entry["source_rows"] == exported == dst
            report[table] = entry
            REPORT.write_text(json.dumps(report, indent=2))
            print(f"{'OK' if entry['ok'] else 'DIVERGE'} {table}: pg={entry['source_rows']} sf={dst} "
                  f"({entry['seconds']}s)", flush=True)

    bad = [t for t, r in report.items() if not r["ok"]]
    if bad:
        sys.exit(f"contagens divergentes: {bad}")
    print("sync completo")


if __name__ == "__main__":
    main()
