"""MkDocs hook that publishes the API reference generated from its OpenAPI contract (ADR-0012).

The reference of the API (endpoints, parameters, bodies, responses and the fields of every
schema) has a single source: the code, through FastAPI's OpenAPI contract (``Field``
descriptions and endpoint docstrings). On every build this hook renders that contract as the
page ``02-ddt/api-referencia.md``, in Spanish, so it can never fall out of step with the code.
The page is generated, never written to disk or versioned.

``render`` is a pure function of the contract, tested in ``tests/docs/``.
"""

import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

from mkdocs.config.defaults import MkDocsConfig
from mkdocs.structure.files import File, Files

PAGE = "02-ddt/api-referencia.md"
METHODS = ("get", "post", "put", "patch", "delete")
FORMATS = {"date": "fecha", "date-time": "fecha y hora", "binary": "binario"}
TYPES = {
    "string": "texto",
    "integer": "entero",
    "number": "número",
    "boolean": "booleano",
    "object": "objeto",
    "null": "null",
}

# FastAPI's default descriptions of the responses, in Spanish.
RESPONSES = {
    "Successful Response": "Respuesta correcta.",
    "Validation Error": "Datos de entrada no válidos (formato de FastAPI).",
}

type Json = Mapping[str, object]


def on_files(files: Files, config: MkDocsConfig) -> Files:
    """Adds the generated reference to the files of the site."""
    root = Path(__file__).resolve().parents[2]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))  # the project is not installed: import api from the root
    from api.main import create_app  # noqa: PLC0415 (needs the path above)

    files.append(File.generated(config, PAGE, content=render(create_app().openapi())))
    return files


def render(contract: Json) -> str:
    """The reference page, in Markdown, for an OpenAPI 3.1 contract."""
    info = _map(contract.get("info"))
    lines = [
        "# Referencia de la API",
        "",
        f"Generada del contrato OpenAPI de la versión **{_str(info.get('version'))}** al construir "
        "esta documentación: es la fuente única de los endpoints, sus parámetros, sus respuestas y "
        "los campos de cada esquema, y no se edita a mano "
        "([ADR-0012](../03-adr/0012-referencia-api-desde-openapi.md)). Las convenciones y las "
        "decisiones de diseño están en el [DDT de la API](api.md); cómo se usa, en el "
        "[manual](../04-manual-usuario/api.md). Con la API arrancada, la versión interactiva "
        "está en `/api/docs` y el contrato en `/api/openapi.json`.",
        "",
    ]
    for tag, operations in _by_tag(_map(contract.get("paths"))).items():
        lines += [f"## {tag}", ""]
        for method, path, operation in operations:
            lines += _operation(method, path, operation)
    schemas = _map(_map(contract.get("components")).get("schemas"))
    lines += ["## Esquemas", ""]
    for name in sorted(schemas):
        lines += _schema(name, _map(schemas[name]))
    return "\n".join(lines)


def _by_tag(paths: Json) -> dict[str, list[tuple[str, str, Json]]]:
    """The operations grouped by their first tag, in the order of the contract."""
    groups: dict[str, list[tuple[str, str, Json]]] = {}
    for path, item in paths.items():
        for method in METHODS:
            operation = _map(_map(item).get(method))
            if operation:
                tags = _list(operation.get("tags"))
                tag = _str(tags[0]) if tags else "Otros"
                groups.setdefault(tag, []).append((method, path, operation))
    return groups


def _operation(method: str, path: str, operation: Json) -> list[str]:
    anchor = _anchor(f"{method}-{path}")
    lines = [
        f"### `{method.upper()} {path}` {{ #{anchor} }}",
        "",
        f"**{_str(operation.get('summary'))}**",
        "",
    ]
    description = _str(operation.get("description"))
    if description:
        lines += [description, ""]
    parameters = [_map(p) for p in _list(operation.get("parameters"))]
    if parameters:
        lines += [
            "| Parámetro | En | Tipo | Obligatorio | Descripción |",
            "|-----------|----|------|-------------|-------------|",
        ]
        for parameter in parameters:
            schema = _map(parameter.get("schema"))
            description = _str(parameter.get("description")) or _str(schema.get("description"))
            lines.append(
                f"| `{_str(parameter.get('name'))}` | {_location(_str(parameter.get('in')))} "
                f"| {_type(schema)} | {_yes(bool(parameter.get('required')))} "
                f"| {_cell(description)} |"
            )
        lines.append("")
    body = _map(operation.get("requestBody"))
    if body:
        lines += [f"**Cuerpo**: {_content(_map(body.get('content')))}", ""]
    lines += ["| Respuesta | Contenido | Descripción |", "|-----------|-----------|-------------|"]
    for status, item in _map(operation.get("responses")).items():
        response = _map(item)
        lines.append(
            f"| `{status}` | {_content(_map(response.get('content')))} "
            f"| {_cell(_response_description(_str(response.get('description'))))} |"
        )
    return [*lines, ""]


