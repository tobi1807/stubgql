"""Schema-aware stub data for GraphQL, with built-in AWS AppSync support."""

from importlib.metadata import version

from stubgql._errors import (
    InvalidSelectionError,
    SchemaError,
    StubgqlError,
    UnknownFieldError,
)
from stubgql._stubber import Stubber

__all__ = [
    "InvalidSelectionError",
    "SchemaError",
    "Stubber",
    "StubgqlError",
    "UnknownFieldError",
    "__version__",
]

__version__ = version("stubgql")
