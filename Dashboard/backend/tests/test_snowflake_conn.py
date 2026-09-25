import os
import threading
import time

import pytest

from backend import snowflake_conn as sc


class FakeCursor:
    def __init__(self, behavior):
        self.behavior = behavior
        self.description = [("N",)]

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False

    def execute(self, sql, params):
        if isinstance(self.behavior, Exception):
            raise self.behavior

    def fetchall(self):
        return [(self.behavior,)]


class FakeConn:
    def __init__(self, behavior):
        self.behavior = behavior
        self.closed = False

    def cursor(self):
        return FakeCursor(self.behavior)

    def close(self):
        self.closed = True


@pytest.fixture(autouse=True)
def _reset_conn():
    sc._conn = None
    yield
    sc._conn = None


def test_reconecta_apos_erro_stale_e_tem_sucesso(monkeypatch):
    conns = [FakeConn(Exception("Session no longer exists")), FakeConn(1)]
    calls = []

    def fake_connect():
        calls.append(1)
        return conns.pop(0)

    monkeypatch.setattr(sc, "_connect", fake_connect)
    result = sc.run("SELECT 1", {})
    assert result == [{"N": 1}]
    assert len(calls) == 2
    assert sc._conn is not None


def test_stale_case_insensitive(monkeypatch):
    conns = [FakeConn(Exception("SESSION NO LONGER EXISTS")), FakeConn(7)]
    monkeypatch.setattr(sc, "_connect", lambda: conns.pop(0))
    assert sc.run("SELECT 1", {}) == [{"N": 7}]


def test_codigo_250002_e_stale(monkeypatch):
    conns = [FakeConn(Exception("250002: token expired")), FakeConn(9)]
    monkeypatch.setattr(sc, "_connect", lambda: conns.pop(0))
    assert sc.run("SELECT 1", {}) == [{"N": 9}]


def test_erro_nao_stale_propaga_sem_reconectar(monkeypatch):
    conns = [FakeConn(ValueError("erro de sintaxe SQL"))]
    calls = []
    monkeypatch.setattr(sc, "_connect", lambda: calls.append(1) or conns.pop(0))
    with pytest.raises(ValueError):
        sc.run("SELECT 1", {})
    assert len(calls) == 1


def test_reconexao_falha_nao_deixa_conexao_fechada_pendurada(monkeypatch):
    """Se _connect() falhar durante a reconexão, a próxima chamada tenta reconectar de novo."""
    attempts = {"n": 0}

    def fake_connect():
        attempts["n"] += 1
        if attempts["n"] == 1:
            return FakeConn(Exception("connection is closed"))
        if attempts["n"] == 2:
            raise RuntimeError("rede indisponível")
        return FakeConn(42)

    monkeypatch.setattr(sc, "_connect", fake_connect)

    with pytest.raises(RuntimeError):
        sc.run("SELECT 1", {})
    assert sc._conn is None

    result = sc.run("SELECT 1", {})
    assert result == [{"N": 42}]
    assert attempts["n"] == 3


def test_reconexao_concorrente_sem_corrida(monkeypatch):
    """8 threads batem numa sessão expirada ao mesmo tempo: só uma deve reconectar,
    nenhuma conexão saudável pode ser fechada por engano, e todas as 8 devem ter sucesso."""
    made = []
    made_lock = threading.Lock()

    class RaceConn:
        def __init__(self, i):
            self.i = i
            self.closed = False
            self.expired = i == 0

        def cursor(self):
            return RaceCursor(self)

        def close(self):
            self.closed = True

    class RaceCursor:
        def __init__(self, conn):
            self.conn = conn
            self.description = [("N",)]

        def __enter__(self):
            return self

        def __exit__(self, *exc_info):
            return False

        def execute(self, sql, params):
            time.sleep(0.05)
            if self.conn.expired:
                raise Exception("390114: Authentication token has expired")
            if self.conn.closed:
                raise Exception("250002 (08003): Connection is closed")

        def fetchall(self):
            return [(self.conn.i,)]

    def fake_connect():
        with made_lock:
            conn = RaceConn(len(made))
            made.append(conn)
        time.sleep(0.02)
        return conn

    monkeypatch.setattr(sc, "_connect", fake_connect)
    sc._get_conn()  # abre a primeira conexão (expirada) antes das threads

    results = []

    def worker():
        try:
            results.append(sc.run("SELECT 1", {}))
        except Exception as exc:  # pragma: no cover - só em caso de falha do teste
            results.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(made) == 2, f"esperava exatamente 1 reconexão (2 connects), teve {len(made)}"
    assert not any(c.closed for c in made[1:]), "uma conexão saudável foi fechada por engano"
    assert results == [[{"N": made[1].i}]] * 8


