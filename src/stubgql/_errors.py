class StubgqlError(Exception):
    """Base class for every error stubgql raises."""


class SchemaError(StubgqlError):
    """The schema couldn't be read or isn't a valid GraphQL schema."""
