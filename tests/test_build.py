"""Build smoke: garantir que anmar.css existe e contém classes/tokens esperados."""
from pathlib import Path

CSS_PATH = Path(__file__).parent.parent / "src" / "anmar_ui" / "static" / "anmar.css"


def test_bundle_exists():
    assert CSS_PATH.exists(), f"Bundle não encontrado em {CSS_PATH}. Rode tools/build_css.py."


def test_bundle_has_brand_tokens():
    css = CSS_PATH.read_text(encoding="utf-8")
    for token in ("--anmar-bordo: #5C0508", "--anmar-verde-lima: #78AE24",
                  "--anmar-amarelo: #F6C101", "--anmar-verde-escuro: #376324"):
        assert token in css, f"Token ausente no bundle: {token}"


def test_bundle_has_chrome_classes():
    css = CSS_PATH.read_text(encoding="utf-8")
    for cls in (".anmar-header", ".anmar-header__nav", ".anmar-btn-logout",
                ".anmar-footer", ".anmar-main"):
        assert cls in css, f"Classe ausente: {cls}"


def test_bundle_has_form_classes():
    css = CSS_PATH.read_text(encoding="utf-8")
    for cls in (".anmar-form", ".anmar-input", ".anmar-btn", ".anmar-btn--primary",
                ".anmar-btn--accent", ".anmar-field-error"):
        assert cls in css, f"Classe ausente: {cls}"


def test_bundle_has_data_classes():
    css = CSS_PATH.read_text(encoding="utf-8")
    for cls in (".anmar-table", ".anmar-card", ".anmar-card--status-prod",
                ".anmar-dl", ".anmar-badge", ".anmar-badge--success"):
        assert cls in css, f"Classe ausente: {cls}"


def test_bundle_has_font_face():
    css = CSS_PATH.read_text(encoding="utf-8")
    assert '@font-face' in css
    assert 'Atomic Alice' in css
    assert 'AtomicAlice-Medium.woff2' in css


def test_bundle_size_reasonable():
    """Bundle não deve ser absurdamente grande pra MVP (<60KB sem minify)."""
    size = CSS_PATH.stat().st_size
    assert size < 60_000, f"Bundle muito grande: {size} bytes"
    assert size > 3_000, f"Bundle suspeitamente pequeno: {size} bytes"