def test_secret_file_ausente_gera_runtimeerror_claro(monkeypatch, tmp_path):
    caminho = str(tmp_path / "nao-existe.json")
    monkeypatch.setenv("SNOWFLAKE_SECRET_FILE", caminho)
    monkeypatch.delenv("SNOWFLAKE_SECRET_ID", raising=False)
    with pytest.raises(RuntimeError, match="SNOWFLAKE_SECRET_FILE não encontrado"):
        sc._secret()


def test_sem_secret_file_nem_secret_id_gera_runtimeerror_claro(monkeypatch):
    monkeypatch.delenv("SNOWFLAKE_SECRET_FILE", raising=False)
    monkeypatch.delenv("SNOWFLAKE_SECRET_ID", raising=False)
    with pytest.raises(RuntimeError):
        sc._secret()


def test_sessao_em_utc(monkeypatch):
    import snowflake.connector

    captured = {}
    monkeypatch.setattr(sc, "_secret", lambda: {"account": "acc", "username": "u", "password": "p"})
    monkeypatch.setattr(snowflake.connector, "connect", lambda **kw: captured.update(kw) or "conn")
    assert sc._connect() == "conn"
    assert captured["timezone"] == "UTC"


class _FakeBoto3:
    """boto3 falso: a sessão padrão (criada 1x) guarda credencial expirada; sessões novas funcionam."""

    def __init__(self, expired_sessions=1):
        self.sessions = 0
        self.calls = 0
        self.expired_sessions = expired_sessions
        fake = self

        class _Client:
            def __init__(self, expired):
                self.expired = expired

            def get_secret_value(self, SecretId):
                fake.calls += 1
                if self.expired:
                    raise Exception(
                        "An error occurred (ExpiredTokenException) when calling the GetSecretValue operation"
                    )
                return {"SecretString": '{"account": "acc", "username": "u", "password": "p"}'}

        class _Session:
            def __init__(self):
                fake.sessions += 1
                self.expired = fake.sessions <= fake.expired_sessions

            def client(self, *_a, **_k):
                return _Client(self.expired)

        class _SessionModule:
            Session = _Session

        self.session = _SessionModule
        self._default = None

    def client(self, *a, **k):  # boto3.client() reutiliza a sessão padrão, como o boto3 real
        if self._default is None:
            self._default = self.session.Session()
        return self._default.client(*a, **k)


def _usar_boto3_falso(monkeypatch, fake):
    import sys

    monkeypatch.delenv("SNOWFLAKE_SECRET_FILE", raising=False)
    monkeypatch.setenv("SNOWFLAKE_SECRET_ID", "prd/x")
    monkeypatch.setitem(sys.modules, "boto3", fake)
    monkeypatch.setitem(sys.modules, "boto3.session", fake.session)


def test_token_expirado_usa_sessao_nova(monkeypatch):
    fake = _FakeBoto3(expired_sessions=1)
    _usar_boto3_falso(monkeypatch, fake)
    monkeypatch.setenv("AWS_SESSION_TOKEN", "velho")
    assert sc._secret()["username"] == "u"
    assert fake.sessions == 2  # a segunda tentativa não reaproveita a sessão com a credencial expirada
    assert "AWS_SESSION_TOKEN" not in os.environ


def test_secret_fica_em_memoria_para_reconexoes(monkeypatch):
    fake = _FakeBoto3(expired_sessions=0)
    _usar_boto3_falso(monkeypatch, fake)
    sc._secret()
    sc._secret()
    assert fake.calls == 1
