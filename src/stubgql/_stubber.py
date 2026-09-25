from stubgql._schema import SchemaSource, load_schema


class Stubber:
    """Produces stubs for the fields of one GraphQL schema.

    Args:
        schema: The schema as SDL, or a path to a `.graphql`, `.graphqls` or
            `.gql` file. AWS AppSync scalars and directives can be used
            without declaring them.
    """

    def __init__(self, schema: SchemaSource) -> None:
        self._schema = load_schema(schema)
