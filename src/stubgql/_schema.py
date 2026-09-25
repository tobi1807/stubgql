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

SchemaSource = str | os.PathLike[str]


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
    if isinstance(source, str) and not source.endswith(SCHEMA_FILE_SUFFIXES):
        return source
    path = Path(source)
    try:
        return path.read_text(encoding="utf-8")
    except OSError as error:
        raise SchemaError(f"Can't read schema file {path}: {error.strerror}") from error
