"""Helper que integra anmar-ui com FastAPI + Jinja2Templates do consumidor."""
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jinja2 import ChoiceLoader, FileSystemLoader


_PKG_ROOT = Path(__file__).parent
_STATIC_DIR = _PKG_ROOT / "static"
_TEMPLATES_DIR = _PKG_ROOT / "templates"


def _version_path(version: str) -> str:
    """'0.1.0' -> 'v0.1' — paths versionados pra cache busting trivial."""
    major, minor = version.split(".")[:2]
    return f"v{major}.{minor}"


def mount(app: FastAPI, templates: Jinja2Templates) -> None:
    """Monta anmar-ui no app FastAPI.

    Após chamar:
      - GET /static/anmar/v{major}.{minor}/* serve arquivos de anmar_ui/static/
      - templates pode renderizar `{% extends "anmar_ui/base.html" %}`
    """
    from anmar_ui import __version__

    # 1. Static files
    app.mount(
        f"/static/anmar/{_version_path(__version__)}",
        StaticFiles(directory=str(_STATIC_DIR)),
        name="anmar_ui_static",
    )

    # 2. Adicionar templates da lib aos paths do Jinja2Templates do consumidor
    existing_loader = templates.env.loader
    lib_loader = FileSystemLoader(str(_TEMPLATES_DIR))
    if existing_loader is None:
        templates.env.loader = lib_loader
    else:
        templates.env.loader = ChoiceLoader([existing_loader, lib_loader])
