import importlib.util
import re
from decimal import Decimal
from pathlib import Path

import pyarrow as pa
import pytest

ROOT = Path(__file__).resolve().parents[2]

_spec = importlib.util.spec_from_file_location("sync_snowflake", ROOT / "scripts" / "sync_snowflake.py")
sync = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sync)

RELATION = re.compile(r"(?i)\b(?:from|join)\s+(?:public\.)?([a-z_][a-z0-9_]*)(?=[\s;),]|$)")


def referenced_relations():
    text = "\n".join(p.read_text() for p in (ROOT / "backend" / "api").glob("*.py"))
    sql_refs = set(RELATION.findall(text))
    ctes = set(re.findall(r"(?i)\b([a-z_][a-z0-9_]*)\s+as\s+(?:materialized\s+)?\(", text))
    py_imports = {"backend", "datetime", "fastapi", "functools", "time", "typing", "exc", "lateral"}
    return {r.lower() for r in sql_refs} - {c.lower() for c in ctes} - py_imports


def test_tables_txt_cobre_routers():
    tables = set((ROOT / "scripts" / "tables.txt").read_text().split())
    faltando = referenced_relations() - tables
    assert not faltando, f"routers citam relações fora de scripts/tables.txt: {sorted(faltando)}"


def test_regex_aceita_schema_e_terminadores():
    sql = "select * from public.leitos; select 1 from produto) x join catmat, y join municipio"
    assert RELATION.findall(sql) == ["leitos", "produto", "catmat", "municipio"]


def test_csv_force_quote_preserva_textos_que_parecem_nulo(tmp_path):
    # Formato do COPY ... WITH (FORMAT csv, HEADER, FORCE_QUOTE *): valor não nulo sempre entre aspas,
    # NULL real é campo vazio sem aspas.
    csv = tmp_path / "t.csv"
    csv.write_bytes(
        b'id,txt,n,d\n'
        b'"1","NA","1.5000","2024-01-02"\n'
        b'"2","N/A",,\n'
        b'"3","NULL","2",\n'
        b'"4","nan",,\n'
        b'"5","",,\n'
        b'"6",,,\n'
        b'"7","linha 1\nlinha 2 \xc3\xa7",,\n'
    )
    types = {"id": pa.int64(), "txt": pa.string(), "n": pa.decimal128(20, 4), "d": pa.date32()}
    tbl = sync.read_pg_csv(csv, types)
    assert tbl.column("txt").to_pylist() == ["NA", "N/A", "NULL", "nan", "", None, "linha 1\nlinha 2 ç"]
    assert tbl.column("n").to_pylist()[:3] == [Decimal("1.5000"), None, Decimal("2.0000")]
    assert tbl.column("d").null_count == 6
    assert tbl.schema.field("n").type == pa.decimal128(20, 4)


def test_copy_sql_forca_aspas_e_utf8():
    sql = sync.copy_sql("municipio")
    assert "FORCE_QUOTE *" in sql and "ENCODING 'UTF8'" in sql and "HEADER" in sql


def test_numeric_sem_precisao_exige_escala():
    with pytest.raises(ValueError):
        sync.arrow_type("numeric", None, None)
    assert sync.arrow_type("numeric", 38, 6) == pa.decimal128(38, 6)
    assert sync.arrow_type("double precision", None, None) == pa.float64()


def test_only_desconhecida_falha_e_skip_stock():
    tables = ["municipio", sync.STOCK, "leitos"]
    with pytest.raises(SystemExit):
        sync.select_tables(tables, "municipio,nao_existe", False)
    assert sync.select_tables(tables, "", True) == ["municipio", "leitos"]
    assert sync.select_tables(tables, f"{sync.STOCK},leitos", True) == ["leitos"]
