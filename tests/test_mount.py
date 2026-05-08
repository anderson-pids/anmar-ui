"""Testes do helper mount() — integra anmar-ui com FastAPI + Jinja2Templates."""
from pathlib import Path

import pytest
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

    # Cria stub do CSS pra teste passar antes do build real (Task A10 cria de verdade)
    static_root = Path(__file__).parent.parent / "src" / "anmar_ui" / "static"
    (static_root / "anmar.css").parent.mkdir(parents=True, exist_ok=True)
    (static_root / "anmar.css").write_text("/* stub */", encoding="utf-8")

    client = TestClient(app)
    resp = client.get("/static/anmar/v0.1/anmar.css")
    assert resp.status_code == 200
    assert "stub" in resp.text or "--anmar-bordo" in resp.text


def test_mount_adds_templates_to_jinja(tmp_path):
    """mount() adiciona anmar_ui templates ao Jinja2Templates do consumidor."""
    app_templates_dir = tmp_path / "app_templates"
    app_templates_dir.mkdir()
    (app_templates_dir / "page.html").write_text(
        '{% extends "anmar_ui/base.html" %}{% block content %}OI{% endblock %}',
        encoding="utf-8",
    )

    app = FastAPI()
    templates = Jinja2Templates(directory=str(app_templates_dir))
    mount(app, templates)

    # Stub do template base na lib (Task A11 cria real)
    lib_templates = Path(__file__).parent.parent / "src" / "anmar_ui" / "templates" / "anmar_ui"
    lib_templates.mkdir(parents=True, exist_ok=True)
    (lib_templates / "base.html").write_text(
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