def _schema(name: str, schema: Json) -> list[str]:
    # The schema's own description is the class docstring, in English like all code comments:
    # the reference shows the Spanish descriptions of its fields instead.
    lines = [f"### `{name}` {{ #{_schema_anchor(name)} }}", ""]
    values = _list(schema.get("enum"))
    if values:
        return [*lines, "Valores: " + ", ".join(f"`{_str(v)}`" for v in values) + ".", ""]
    properties = _map(schema.get("properties"))
    if not properties:
        return [*lines, f"Tipo: {_type(schema)}.", ""]
    required = {_str(r) for r in _list(schema.get("required"))}
    lines += [
        "| Campo | Tipo | Obligatorio | Descripción |",
        "|-------|------|-------------|-------------|",
    ]
    for field, item in properties.items():
        definition = _map(item)
        lines.append(
            f"| `{field}` | {_type(definition)} | {_yes(field in required)} "
            f"| {_cell(_str(definition.get('description')))} |"
        )
    return [*lines, ""]


def _type(schema: Json) -> str:
    """A short Spanish description of a JSON schema type, linking to referenced schemas."""
    reference = _str(schema.get("$ref"))
    if reference:
        name = reference.rsplit("/", 1)[-1]
        return f"[`{name}`](#{_schema_anchor(name)})"
    for combinator in ("anyOf", "oneOf"):
        options = [_type(_map(option)) for option in _list(schema.get(combinator))]
        if options:
            return " o ".join(dict.fromkeys(options))
    if "const" in schema:
        return f"`{_str(schema.get('const'))}`"
    values = _list(schema.get("enum"))
    if values:
        return " \\| ".join(f"`{_str(v)}`" for v in values)
    return _plain_type(schema)


def _plain_type(schema: Json) -> str:
    """The type of a schema without references, alternatives or fixed values."""
    kind = schema.get("type")
    if isinstance(kind, list):
        return " o ".join(_type({"type": k}) for k in kind)
    if kind == "array":
        return f"lista de {_type(_map(schema.get('items')))}"
    extra = schema.get("additionalProperties")
    if kind == "object" and isinstance(extra, Mapping):
        return f"objeto de {_type(extra)}"
    text = TYPES.get(_str(kind), _str(kind) or "cualquiera")
    form = FORMATS.get(_str(schema.get("format")))
    return f"{text} ({form})" if form else text


def _content(content: Json) -> str:
    if not content:
        return "—"
    parts = []
    for media, item in content.items():
        schema = _map(_map(item).get("schema"))
        parts.append(f"{_type(schema)} (`{media}`)" if schema else f"`{media}`")
    return ", ".join(parts)


def _response_description(text: str) -> str:
    return RESPONSES.get(text, text)


def _location(where: str) -> str:
    return {"path": "ruta", "query": "consulta", "header": "cabecera"}.get(where, where)


def _yes(value: bool) -> str:
    return "sí" if value else "no"


def _cell(text: str) -> str:
    """Text that fits in a table cell: one line and no unescaped pipes."""
    return " ".join(text.split()).replace("|", "\\|")


def _anchor(text: str) -> str:
    """``get-api-pokemon-pokemon`` for ``get-/api/pokemon/{pokemon}``."""
    return "-".join("".join(c if c.isalnum() else " " for c in text.lower()).split())


def _schema_anchor(name: str) -> str:
    return f"esquema-{name.lower()}"


def _map(value: object) -> Json:
    return value if isinstance(value, Mapping) else {}


def _list(value: object) -> Sequence[object]:
    return value if isinstance(value, list) else []


def _str(value: object) -> str:
    """JSON values as they are written in JSON: ``true``, ``null``…"""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return value if isinstance(value, str) else str(value)
