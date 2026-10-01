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
