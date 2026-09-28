import pytest

from stubgql import Stubber

SCHEMA = """
enum Role { ADMIN EDITOR READER }
scalar Money

type Query {
  text: String
  count: Int
  ratio: Float
  flag: Boolean
  key: ID
  role: Role
  price: Money
  name: String!
  tags: [String!]!
}
"""

INT_MIN, INT_MAX = -(2**31), 2**31 - 1


@pytest.fixture
def stubber():
    return Stubber(SCHEMA)


def test_resolves_a_string_field_to_a_string(stubber):
    assert isinstance(stubber.resolve("Query", "text"), str)


def test_resolves_an_int_field_to_a_32_bit_integer(stubber):
    value = stubber.resolve("Query", "count")
    assert type(value) is int
    assert INT_MIN <= value <= INT_MAX


def test_resolves_a_float_field_to_a_float(stubber):
    assert type(stubber.resolve("Query", "ratio")) is float


def test_resolves_a_boolean_field_to_a_boolean(stubber):
    assert type(stubber.resolve("Query", "flag")) is bool


def test_resolves_an_id_field_to_a_non_empty_string(stubber):
    value = stubber.resolve("Query", "key")
    assert isinstance(value, str)
    assert value


def test_resolves_an_enum_field_to_one_of_its_values(stubber):
    assert stubber.resolve("Query", "role") in {"ADMIN", "EDITOR", "READER"}


def test_resolves_a_custom_scalar_field_to_a_string(stubber):
    assert isinstance(stubber.resolve("Query", "price"), str)


def test_resolves_a_non_null_field_to_a_value(stubber):
    assert isinstance(stubber.resolve("Query", "name"), str)


def test_resolves_a_list_field_to_a_non_empty_list_of_items(stubber):
    value = stubber.resolve("Query", "tags")
    assert isinstance(value, list)
    assert value
    assert all(isinstance(item, str) for item in value)
