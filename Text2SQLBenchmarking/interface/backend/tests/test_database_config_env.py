from __future__ import annotations

from src.utilitis import get_db_config


DATABASE_ENV_NAMES = (
    "DATASUS_DB_HOST",
    "DATASUS_DB_PORT",
    "DATASUS_DB_NAME",
    "DATASUS_DB_USER",
    "DATASUS_DB_PASSWORD",
    "SIH_DATABASE_DB_HOST",
    "SIH_DATABASE_DB_PORT",
    "SIH_DATABASE_DB_NAME",
    "SIH_DATABASE_DB_USER",
    "SIH_DATABASE_DB_PASSWORD",
)


def _clear_database_environment(monkeypatch) -> None:
    for name in DATABASE_ENV_NAMES:
        monkeypatch.delenv(name, raising=False)


def test_database_config_without_overrides_preserves_registered_defaults(monkeypatch):
    _clear_database_environment(monkeypatch)

    datasus, datasus_ground_truth = get_db_config("datasus")
    sih, sih_ground_truth = get_db_config("sih_database")

    assert datasus is not None
    assert sih is not None
    assert datasus["SGBD"] == "postgresql"
    assert sih["SGBD"] == "postgresql"
    assert datasus["host"] == "localhost"
    assert datasus["port"] == "5433"
    assert sih["host"] == "localhost"
    assert sih["port"] == "5432"
    assert set(datasus) == {"SGBD", "user", "password", "host", "port", "db_name"}
    assert set(sih) == {"SGBD", "user", "password", "host", "port", "db_name"}
    assert datasus_ground_truth == "benchmark_curated"
    assert sih_ground_truth == "ground_truth"


def test_database_config_overrides_host_only(monkeypatch):
    _clear_database_environment(monkeypatch)
    baseline, _ = get_db_config("datasus")
    monkeypatch.setenv("DATASUS_DB_HOST", "db.example.internal")

    configured, _ = get_db_config("datasus")

    assert baseline is not None
    assert configured == {**baseline, "host": "db.example.internal"}


def test_database_config_overrides_port_only(monkeypatch):
    _clear_database_environment(monkeypatch)
    baseline, _ = get_db_config("sih_database")
    monkeypatch.setenv("SIH_DATABASE_DB_PORT", "55432")

    configured, _ = get_db_config("sih_database")

    assert baseline is not None
    assert configured == {**baseline, "port": "55432"}


def test_database_config_accepts_complete_override(monkeypatch):
    _clear_database_environment(monkeypatch)
    expected = {
        "host": "postgres.remote.internal",
        "port": "6543",
        "db_name": "remote_database",
        "user": "runtime_user",
        "password": "synthetic-password",
    }
    for suffix, value in (
        ("HOST", expected["host"]),
        ("PORT", expected["port"]),
        ("NAME", expected["db_name"]),
        ("USER", expected["user"]),
        ("PASSWORD", expected["password"]),
    ):
        monkeypatch.setenv(f"DATASUS_DB_{suffix}", value)

    configured, _ = get_db_config("datasus")

    assert configured == {"SGBD": "postgresql", **expected}


def test_override_for_one_database_does_not_affect_the_other(monkeypatch):
    _clear_database_environment(monkeypatch)
    baseline_sih, _ = get_db_config("sih_database")
    monkeypatch.setenv("DATASUS_DB_HOST", "jabuti.remote.internal")

    configured_datasus, _ = get_db_config("datasus")
    configured_sih, _ = get_db_config("sih_database")

    assert configured_datasus is not None
    assert configured_datasus["host"] == "jabuti.remote.internal"
    assert configured_sih == baseline_sih
