"""Converte TTF do brand book Anmar pra WOFF2 + WOFF.

Uso:
    python tools/convert_font.py <caminho-do-ttf>

Output em src/anmar_ui/static/fonts/.
"""
import sys
from pathlib import Path

from fontTools.ttLib import TTFont


def convert(ttf_path: Path, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    base = ttf_path.stem  # ex: "atomicalice-medium"

    # Normaliza nome: AtomicAlice-Medium
    name = "".join(p.capitalize() for p in base.replace("_", "-").split("-"))
    # "atomicalice-medium" -> "AtomicaliceMedium"; ajustar pra AtomicAlice-Medium
    if name.lower().startswith("atomicalice"):
        name = "AtomicAlice-" + name[len("Atomicalice"):]

    for flavor in ("woff2", "woff"):
        font = TTFont(str(ttf_path))
        font.flavor = flavor
        out = out_dir / f"{name}.{flavor}"
        font.save(str(out))
        print(f"✓ {out} ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    ttf = Path(sys.argv[1]).expanduser()
    if not ttf.exists():
        print(f"TTF não encontrado: {ttf}")
        sys.exit(1)

    out = Path(__file__).parent.parent / "src" / "anmar_ui" / "static" / "fonts"
    convert(ttf, out)
