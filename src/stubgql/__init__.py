"""Schema-aware stub data for GraphQL, with built-in AWS AppSync support."""

from importlib.metadata import version

from stubgql._errors import SchemaError, StubgqlError
from stubgql._stubber import Stubber

__all__ = ["SchemaError", "Stubber", "StubgqlError", "__version__"]

__version__ = version("stubgql")
