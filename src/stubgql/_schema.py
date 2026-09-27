import os
from pathlib import Path

from graphql import (
    GraphQLError,
    GraphQLSchema,
    build_ast_schema,
    parse,
    validate_schema,
)

from stubgql._appsync import with_appsync_prelude
from stubgql._errors import SchemaError

SCHEMA_FILE_SUFFIXES = (".graphql", ".graphqls", ".gql")

SchemaSource = str | bytes | os.PathLike[str]


def load_schema(source: SchemaSource) -> GraphQLSchema:
    try:
        document = parse(_read_sdl(source))
    except GraphQLError as error:
        raise SchemaError(f"Invalid schema: {error.message}") from error
    document = with_appsync_prelude(document)
    try:
        schema = build_ast_schema(document)
    except TypeError as error:  # graphql-core reports invalid SDL as TypeError
        raise SchemaError(f"Invalid schema: {error}") from error
    if errors := validate_schema(schema):
        details = "\n".join(error.message for error in errors)
        raise SchemaError(f"Invalid schema:\n{details}")
    return schema


def _read_sdl(source: SchemaSource) -> str:
    if isinstance(source, bytes):
        return _decode(source, "Schema bytes")
    if isinstance(source, str) and not _looks_like_path(source):
        return source
    path = Path(source)
    try:
        data = path.read_bytes()
    except OSError as error:
        raise SchemaError(f"Can't read schema file {path}: {error.strerror}") from error
    return _decode(data, f"Schema file {path}")


def _decode(data: bytes, description: str) -> str:
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise SchemaError(
            f"{description} isn't valid UTF-8 (byte {error.start}: {error.reason})"
        ) from error


def _looks_like_path(source: str) -> bool:
    # SDL always spans lines or contains braces; a schema path never does.
    return (
        "\n" not in source
        and "{" not in source
        and source.endswith(SCHEMA_FILE_SUFFIXES)
    )
