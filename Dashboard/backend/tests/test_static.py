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
    assert r.status_code == 200
    assert '<base href="/">' in r.text


def test_raiz_com_prefixo_serve_index_com_e_sem_barra(tmp_path, monkeypatch):
    c = make_client(tmp_path, monkeypatch, base="/pbp-x_8000")
    r_com_barra = c.get("/pbp-x_8000/")
    r_sem_barra = c.get("/pbp-x_8000")
    for r in (r_com_barra, r_sem_barra):
        assert r.status_code == 200
        assert '<base href="/pbp-x_8000/">' in r.text


def test_raiz_local_serve_index_quando_dist_existe(tmp_path, monkeypatch):
    c = make_client(tmp_path, monkeypatch, base="")
    r = c.get("/")
    assert r.status_code == 200
    assert '<base href="/">' in r.text


def test_healthcare_nao_e_bloqueado_como_health(tmp_path, monkeypatch):
    c = make_client(tmp_path, monkeypatch, base="/pbp-x_8000")
    r = c.get("/pbp-x_8000/healthcare")
    assert r.status_code == 200
    assert '<base href="/pbp-x_8000/">' in r.text


def test_api_prefixo_continua_bloqueado(tmp_path, monkeypatch):
    c = make_client(tmp_path, monkeypatch, base="/pbp-x_8000")
    r = c.get("/pbp-x_8000/api/rota-inexistente")
    assert r.status_code == 404


def test_path_traversal_nao_escapa_do_dist(tmp_path, monkeypatch):
    c = make_client(tmp_path, monkeypatch, base="/pbp-x_8000")
    r = c.get("/pbp-x_8000/../backend/main.py", follow_redirects=False)
    assert r.status_code in (200, 404)
    assert "def install" not in r.text
    assert "psycopg" not in r.text


def test_path_traversal_percent_encoded_nao_escapa_do_dist(tmp_path, monkeypatch):
    c = make_client(tmp_path, monkeypatch, base="/pbp-x_8000")
    r = c.get("/pbp-x_8000/%2e%2e/backend/main.py", follow_redirects=False)
    assert r.status_code in (200, 404)
    assert "def install" not in r.text
    assert "psycopg" not in r.text
