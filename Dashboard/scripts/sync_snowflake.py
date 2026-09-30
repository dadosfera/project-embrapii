#!/usr/bin/env python3
"""Copia as tabelas do Dashboard do Postgres da UFMG (datalake_db2, via túnel) para o Snowflake EMBRAPII_DATASUS.

Uso: scripts/tunnel.sh &  ;  .venv/bin/python scripts/sync_snowflake.py [--only t1,t2] [--resume] [--include-stock]
Por padrão o estoque (recorte pesado, ~17 min no banco compartilhado) NÃO é copiado; --include-stock o inclui.
Cada tabela: COPY (SELECT) TO STDOUT em CSV (FORCE_QUOTE *) → CSV em disco → parquet com os tipos do Postgres →
PUT no stage → <T>__NEW (USING TEMPLATE + COPY INTO) → confere contagem → SWAP atômico com <T>.
Relatório em scripts/sync_report.json.

`instituicao_estoca_produto` (248 M linhas, 39 GB) é copiada recortada: só a posição mais recente de cada
(instituicao_id, produto_id). O DISTINCT ON roda uma única vez no servidor (no próprio COPY). Para todas as
tabelas a contagem de origem é a que o próprio COPY devolve (cur.rowcount); o tamanho da tabela cheia do
estoque vem de pg_class.reltuples.
A carga do estoque de 24/09/2026 usou o parser antigo; uma amostra TABLESAMPLE SYSTEM(0.1) (249 mil linhas) achou 0 textos tipo NA e 0 vazios em numero_do_lote/sigla/descricao, então não foi recarregada.
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


def copy_sql(table: str) -> str:
    # FORCE_QUOTE *: todo valor não nulo sai entre aspas; só NULL real sai como campo vazio sem aspas.
    return f"COPY ({source_sql(table)}) TO STDOUT WITH (FORMAT csv, HEADER, FORCE_QUOTE *, ENCODING 'UTF8')"


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
        if precision is None or scale is None:
            raise ValueError("numeric sem precisão declarada: passe a escala observada")
        if precision > 38:
            raise ValueError(f"numeric({precision},{scale}) não cabe em NUMBER(38)")
        return pa.decimal128(precision, scale)
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
    """Tipos explícitos a partir do information_schema (o CSV sozinho perde datas, numeric e boolean).

    `numeric` sem precisão declarada vira decimal128(38, S), com S = maior escala observada na coluna
    (consulta só em tabelas fora do estoque; as numeric do estoque são declaradas numeric(20,4)).
    """
    cur.execute(
        """SELECT column_name, data_type, numeric_precision, numeric_scale
           FROM information_schema.columns
           WHERE table_schema = 'public' AND table_name = %(t)s ORDER BY ordinal_position""",
        {"t": table},
    )
    cols = cur.fetchall()
    types = {}
    for r in cols:
        name, dt, prec, scale = r["column_name"], r["data_type"], r["numeric_precision"], r["numeric_scale"]
        if dt == "numeric" and prec is None:
            if table == STOCK:
                raise RuntimeError(f"{STOCK}.{name}: numeric sem precisão; não consultamos a escala no estoque")
            cur.execute(f'SELECT COALESCE(max(scale("{name}")), 0) AS s FROM {table}')
            prec, scale = 38, int(cur.fetchone()["s"])
        types[name] = arrow_type(dt, prec, scale)
    return types


def read_pg_csv(path: Path, types: dict) -> pa.Table:
    """Lê o CSV do COPY ... FORCE_QUOTE *: só campo vazio sem aspas é NULL; 'NA', 'NULL', '' etc. são texto."""
    return pacsv.read_csv(
        path,
        read_options=pacsv.ReadOptions(encoding="utf8"),
        parse_options=pacsv.ParseOptions(newlines_in_values=True),
        convert_options=pacsv.ConvertOptions(
            column_types=types,
            null_values=[""],
            strings_can_be_null=True,
            quoted_strings_can_be_null=False,
            true_values=["t"],
            false_values=["f"],
        ),
    )


def export_parquet(pg, table: str, types: dict, workdir: Path, out: Path) -> int:
    """Faz o COPY em streaming para um CSV em disco e converte para parquet. Devolve as linhas do COPY."""
    csv_path = workdir / f"{table}.csv"
    with pg.cursor() as cur:
        with open(csv_path, "wb") as f:
            with cur.copy(copy_sql(table)) as cp:
                for chunk in cp:
                    f.write(chunk)
        copied = cur.rowcount
    if copied is None or copied < 0:
        raise RuntimeError(f"{table}: COPY não informou a contagem de linhas")
    tbl = read_pg_csv(csv_path, types)
    csv_path.unlink()
    tbl = tbl.rename_columns([c.upper() for c in tbl.column_names])
    pq.write_table(tbl, out)
    if copied != tbl.num_rows:
        raise RuntimeError(f"{table}: COPY reportou {copied} linhas, parquet tem {tbl.num_rows}")
    return copied


def table_exists(name: str) -> bool:
    rows = snowflake_conn.run(
        "SELECT COUNT(*) AS N FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = %(s)s AND TABLE_NAME = %(t)s",
        {"s": SCHEMA, "t": name},
    )
    return rows[0]["N"] > 0


def load_snowflake(table: str, parquet: Path, expected: int) -> int:
    """Carrega em <T>__NEW, confere a contagem e só então troca com <T> (SWAP) e descarta a versão antiga."""
    t = table.upper()
    new = f"{t}__NEW"
    run = snowflake_conn.run
    try:
        run(f"REMOVE @EMBRAPII_SYNC/{t}/", {})
        run(f"PUT 'file://{parquet}' @EMBRAPII_SYNC/{t}/ OVERWRITE = TRUE AUTO_COMPRESS = FALSE", {})
        run(
            f"""CREATE OR REPLACE TABLE {new} USING TEMPLATE (
                  SELECT ARRAY_AGG(OBJECT_CONSTRUCT(*)) WITHIN GROUP (ORDER BY ORDER_ID)
                  FROM TABLE(INFER_SCHEMA(
                    LOCATION => '@EMBRAPII_SYNC/{t}/', FILE_FORMAT => 'EMBRAPII_PARQUET')))""",
            {},
        )
        run(f"COPY INTO {new} FROM @EMBRAPII_SYNC/{t}/ FILE_FORMAT = (FORMAT_NAME = 'EMBRAPII_PARQUET') "
            "MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE PURGE = TRUE", {})
        n = run(f"SELECT COUNT(*) AS N FROM {new}", {})[0]["N"]
        if n != expected:
            raise RuntimeError(f"{table}: {new} tem {n} linhas, esperado {expected}; {t} mantida")
        if table_exists(t):
            run(f"ALTER TABLE {t} SWAP WITH {new}", {})
            run(f"DROP TABLE {new}", {})  # depois do SWAP, __NEW é a versão antiga
        else:
            run(f"ALTER TABLE {new} RENAME TO {t}", {})
        return run(f"SELECT COUNT(*) AS N FROM {t}", {})[0]["N"]
    except Exception:
        try:
            run(f"DROP TABLE IF EXISTS {new}", {})
        except Exception as cleanup_exc:  # não mascara o erro original
            print(f"aviso: falha ao remover {new}: {cleanup_exc}", file=sys.stderr)
        raise


def prepare_snowflake() -> None:
    run = snowflake_conn.run
    run(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}", {})
    run(f"USE SCHEMA {SCHEMA}", {})
    run("CREATE FILE FORMAT IF NOT EXISTS EMBRAPII_PARQUET TYPE = PARQUET USE_LOGICAL_TYPE = TRUE", {})
    run("CREATE STAGE IF NOT EXISTS EMBRAPII_SYNC FILE_FORMAT = EMBRAPII_PARQUET", {})


def select_tables(all_tables, only: str, include_stock: bool):
    tables = list(all_tables)
    if only:
        wanted = [t for t in only.split(",") if t]
        unknown = sorted(set(wanted) - set(tables))
        if unknown:
            raise SystemExit(f"--only com tabelas fora de scripts/tables.txt: {unknown}")
        tables = [t for t in tables if t in wanted]
    if not include_stock:
        tables = [t for t in tables if t != STOCK]
    return tables


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--resume", action="store_true", help="pula tabelas já OK no relatório")
    ap.add_argument("--include-stock", action="store_true",
                    help=f"também copia {STOCK} (DISTINCT ON sobre 248 M linhas; só para recarga rara)")
    ap.add_argument("--skip-stock", action="store_true", help="sem efeito: o estoque já fica fora por padrão")
    args = ap.parse_args()
    tables = select_tables((ROOT / "scripts" / "tables.txt").read_text().split(), args.only,
                           args.include_stock and not args.skip_stock)
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
            report[table] = {"ok": False, "status": "carregando", "started": time.strftime("%Y-%m-%dT%H:%M:%S")}
            REPORT.write_text(json.dumps(report, indent=2))
            t0 = time.time()
            with pg.cursor() as cur:
                types = column_types(cur, table)
            with tempfile.TemporaryDirectory() as d:
                out = Path(d) / f"{table}.parquet"
                src = export_parquet(pg, table, types, Path(d), out)
                dst = load_snowflake(table, out, src)
            entry = {"source_rows": src, "snowflake_rows": dst, "seconds": round(time.time() - t0, 1),
                     "csv": "force_quote"}
            if table == STOCK:
                entry["recorte"] = "DISTINCT ON (instituicao_id, produto_id), posição mais recente"
                entry["source_total_estimate"] = cat.get(STOCK, {}).get("est")
            entry["ok"] = src == dst
            report[table] = entry
            REPORT.write_text(json.dumps(report, indent=2))
            print(f"{'OK' if entry['ok'] else 'DIVERGE'} {table}: pg={src} sf={dst} ({entry['seconds']}s)",
                  flush=True)

    bad = [t for t, r in report.items() if not r["ok"]]
    if bad:
        sys.exit(f"contagens divergentes ou incompletas: {bad}")
    print("sync completo")


if __name__ == "__main__":
    main()
