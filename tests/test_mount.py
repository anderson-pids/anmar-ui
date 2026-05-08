"""Testes do helper mount() — integra anmar-ui com FastAPI + Jinja2Templates."""
from pathlib import Path

from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.testclient import TestClient

from anmar_ui import mount, __version__


def test_version_exposed():
    """__version__ está exposto e segue semver."""
    assert __version__ == "0.1.0"


def test_mount_serves_static_css(tmp_path):
    """mount() expõe anmar.css em /static/anmar/v0.1/anmar.css."""
    app = FastAPI()
    templates = Jinja2Templates(directory=str(tmp_path))
    mount(app, templates)

    # Garante que existe um anmar.css no path real pra StaticFiles servir.
    # Se o bundle real já foi gerado (Task A10), preserva. Senão, cria stub mínimo.
    static_root = Path(__file__).parent.parent / "src" / "anmar_ui" / "static"
    static_root.mkdir(parents=True, exist_ok=True)
    css_path = static_root / "anmar.css"
    if not css_path.exists():
        css_path.write_text("/* stub */", encoding="utf-8")

    client = TestClient(app)
    resp = client.get("/static/anmar/v0.1/anmar.css")
    assert resp.status_code == 200
    # Aceita stub OU bundle real (tem token --anmar-bordo)
    assert "stub" in resp.text or "--anmar-bordo" in resp.text


def test_mount_adds_templates_to_jinja(tmp_path):
    """mount() adiciona anmar_ui templates ao Jinja2Templates do consumidor."""
    app_templates_dir = tmp_path / "app_templates"
    app_templates_dir.mkdir()
    (app_templates_dir / "page.html").write_text(
        '{% extends "anmar_ui/base.html" %}'
        '{% block content %}OI{% endblock %}',
        encoding="utf-8",
    )

    app = FastAPI()
    templates = Jinja2Templates(directory=str(app_templates_dir))
    mount(app, templates)

    # Garante que existe base.html (cria stub mínimo se ainda não existir).
    lib_templates = Path(__file__).parent.parent / "src" / "anmar_ui" / "templates" / "anmar_ui"
    lib_templates.mkdir(parents=True, exist_ok=True)
    base_path = lib_templates / "base.html"
    if not base_path.exists():
        base_path.write_text(
            "<!doctype html><html><body>{% block content %}{% endblock %}</body></html>",
            encoding="utf-8",
        )

    rendered = templates.get_template("page.html").render({"request": None})
    assert "OI" in rendered


def test_mount_path_uses_major_minor_version():
    """Path do static usa major.minor (v0.1) do __version__."""
    from anmar_ui.mount import _version_path

    assert _version_path("0.1.0") == "v0.1"
    assert _version_path("0.1.5") == "v0.1"
    assert _version_path("1.2.3") == "v1.2"
