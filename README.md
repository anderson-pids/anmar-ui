# anmar-ui

Design system compartilhado dos apps Anmar (`anmar-apps`, `anmar-rebanho`, `anmar-leite`, etc.).

Tokens (cores brand book + spacing + fonts) + chrome (header/nav/footer) + forms + componentes de dados (table responsivo, card, dl, badge). Mobile-first, sem JS framework.

Repo público. A fonte Atomic Alice (comercial LHFs) está coberta pela licença web da Anmar — não redistribuir fora desse contexto.

## Identidade

- Paleta oficial Anmar: bordô `#5C0508`, verde escuro `#376324`, verde lima `#78AE24`, amarelo sol `#F6C101`
- Display: Atomic Alice Medium (self-hosted, WOFF2)
- Body: Nunito (Google Fonts)

## Install

```bash
pip install git+https://github.com/anderson-pids/anmar-ui.git@v0.1.1
```

## Use no FastAPI

```python
from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from anmar_ui import mount as mount_ui

app = FastAPI()
templates = Jinja2Templates(directory="src/<seu_app>/templates")
mount_ui(app, templates)
```

Isso:
- Monta `/static/anmar/v0.1/anmar.css` e fontes
- Adiciona `anmar_ui/templates/` aos paths do Jinja2Templates do app

## Use no template

```jinja
{# src/<seu_app>/templates/base.html #}
{% extends "anmar_ui/base.html" %}

{% block app_name %}Rebanho{% endblock %}
{% block nav %}
  <a href="/">Dashboard</a>
  <a href="/animais">Animais</a>
{% endblock %}
{% block content %}{% endblock %}
```

## Componentes

Veja `demo/index.html` (abrir no browser via `python3 -m http.server` na raiz do repo).

Classes principais:

- **Forms**: `.anmar-form`, `.anmar-input`, `.anmar-select`, `.anmar-textarea`, `.anmar-label`, `.anmar-label--required`, `.anmar-btn`, `.anmar-btn--primary|accent|ghost|danger`
- **Tabela**: `.anmar-table` (mobile vira cards via `data-label` em cada `<td>`)
- **Card**: `.anmar-card`, `.anmar-card--status-prod|dev|planejado`, `.anmar-cards-grid`
- **Detail (dl)**: `.anmar-dl`
- **Badge**: `.anmar-badge`, `.anmar-badge--success|warning|danger|neutral`
- **Field messages**: `.anmar-field-error`, `.anmar-field-success`, `.anmar-field-help`

## Desenvolvimento

```bash
git clone https://github.com/anderson-pids/anmar-ui.git
cd anmar-ui
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"

# Rebuild CSS
.venv/bin/python tools/build_css.py

# Tests
.venv/bin/pytest

# Demo
python3 -m http.server 8765 && open http://127.0.0.1:8765/demo/
```

## Licença Atomic Alice

Atomic Alice Medium é fonte comercial da Letterhead Fonts. Use coberto por licença adquirida pela Anmar (Anderson Pimentel) — não redistribuir fora do escopo de apps Anmar.

## License

MIT — Anderson Pimentel.
