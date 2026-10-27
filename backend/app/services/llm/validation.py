"""Strict validation for the JSON-schema subset used by DBCAS prompts."""
import math

from .errors import LLMError


def validate_json_schema(value, schema: dict, path="response"):
    def invalid():
        raise LLMError(LLMError.INVALID_RESPONSE, f"The AI response has an invalid field at {path}")
    if "anyOf" in schema:
        for option in schema["anyOf"]:
            try:
                validate_json_schema(value, option, path)
                break
            except LLMError:
                continue
        else:
            invalid()
    kind = schema.get("type")
    checks = {
        "object": lambda v: isinstance(v, dict),
        "array": lambda v: isinstance(v, list),
        "string": lambda v: isinstance(v, str),
        "boolean": lambda v: isinstance(v, bool),
        "number": lambda v: type(v) is int or (type(v) is float and math.isfinite(v)),
        "integer": lambda v: type(v) is int,
        "null": lambda v: v is None,
    }
    if kind in checks and not checks[kind](value):
        invalid()
    if "enum" in schema and value not in schema["enum"]:
        invalid()
    if isinstance(value, dict):
        props = schema.get("properties", {})
        if any(key not in value for key in schema.get("required", [])):
            invalid()
        if schema.get("additionalProperties") is False and set(value) - set(props):
            invalid()
        for key, item in value.items():
            validate_json_schema(item, props.get(key, {}), path + "." + key)
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0) or len(value) > schema.get("maxItems", 10000):
            invalid()
        for item in value:
            validate_json_schema(item, schema.get("items", {}), path + "[]")
    if type(value) in (int, float):
        if (type(value) is float and not math.isfinite(value)) or value < schema.get("minimum", -math.inf) or value > schema.get("maximum", math.inf):
            invalid()
    if isinstance(value, str) and (len(value) < schema.get("minLength", 0) or len(value) > schema.get("maxLength", 262144)):
        invalid()
