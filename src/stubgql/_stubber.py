from collections.abc import Mapping
from typing import Any

from faker import Faker
from graphql import (
    GraphQLEnumType,
    GraphQLList,
    GraphQLObjectType,
    GraphQLOutputType,
    GraphQLScalarType,
    get_nullable_type,
)

from stubgql._appsync import AWS_SCALAR_GENERATORS
from stubgql._errors import UnknownFieldError
from stubgql._scalars import SCALAR_GENERATORS
from stubgql._schema import SchemaSource, load_schema
from stubgql._seeding import derive_seed

LIST_LENGTH = (2, 5)


class Stubber:
    """Produces stubs for the fields of one GraphQL schema.

    Args:
        schema: The schema as SDL (`str` or UTF-8 `bytes`), or a path to a
            `.graphql`, `.graphqls` or `.gql` file. AWS AppSync scalars and
            directives can be used without declaring them.
    """

    def __init__(self, schema: SchemaSource) -> None:
        self._schema = load_schema(schema)
        self._faker = Faker()
        self._scalar_generators = SCALAR_GENERATORS | AWS_SCALAR_GENERATORS

    def resolve(
        self,
        type_name: str,
        field_name: str,
        *,
        args: Mapping[str, Any] | None = None,
    ) -> Any:
        """Produce a stub for one field of one type.

        Args:
            type_name: The type that owns the field, such as `"Query"`.
            field_name: The field to stub, such as `"getUser"`.
            args: The field's arguments. The same arguments always produce
                the same stub.

        Returns:
            A value conforming to the field's type.

        Raises:
            UnknownFieldError: The type or field isn't in the schema.
        """
        parent = self._schema.get_type(type_name)
        fields = parent.fields if isinstance(parent, GraphQLObjectType) else {}
        field = fields.get(field_name)
        if field is None:
            raise UnknownFieldError(f"{type_name}.{field_name} is not in the schema")
        self._faker.seed_instance(derive_seed(type_name, field_name, args or {}))
        return self._stub(field.type)

    def _stub(self, type_: GraphQLOutputType) -> Any:
        nullable = get_nullable_type(type_)
        if isinstance(nullable, GraphQLList):
            length = self._faker.random_int(*LIST_LENGTH)
            return [self._stub(nullable.of_type) for _ in range(length)]
        if isinstance(nullable, GraphQLEnumType):
            return self._faker.random_element(list(nullable.values))
        if not isinstance(nullable, GraphQLScalarType):
            raise NotImplementedError("object, interface and union stubs")
        generator = self._scalar_generators.get(
            nullable.name, self._scalar_generators["String"]
        )
        return generator(self._faker)
