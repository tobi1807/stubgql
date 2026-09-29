import threading
from collections.abc import Mapping
from typing import Any

from faker import Faker
from graphql import (
    GraphQLEnumType,
    GraphQLList,
    GraphQLObjectType,
    GraphQLOutputType,
    GraphQLScalarType,
    get_named_type,
    get_nullable_type,
    is_leaf_type,
)

from stubgql._appsync import AWS_SCALAR_GENERATORS
from stubgql._errors import InvalidSelectionError, UnknownFieldError
from stubgql._scalars import SCALAR_GENERATORS
from stubgql._schema import SchemaSource, load_schema
from stubgql._seeding import derive_seed
from stubgql._selection import Selection, full_selection, parse_selection

LIST_LENGTH = (2, 5)
# Object levels included when the caller gives no selection.
FULL_SELECTION_DEPTH = 3


class Stubber:
    """Produces stubs for the fields of one GraphQL schema.

    Args:
        schema: The schema as SDL (`str` or UTF-8 `bytes`), or a path to a
            `.graphql`, `.graphqls` or `.gql` file. AWS AppSync scalars and
            directives can be used without declaring them.
    """

    def __init__(self, schema: SchemaSource) -> None:
        self._schema = load_schema(schema)
        self._local = threading.local()
        self._scalar_generators = SCALAR_GENERATORS | AWS_SCALAR_GENERATORS

    def resolve(
        self,
        type_name: str,
        field_name: str,
        *,
        args: Mapping[str, Any] | None = None,
        selection: str | None = None,
    ) -> Any:
        """Produce a stub for one field of one type.

        Args:
            type_name: The type that owns the field, such as `"Query"`.
            field_name: The field to stub, such as `"getUser"`.
            args: The field's arguments. The same arguments always produce
                the same stub.
            selection: The fields to include when the field's type is an
                object, as a GraphQL selection set such as
                `"{ id name posts { title } }"`. Without one, every field is
                included, down to three levels of nested objects.

        Returns:
            A value conforming to the field's type.

        Raises:
            UnknownFieldError: The type or a selected field isn't in the schema.
            InvalidSelectionError: The selection isn't a valid selection set.
        """
        parent = self._schema.get_type(type_name)
        fields = parent.fields if isinstance(parent, GraphQLObjectType) else {}
        field = fields.get(field_name)
        if field is None:
            raise UnknownFieldError(f"{type_name}.{field_name} is not in the schema")
        if selection:
            parsed = parse_selection(selection)
        else:
            named = get_named_type(field.type)
            parsed = (
                full_selection(named, FULL_SELECTION_DEPTH)
                if isinstance(named, GraphQLObjectType)
                else {}
            )
        seed = derive_seed(type_name, field_name, args or {})
        return self._stub(field.type, seed, parsed)

    def _seeded_faker(self, seed: int) -> Faker:
        # Faker instances hold random state, so each thread gets its own.
        faker = getattr(self._local, "faker", None)
        if faker is None:
            faker = self._local.faker = Faker()
        faker.seed_instance(seed)
        return faker

    def _stub(self, type_: GraphQLOutputType, seed: int, selection: Selection) -> Any:
        # Every value has its own seed, derived from its parent's seed and its
        # position, so a value doesn't depend on what else is selected.
        nullable = get_nullable_type(type_)
        if isinstance(nullable, GraphQLList):
            length = self._seeded_faker(seed).random_int(*LIST_LENGTH)
            return [
                self._stub(nullable.of_type, derive_seed(seed, index), selection)
                for index in range(length)
            ]
        if isinstance(nullable, GraphQLObjectType):
            return self._stub_object(nullable, seed, selection)
        faker = self._seeded_faker(seed)
        if isinstance(nullable, GraphQLEnumType):
            return faker.random_element(list(nullable.values))
        if not isinstance(nullable, GraphQLScalarType):
            raise NotImplementedError("interface and union stubs")
        generator = self._scalar_generators.get(
            nullable.name, self._scalar_generators["String"]
        )
        return generator(faker)

    def _stub_object(
        self, type_: GraphQLObjectType, seed: int, selection: Selection
    ) -> dict[str, Any]:
        stub: dict[str, Any] = {}
        for name, subselection in selection.items():
            if name == "__typename":
                stub[name] = type_.name
                continue
            field = type_.fields.get(name)
            if field is None:
                raise UnknownFieldError(f"{type_.name}.{name} is not in the schema")
            if not subselection and not is_leaf_type(get_named_type(field.type)):
                raise InvalidSelectionError(
                    f"{type_.name}.{name} is an object; select its subfields"
                )
            stub[name] = self._stub(field.type, derive_seed(seed, name), subselection)
        return stub
