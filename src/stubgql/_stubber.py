import threading
from collections.abc import Mapping
from types import MappingProxyType
from typing import Any

from faker import Faker
from graphql import (
    GraphQLEnumType,
    GraphQLField,
    GraphQLInterfaceType,
    GraphQLList,
    GraphQLObjectType,
    GraphQLOutputType,
    GraphQLScalarType,
    GraphQLUnionType,
    get_named_type,
    get_nullable_type,
    is_leaf_type,
)

from stubgql._appsync import AWS_SCALAR_GENERATORS, read_event, unwrap_selection
from stubgql._echo import echo_values, fits, foreign_key
from stubgql._errors import InvalidSelectionError, UnknownFieldError
from stubgql._inference import FieldContext, infer
from stubgql._scalars import SCALAR_GENERATORS
from stubgql._schema import SchemaSource, load_schema
from stubgql._seeding import derive_seed
from stubgql._selection import (
    FULL_SELECTION_DEPTH,
    CompositeType,
    Selection,
    fields_for,
    full_selection,
    parse_selection,
)

LIST_LENGTH = (2, 5)
NO_ECHO: Mapping[str, Any] = MappingProxyType({})


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
        source: Mapping[str, Any] | None = None,
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
            source: The parent object, for fields resolved under another
                object, such as a post when resolving `Post.author`.

        Returns:
            A value conforming to the field's type.

        Raises:
            UnknownFieldError: The type or a selected field isn't in the schema.
            InvalidSelectionError: The selection isn't a valid selection set.
        """
        parsed = parse_selection(selection) if selection else None
        return self._resolve(type_name, field_name, args, parsed, source)

    def handle_appsync(self, event: Mapping[str, Any] | list[Mapping[str, Any]]) -> Any:
        """Produce the response to an AWS AppSync direct resolver event.

        Args:
            event: The event AppSync sends a direct Lambda resolver, or a
                list of them when batching is enabled.

        Returns:
            The stub for the field the event asks about. For a batch, a list
            with one `{"data": stub, "errorMessage": None, "errorType": None}`
            item per event, in order, which is the shape AppSync requires.

        Raises:
            InvalidEventError: The event isn't an AppSync resolver event.
            UnknownFieldError: The event names a type or field that isn't in
                the schema.
        """
        if isinstance(event, list):
            return [
                {
                    "data": self.handle_appsync(single),
                    "errorMessage": None,
                    "errorType": None,
                }
                for single in event
            ]
        request = read_event(event)
        selection = None
        if request.selection:
            field = self._field(request.type_name, request.field_name)
            selection = unwrap_selection(
                parse_selection(request.selection),
                request.field_name,
                get_named_type(field.type),
            )
        return self._resolve(
            request.type_name,
            request.field_name,
            request.args,
            selection,
            request.source,
        )

    def _field(self, type_name: str, field_name: str) -> GraphQLField:
        parent = self._schema.get_type(type_name)
        fields = parent.fields if isinstance(parent, GraphQLObjectType) else {}
        field = fields.get(field_name)
        if field is None:
            raise UnknownFieldError(f"{type_name}.{field_name} is not in the schema")
        return field

    def _resolve(
        self,
        type_name: str,
        field_name: str,
        args: Mapping[str, Any] | None,
        selection: Selection | None,
        source: Mapping[str, Any] | None,
    ) -> Any:
        field = self._field(type_name, field_name)
        if selection is None:
            named = get_named_type(field.type)
            selection = (
                full_selection(named, FULL_SELECTION_DEPTH, self._schema)
                if isinstance(named, CompositeType)
                else Selection()
            )
        seed = derive_seed(type_name, field_name, args or {})
        if source is not None:
            # A parent's other fields depend on what its query selected, so
            # only its id identifies it when it has one.
            seed = derive_seed(seed, source.get("id", source))
        context = FieldContext(type_name, field_name, derive_seed(type_name))
        echo = echo_values(args or {})
        key = foreign_key(source, field_name) if source is not None else None
        if key is not None:
            echo.setdefault("id", key)  # an id argument wins
        return self._stub(field.type, seed, selection, context, echo)

    def _seeded_faker(self, seed: int) -> Faker:
        # Faker instances hold random state, so each thread gets its own.
        faker = getattr(self._local, "faker", None)
        if faker is None:
            faker = self._local.faker = Faker()
        faker.seed_instance(seed)
        return faker

    def _stub(
        self,
        type_: GraphQLOutputType,
        seed: int,
        selection: Selection,
        context: FieldContext,
        echo: Mapping[str, Any] = NO_ECHO,
    ) -> Any:
        # Every value has its own seed, derived from its parent's seed and its
        # position, so a value doesn't depend on what else is selected.
        nullable = get_nullable_type(type_)
        if isinstance(nullable, GraphQLList):
            length = self._seeded_faker(seed).random_int(*LIST_LENGTH)
            return [
                self._stub(
                    nullable.of_type, derive_seed(seed, index), selection, context
                )
                for index in range(length)
            ]
        if isinstance(nullable, GraphQLObjectType):
            return self._stub_object(nullable, seed, selection, echo)
        faker = self._seeded_faker(seed)
        if isinstance(nullable, GraphQLInterfaceType | GraphQLUnionType):
            # AppSync needs __typename to tell which concrete type it got.
            possible_types = self._schema.get_possible_types(nullable)
            concrete = faker.random_element(possible_types)
            return {
                "__typename": concrete.name,
                **self._stub_object(concrete, seed, selection, echo),
            }
        if isinstance(nullable, GraphQLEnumType):
            return faker.random_element(list(nullable.values))
        assert isinstance(nullable, GraphQLScalarType)
        generator = infer(context, nullable.name) or self._scalar_generators.get(
            nullable.name, self._scalar_generators["String"]
        )
        return generator(faker)

    def _stub_object(
        self,
        type_: GraphQLObjectType,
        seed: int,
        selection: Selection,
        echo: Mapping[str, Any] = NO_ECHO,
    ) -> dict[str, Any]:
        if (id_field := type_.fields.get("id")) is not None:
            # An entity: its id decides every other value, so the same entity
            # looks the same wherever it appears.
            entity_id = echo.get("id")
            if entity_id is None or not fits(entity_id, id_field.type):
                context = FieldContext(type_.name, "id", seed)
                entity_id = self._stub(
                    id_field.type, derive_seed(seed, "id"), Selection(), context
                )
            seed = derive_seed("entity", type_.name, entity_id)
            echo = {**echo, "id": entity_id}
        stub: dict[str, Any] = {}
        for name, subselection in fields_for(selection, type_, self._schema).items():
            if name == "__typename":
                stub[name] = type_.name
                continue
            field = type_.fields.get(name)
            if field is None:
                raise UnknownFieldError(f"{type_.name}.{name} is not in the schema")
            if subselection.is_empty() and not is_leaf_type(get_named_type(field.type)):
                raise InvalidSelectionError(
                    f"{type_.name}.{name} is an object; select its subfields"
                )
            if name in echo and fits(echo[name], field.type):
                stub[name] = echo[name]
                continue
            context = FieldContext(type_.name, name, seed)
            stub[name] = self._stub(
                field.type, derive_seed(seed, name), subselection, context
            )
        return stub
