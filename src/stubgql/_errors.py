class StubgqlError(Exception):
    """Base class for every error stubgql raises."""


class SchemaError(StubgqlError):
    """The schema couldn't be read or isn't a valid GraphQL schema."""


class UnknownFieldError(StubgqlError):
    """The requested type or field isn't in the schema."""


class InvalidSelectionError(StubgqlError):
    """The selection isn't a valid GraphQL selection set."""


class InvalidEventError(StubgqlError):
    """The event isn't an AWS AppSync resolver event."""
