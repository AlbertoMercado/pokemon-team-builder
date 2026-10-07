"""The API reference generated from the OpenAPI contract (``docs/hooks/api_reference.py``,
ADR-0012).

The reference is the single source of the endpoints and fields of the API, so these tests also
require the contract to be complete: every endpoint, parameter and field has a description.
"""

import re

import pytest

from api.main import create_app
from docs.hooks.api_reference import render

# FastAPI's own schemas for its 422 responses: their fields are not ours to describe.
FASTAPI_SCHEMAS = {"HTTPValidationError", "ValidationError"}
METHODS = ("get", "post", "put", "patch", "delete")

type Json = dict[str, object]


@pytest.fixture(scope="module")
def contract() -> dict[str, object]:
    openapi: dict[str, object] = create_app().openapi()
    return openapi


def _operations(contract: Json) -> list[tuple[str, str, Json]]:
    paths = contract["paths"]
    assert isinstance(paths, dict)
    return [
        (method, path, item[method])
        for path, item in paths.items()
        for method in METHODS
        if method in item
    ]


def _schemas(contract: Json) -> dict[str, Json]:
    components = contract["components"]
    assert isinstance(components, dict)
    schemas: dict[str, Json] = components["schemas"]
    return schemas


def test_every_endpoint_and_schema_is_in_the_reference(contract: Json) -> None:
    page = render(contract)

    for method, path, _ in _operations(contract):
        assert f"### `{method.upper()} {path}`" in page
    for name in _schemas(contract):
        assert f"### `{name}` {{ #esquema-{name.lower()} }}" in page


def test_every_link_to_a_schema_has_its_section(contract: Json) -> None:
    page = render(contract)
    anchors = set(re.findall(r"\{ #([a-z0-9-]+) \}", page))

    links = set(re.findall(r"\]\(#([a-z0-9-]+)\)", page))

    assert links
    assert links <= anchors


def test_the_reference_is_in_spanish(contract: Json) -> None:
    page = render(contract)

    assert "Successful Response" not in page
    assert "| `200` |" in page


def test_every_endpoint_has_a_summary_and_a_description(contract: Json) -> None:
    for method, path, operation in _operations(contract):
        assert operation.get("summary"), f"{method} {path} sin summary"
        assert operation.get("description"), f"{method} {path} sin docstring"


def test_every_parameter_has_a_description(contract: Json) -> None:
    for method, path, operation in _operations(contract):
        parameters = operation.get("parameters", [])
        assert isinstance(parameters, list)
        for parameter in parameters:
            assert parameter.get("description"), f"{method} {path}: {parameter['name']}"


def test_every_field_has_a_description(contract: Json) -> None:
    missing = []
    for name, schema in _schemas(contract).items():
        properties = schema.get("properties", {})
        assert isinstance(properties, dict)
        if name not in FASTAPI_SCHEMAS:
            missing += [f"{name}.{f}" for f, d in properties.items() if not d.get("description")]
    assert missing == []


def test_types_are_described_in_spanish() -> None:
    contract: Json = {
        "info": {"version": "9.9.9"},
        "paths": {},
        "components": {
            "schemas": {
                "Thing": {
                    "properties": {
                        "when": {"anyOf": [{"type": "string", "format": "date"}, {"type": "null"}]},
                        "tags": {"type": "array", "items": {"$ref": "#/components/schemas/Kind"}},
                    },
                    "required": ["tags"],
                },
                "Kind": {"enum": ["a", "b"], "type": "string"},
            }
        },
    }

    page = render(contract)

    assert "| `when` | texto (fecha) o null | no |" in page
    assert "| `tags` | lista de [`Kind`](#esquema-kind) | sí |" in page
    assert "Valores: `a`, `b`." in page
    assert "**9.9.9**" in page
