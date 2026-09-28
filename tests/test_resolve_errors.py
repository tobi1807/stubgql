import pytest

from stubgql import Stubber, UnknownFieldError

SCHEMA = """
enum Role { ADMIN READER }
type Query { title: String }
"""


def test_rejects_a_field_that_is_not_in_the_schema():
    with pytest.raises(UnknownFieldError, match=r"Query\.getUsr"):
        Stubber(SCHEMA).resolve("Query", "getUsr")


def test_rejects_a_type_that_is_not_in_the_schema():
    with pytest.raises(UnknownFieldError, match=r"Querry\.title"):
        Stubber(SCHEMA).resolve("Querry", "title")


def test_rejects_a_type_that_has_no_fields():
    with pytest.raises(UnknownFieldError, match=r"Role\.ADMIN"):
        Stubber(SCHEMA).resolve("Role", "ADMIN")
