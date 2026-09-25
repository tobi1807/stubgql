"""Schema-aware stub data for GraphQL, with built-in AWS AppSync support."""

from importlib.metadata import version

from stubgql._errors import StubgqlError

__all__ = ["StubgqlError", "__version__"]

__version__ = version("stubgql")
