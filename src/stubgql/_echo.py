from collections.abc import Mapping
from typing import Any

from graphql import (
    GraphQLEnumType,
    GraphQLList,
    GraphQLNonNull,
    GraphQLOutputType,
    GraphQLScalarType,
    get_nullable_type,
)

from stubgql._inference import scalar_kind


def echo_values(args: Mapping[str, Any]) -> dict[str, Any]:
    """Argument values that should reappear in the returned object.

    Fields of input objects (such as `input: {title: "Hi"}`) are included,
    and plain arguments (such as `id: "1"`) take precedence over them.
    """
    values: dict[str, Any] = {}
    for value in args.values():
        if isinstance(value, Mapping):
            values.update(value)
    for name, value in args.items():
        if not isinstance(value, Mapping):
            values[name] = value
    return values


def foreign_key(source: Mapping[str, Any], field_name: str) -> Any:
    """The id a parent stores for a field, such as `authorId` for `author`."""
    for key in (f"{field_name}Id", f"{field_name}_id"):
        if key in source:
            return source[key]
    return None


def fits(value: Any, type_: GraphQLOutputType) -> bool:
    """Whether an argument value is a valid result for a field of this type."""
    if value is None:
        return not isinstance(type_, GraphQLNonNull)
    nullable = get_nullable_type(type_)
    if isinstance(nullable, GraphQLList):
        return isinstance(value, list) and all(
            fits(item, nullable.of_type) for item in value
        )
    if isinstance(nullable, GraphQLEnumType):
        return value in nullable.values
    if isinstance(nullable, GraphQLScalarType):
        return _fits_scalar(value, nullable.name)
    return False  # Objects are generated, never echoed.


def _fits_scalar(value: Any, scalar_name: str) -> bool:
    kind = scalar_kind(scalar_name)
    if scalar_name == "AWSJSON" or kind == "json":
        return True  # AppSync hands JSON arguments over already parsed.
    if kind == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if isinstance(value, bool):
        return scalar_name == "Boolean"
    if scalar_name in {"Int", "AWSTimestamp"}:
        return isinstance(value, int)
    if scalar_name == "Float":
        return isinstance(value, int | float)
    if scalar_name == "ID":
        return isinstance(value, str | int)
    if scalar_name == "Boolean":
        return False
    return isinstance(value, str)
