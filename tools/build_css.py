"""Concatena source/*.css na ordem correta → src/anmar_ui/static/anmar.css.

Sem minificação no MVP — bundle fica legível pra debug. Tamanho alvo <40KB.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))
from anmar_ui import __version__  # noqa: E402

SOURCES = [
    "tokens.css",
    "reset.css",
    "typography.css",
    "chrome.css",
    "forms.css",
    "data.css",
]
OUT = ROOT / "src" / "anmar_ui" / "static" / "anmar.css"


def build() -> Path:
    parts = [f"/* anmar-ui v{__version__} — bundle (concatenação de source/*.css) */\n\n"]
    for name in SOURCES:
        path = ROOT / "source" / name
        if not path.exists():
            raise FileNotFoundError(f"Source ausente: {path}")
        parts.append(f"/* === source/{name} === */\n")
        parts.append(path.read_text(encoding="utf-8"))
        parts.append("\n\n")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("".join(parts), encoding="utf-8")
    print(f"✓ {OUT} ({OUT.stat().st_size // 1024} KB)")
    return OUT


if __name__ == "__main__":
    build()
