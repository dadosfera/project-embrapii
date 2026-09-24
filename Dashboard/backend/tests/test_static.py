import importlib

from fastapi.testclient import TestClient


def make_client(tmp_path, monkeypatch, base=""):
    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text("<html><head><title>x</title></head><body></body></html>")
    (dist / "assets" / "app.js").write_text("console.log(1)")
    monkeypatch.setenv("FRONTEND_DIST", str(dist))
    monkeypatch.setenv("APP_BASE_PATH", base)
    import backend.main as main

    importlib.reload(main)
    return TestClient(main.app)


def test_spa_fallback_injeta_base(tmp_path, monkeypatch):
    c = make_client(tmp_path, monkeypatch, base="/pbp-x_8000")
    r = c.get("/pbp-x_8000/leitos")
    assert r.status_code == 200
    assert '<base href="/pbp-x_8000/">' in r.text
    assert 'window.__APP_BASE__="/pbp-x_8000"' in r.text


def test_asset_com_prefixo(tmp_path, monkeypatch):
    c = make_client(tmp_path, monkeypatch, base="/pbp-x_8000")
    r = c.get("/pbp-x_8000/assets/app.js")
    assert r.status_code == 200 and "console.log" in r.text


def test_health_com_e_sem_prefixo(tmp_path, monkeypatch):
    c = make_client(tmp_path, monkeypatch, base="/pbp-x_8000")
    assert c.get("/pbp-x_8000/health").json() == {"status": "ok"}
    assert c.get("/health").json() == {"status": "ok"}


def test_local_sem_prefixo(tmp_path, monkeypatch):
    c = make_client(tmp_path, monkeypatch, base="")
    r = c.get("/compras")
    assert '<base href="/">' in r.text
