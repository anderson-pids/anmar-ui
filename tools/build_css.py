"""Concatena source/*.css na ordem correta → src/anmar_ui/static/anmar.css.

Sem minificação no MVP — bundle fica legível pra debug. Tamanho alvo <40KB.
"""
from pathlib import Path

ROOT = Path(__file__).parent.parent
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
    parts = ["/* anmar-ui v0.1.0 — bundle (concatenação de source/*.css) */\n\n"]
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
