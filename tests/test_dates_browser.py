"""Campo real em pt-BR, com navegador inglês e contrato ISO dos consumidores."""
import os
from pathlib import Path

import pytest
from playwright.sync_api import expect, sync_playwright

STATIC = Path(__file__).parents[1] / 'src/anmar_ui/static'


@pytest.fixture(params=['en-US', 'pt-BR'])
def page(request):
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=os.getenv('CHROMIUM_EXECUTABLE_PATH'))
        page = browser.new_page(locale=request.param, viewport={'width': 390, 'height': 844})
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.set_content('''<form id="form"><label for="data">Fabricação</label>
          <input type="date" id="data" name="data" value="2026-10-14" required>
          <label>Competência<input type="month" id="mes" name="mes" value="2026-10"></label>
          <button type="submit">Salvar</button><button type="reset">Limpar</button></form>''')
        page.add_style_tag(path=str(STATIC / 'dates-br.css'))
        page.add_script_tag(path=str(STATIC / 'dates-br.js'))
        page.evaluate('''() => {
          window.enviados = []; window.alteracoes = [];
          document.querySelector('#data').addEventListener('change', e => alteracoes.push(e.target.value));
          document.querySelector('#form').addEventListener('submit', e => {e.preventDefault(); enviados.push(Object.fromEntries(new FormData(e.target)));});
        }''')
        yield page
        assert errors == []
        browser.close()


def test_exibe_br_e_envia_iso_sem_inverter_dia_mes(page):
    campo = page.get_by_role('textbox', name='Fabricação', exact=True)
    expect(campo).to_have_value('14/10/2026')
    campo.fill('07102026')
    expect(campo).to_have_value('07/10/2026')
    page.get_by_role('button', name='Salvar').click()
    assert page.evaluate('enviados') == [{'data': '2026-10-07', 'mes': '2026-10'}]
    assert page.evaluate('alteracoes') == ['2026-10-07']
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')


def test_mes_e_inicializacao_por_script_reset_e_limpeza(page):
    campo = page.get_by_role('textbox', name='Fabricação', exact=True)
    mes = page.get_by_role('textbox', name='Competência', exact=True)
    expect(mes).to_have_value('10/2026')
    mes.fill('012027')
    expect(mes).to_have_value('01/2027')
    page.evaluate("document.querySelector('#data').value = '2024-02-29'")
    expect(campo).to_have_value('29/02/2024')
    page.get_by_role('button', name='Limpar').click()
    expect(campo).to_have_value('14/10/2026')
    expect(mes).to_have_value('10/2026')
    campo.fill('')
    page.get_by_role('button', name='Salvar').click()
    assert page.evaluate('enviados') == []


def test_datas_invalidas_limites_e_bissexto(page):
    campo = page.get_by_role('textbox', name='Fabricação', exact=True)
    for valor in ['31022026', '29022026', '0710', '00002026']:
        campo.fill(valor)
        page.get_by_role('button', name='Salvar').click()
        assert page.evaluate('enviados') == []
        assert page.locator('#data').input_value() == ''
    page.locator('#data').evaluate("e => {e.min='2024-02-01';e.max='2024-02-29'}")
    campo.fill('01032024')
    page.get_by_role('button', name='Salvar').click()
    assert page.evaluate('enviados') == []
    campo.fill('29022024')
    page.get_by_role('button', name='Salvar').click()
    assert page.evaluate('enviados[0].data') == '2024-02-29'


def test_formulario_dinamico_eventos_e_calendario(page):
    page.evaluate('''() => {
      document.querySelector('form').insertAdjacentHTML('beforeend', '<label for="dinamica">Transferência</label><input id="dinamica" name="transferencia" type="date">');
    }''')
    campo = page.get_by_role('textbox', name='Transferência', exact=True)
    campo.fill('31122026')
    expect(campo).to_have_value('31/12/2026')
    assert page.locator('#dinamica').input_value() == '2026-12-31'
    page.locator('#dinamica').evaluate('e => {e.showPicker = () => window.calendarioAberto = true}')
    page.get_by_role('button', name='Abrir calendário: Transferência', exact=True).click()
    assert page.evaluate('calendarioAberto')
    page.locator('#dinamica').evaluate("e => {e.value = '2027-01-01';e.dispatchEvent(new Event('change', {bubbles:true}));e.disabled = true}")
    expect(campo).to_have_value('01/01/2027')
    expect(campo).to_be_disabled()
    page.get_by_role('button', name='Salvar').click()
    assert 'transferencia' not in page.evaluate('enviados[0]')


def test_colagem_e_largura_intrinseca(page):
    campo = page.get_by_role('textbox', name='Fabricação', exact=True)
    for texto, esperado in [('7/10/2026', '2026-10-07'), ('07102026', '2026-10-07'), ('31/02/2026', '')]:
        campo.evaluate("""(e, text) => {const data = new DataTransfer();data.setData('text/plain', text); e.dispatchEvent(new ClipboardEvent('paste', {clipboardData:data, bubbles:true}));}""", texto)
        assert page.locator('#data').input_value() == esperado
    page.set_viewport_size({'width': 1280, 'height': 800})
    page.add_style_tag(content='form {display:flex; align-items:flex-end} label {width:auto} input {padding:12px}')
    for campo in page.locator('.anmar-date-display').all():
        assert campo.evaluate('e => e.scrollWidth <= e.clientWidth')


def test_month_sem_suporte_nativo(page):
    page.evaluate("""() => {
      const input = document.createElement('input');
      input.setAttribute('type', 'month'); input.id='fallback';input.name='fallback';
      Object.defineProperty(input, 'type', {value:'text'});
      input.value='2026-10';input.min='2026-09';input.max='2026-12';
      document.querySelector('form').append(input);
    }""")
    campo = page.locator('#fallback--br')
    expect(campo).to_have_value('10/2026')
    campo.fill('112026')
    page.get_by_role('button', name='Salvar').click()
    assert page.evaluate('enviados[0].fallback') == '2026-11'
    campo.fill('012027')
    assert not campo.evaluate('e => e.checkValidity()')


def test_selecao_real_no_calendario_atualiza_data_br(page):
    page.get_by_role('button', name='Abrir calendário: Fabricação', exact=True).click()
    page.keyboard.press('ArrowDown')
    page.keyboard.press('Enter')
    expect(page.get_by_role('textbox', name='Fabricação', exact=True)).to_have_value('21/10/2026')
    assert page.locator('#data').input_value() == '2026-10-21'
