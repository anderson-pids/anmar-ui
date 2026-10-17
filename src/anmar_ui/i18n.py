"""Request-scoped translations. The authenticated SSO identity owns the locale."""

import json
import re
from pathlib import Path

from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from jinja2 import ChoiceLoader, FileSystemLoader, pass_context
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse

_SLOT = re.compile(r"\{([A-Za-z_]\w*)\}")
_COMMON_PATH = Path(__file__).parent / "locales" / "es.json"


def locale_for_request(request):
    user = getattr(getattr(request, "state", None), "user", None)
    return "es" if isinstance(user, dict) and user.get("locale") == "es" else "pt-BR"


def _interpolate(message, params):
    return _SLOT.sub(lambda m: str(params.get(m[1], m[0])), message)


class Catalog:
    def __init__(self, messages):
        self.messages = messages
        self.patterns = []
        for source, target in messages.items():
            slots = list(_SLOT.finditer(source))
            if not slots:
                continue
            parts, names, offset = [], set(), 0
            for slot in slots:
                name = slot[1]
                parts.append(re.escape(source[offset : slot.start()]))
                parts.append(f"(?P={name})" if name in names else f"(?P<{name}>.*?)")
                names.add(name)
                offset = slot.end()
            parts.append(re.escape(source[offset:]))
            self.patterns.append((re.compile("".join(parts), re.DOTALL), target))

    def translate(self, message, locale="pt-BR", **params):
        message = "" if message is None else str(message)
        if locale != "es":
            return _interpolate(message, params)
        target = self.messages.get(message)
        if target is not None:
            return _interpolate(target, params)
        # Legacy exceptions/UI helpers sometimes supply an already formatted message.
        # Only explicitly catalogued messages can match; no application data is scanned.
        for pattern, translated in self.patterns:
            match = pattern.fullmatch(message)
            if match:
                return _interpolate(translated, {**match.groupdict(), **params})
        return _interpolate(message, params)


def _catalog_for_request(request):
    state = getattr(getattr(request, "app", None), "state", None)
    return getattr(state, "anmar_i18n", _COMMON)


def translate_for_request(request, message, **params):
    return _catalog_for_request(request).translate(
        message, locale_for_request(request), **params
    )


def _read_catalog(path):
    messages = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(messages, dict) or not all(
        isinstance(k, str) and isinstance(v, str) for k, v in messages.items()
    ):
        raise ValueError(f"Translation catalog must map strings to strings: {path}")
    for source, target in messages.items():
        if set(_SLOT.findall(source)) != set(_SLOT.findall(target)):
            raise ValueError(f"Translation placeholders differ: {path}: {source}")
    return messages


def _catalog_paths(loader):
    if isinstance(loader, FileSystemLoader):
        for directory in loader.searchpath:
            path = Path(directory) / "locales" / "es.json"
            if path.exists():
                yield path
    elif isinstance(loader, ChoiceLoader):
        for child in reversed(loader.loaders):
            yield from _catalog_paths(child)


_COMMON = Catalog(_read_catalog(_COMMON_PATH))


def install(app, templates):
    messages = dict(_COMMON.messages)
    for path in _catalog_paths(templates.env.loader):
        messages.update(_read_catalog(path))
    catalog = Catalog(messages)
    app.state.anmar_i18n = catalog

    @pass_context
    def t(context, message, **params):
        return catalog.translate(
            message, locale_for_request(context.get("request")), **params
        )

    @pass_context
    def i18n_context(context):
        locale = locale_for_request(context.get("request"))
        return {
            "locale": locale,
            "messages": catalog.messages if locale == "es" else {},
        }

    templates.env.globals.update(
        t=t, locale_for_request=locale_for_request, i18n_context=i18n_context
    )
    templates.env.filters["t"] = t

    async def http_exception(request, exc):
        if exc.status_code in (204, 304) or exc.status_code < 200:
            from starlette.responses import Response

            return Response(status_code=exc.status_code, headers=exc.headers)
        detail = exc.detail
        if isinstance(detail, str):
            detail = translate_for_request(request, detail)
        return JSONResponse(
            {"detail": detail}, status_code=exc.status_code, headers=exc.headers
        )

    async def validation_exception(request, exc):
        errors = jsonable_encoder(exc.errors())
        for error in errors:
            message = error.get("msg", "")
            if locale_for_request(request) == "es" and message.startswith(
                "Value error, "
            ):
                message = message.removeprefix("Value error, ")
            error["msg"] = translate_for_request(request, message)
        return JSONResponse({"detail": errors}, status_code=422)

    # Keep consumer-owned handlers; these replace only FastAPI's defaults.
    from fastapi.exception_handlers import (
        http_exception_handler,
        request_validation_exception_handler,
    )

    if app.exception_handlers.get(HTTPException) is http_exception_handler:
        app.add_exception_handler(HTTPException, http_exception)
    if (
        app.exception_handlers.get(RequestValidationError)
        is request_validation_exception_handler
    ):
        app.add_exception_handler(RequestValidationError, validation_exception)
