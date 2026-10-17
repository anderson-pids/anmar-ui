import json
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

from fastapi import FastAPI, HTTPException, Request
from fastapi.templating import Jinja2Templates
from fastapi.testclient import TestClient

from anmar_ui import mount
from anmar_ui.i18n import locale_for_request, translate_for_request


def make_client(tmp_path):
    (tmp_path / "locales").mkdir()
    (tmp_path / "locales/es.json").write_text(
        json.dumps(
            {
                "Salvar": "Guardar",
                "Animal {id} não encontrado": "Animal {id} no encontrado",
                "Olá {nome}": "Hola {nome}",
                "Teste seguro": "</script><script>alert(1)</script>",
            }
        )
    )
    (tmp_path / "page.html").write_text(
        '{% extends "anmar_ui/base.html" %}{% block content %}'
        '{{ t("Salvar") }}|{{ t("Olá {nome}", nome=nome) }}|{{ nome }}'
        "{% endblock %}"
    )
    app = FastAPI()
    templates = Jinja2Templates(directory=tmp_path)
    mount(app, templates)

    @app.middleware("http")
    async def identity(request, call_next):
        # Only this test supplies identity via a header. Production uses verified SSO.
        request.state.user = {"locale": request.headers.get("x-test-locale")}
        return await call_next(request)

    @app.get("/")
    def page(request: Request):
        return templates.TemplateResponse(request, "page.html", {"nome": "<María>"})

    @app.get("/error")
    def error():
        raise HTTPException(
            404, "Animal 123 não encontrado", headers={"X-Error": "kept"}
        )

    @app.get("/validation")
    def validation(quantity: int):
        return quantity

    @app.get("/business")
    def business():
        return {"nome": "Salvar", "status": "pendente"}

    return TestClient(app)


def test_only_validated_user_selects_locale():
    assert locale_for_request(None) == "pt-BR"
    for user, expected in [
        (None, "pt-BR"),
        ({}, "pt-BR"),
        ({"locale": "fr"}, "pt-BR"),
        ({"locale": "es"}, "es"),
    ]:
        request = SimpleNamespace(
            state=SimpleNamespace(user=user), cookies={"locale": "es"}
        )
        assert locale_for_request(request) == expected


def test_templates_translate_system_text_without_translating_user_data(tmp_path):
    client = make_client(tmp_path)
    es = client.get("/", headers={"x-test-locale": "es"}).text
    assert '<html lang="es">' in es
    assert "Guardar|Hola &lt;María&gt;|&lt;María&gt;" in es
    assert "Directo de la finca" in es
    assert "</script><script>alert(1)</script>" not in es
    pt = client.get("/").text
    assert '<html lang="pt-BR">' in pt
    assert "Salvar|Olá &lt;María&gt;|&lt;María&gt;" in pt
    # Portuguese is the source language and needs no translation payload.
    assert '"messages": {}' in pt


def test_concurrent_users_do_not_share_locale(tmp_path):
    client = make_client(tmp_path)

    def render(locale):
        result = client.get("/", headers={"x-test-locale": locale}).text
        return ("Guardar|" in result) == (locale == "es")

    with ThreadPoolExecutor(max_workers=6) as pool:
        assert all(pool.map(render, ["es", "pt-BR"] * 12))


def test_errors_translate_but_keep_status_headers_and_business_data(tmp_path):
    client = make_client(tmp_path)
    es = {"x-test-locale": "es"}
    response = client.get("/error", headers=es)
    assert response.status_code == 404
    assert response.headers["x-error"] == "kept"
    assert response.json() == {"detail": "Animal 123 no encontrado"}
    assert client.get("/error").json() == {"detail": "Animal 123 não encontrado"}
    assert client.get("/business", headers=es).json() == {
        "nome": "Salvar",
        "status": "pendente",
    }
    validation = client.get("/validation?quantity=abc", headers=es)
    assert validation.status_code == 422
    detail = validation.json()["detail"][0]
    assert detail["loc"] == ["query", "quantity"]
    assert detail["input"] == "abc"
    assert "entero" in detail["msg"]


def test_request_translation_interpolates_and_falls_back(tmp_path):
    client = make_client(tmp_path)
    request = SimpleNamespace(
        app=client.app, state=SimpleNamespace(user={"locale": "es"})
    )
    assert translate_for_request(request, "Olá {nome}", nome="Ana") == "Hola Ana"
    assert (
        translate_for_request(request, "Desconhecido {nome}", nome="Ana")
        == "Desconhecido Ana"
    )
    assert (
        translate_for_request(request, "Animal <123> não encontrado")
        == "Animal <123> no encontrado"
    )
    assert translate_for_request(None, "Salvar") == "Salvar"
