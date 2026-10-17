"""Real browser coverage of the offline runtime and calendar's Spanish UI."""

import json
import os
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).parents[1] / "src/anmar_ui"


def test_spanish_runtime_and_dates_work_without_network():
    messages = json.loads((ROOT / "locales/es.json").read_text())
    messages.update(
        {
            "Animal {id} não encontrado": "Animal {id} no encontrado",
            "{id} = {id}": "Iguales: {id}",
            "Salvar": "Guardar",
        }
    )
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            executable_path=os.getenv("CHROMIUM_EXECUTABLE_PATH")
        )
        context = browser.new_context(locale="pt-BR", offline=True)
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.set_content(
            '<html lang="es"><form><label for="date">Fecha</label>'
            '<input id="date" name="date" type="date" required min="2026-10-01">'
            '<span id="name">Salvar</span></form></html>'
        )
        page.evaluate(
            "data => {const el = document.createElement('script');el.id='anmar-i18n';el.type='application/json';el.textContent=JSON.stringify(data);document.head.append(el)}",
            {"locale": "es", "messages": messages},
        )
        page.add_script_tag(path=str(ROOT / "static/i18n.js"))
        page.add_script_tag(path=str(ROOT / "static/dates-br.js"))
        assert page.evaluate("AnmarI18n.t('Salvar')") == "Guardar"
        assert (
            page.evaluate("AnmarI18n.t('Animal 123 não encontrado')")
            == "Animal 123 no encontrado"
        )
        assert (
            page.evaluate("AnmarI18n.t('Animal {id} não encontrado', {id:'$1'})")
            == "Animal $1 no encontrado"
        )
        assert page.evaluate("AnmarI18n.t('A = A')") == "Iguales: A"
        assert page.evaluate("AnmarI18n.t('A = B')") == "A = B"
        assert page.evaluate("AnmarI18n.t('constructor')") == "constructor"
        expect(page.locator("#name")).to_have_text("Salvar")
        field = page.get_by_role("textbox", name="Fecha", exact=True)
        expect(
            page.get_by_role("button", name="Abrir calendario: Fecha")
        ).to_be_visible()
        assert field.evaluate("el => el.validationMessage") == "Ingrese la fecha."
        field.fill("30092026")
        assert (
            field.evaluate("el => el.validationMessage")
            == "Use una fecha a partir de 01/10/2026."
        )
        field.fill("17102026")
        assert page.locator("#date").input_value() == "2026-10-17"
        assert field.evaluate("el => el.checkValidity()")
        assert errors == []
        browser.close()
