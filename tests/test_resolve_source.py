import pytest

from stubgql import Stubber

SCHEMA = """
type User {
  id: ID!
  name: String!
}

type Post {
  id: ID!
  title: String!
  author: User!
  editor: User
}

type Query {
  getUser(id: ID!): User
}
"""

SELECTION = "{ id name }"


@pytest.fixture
def stubber():
    return Stubber(SCHEMA)


def test_different_parents_get_different_nested_stubs(stubber):
    first = stubber.resolve("Post", "author", source={"id": "p1"}, selection=SELECTION)
    second = stubber.resolve("Post", "author", source={"id": "p2"}, selection=SELECTION)
    assert first != second


def test_only_the_parents_id_matters_when_it_has_one(stubber):
    lean = stubber.resolve("Post", "author", source={"id": "p1"}, selection=SELECTION)
    rich = stubber.resolve(
        "Post", "author", source={"id": "p1", "title": "Hi"}, selection=SELECTION
    )
    assert lean == rich


@pytest.mark.parametrize("key", ["authorId", "author_id"])
def test_a_foreign_key_in_the_parent_picks_the_entity(stubber, key):
    author = stubber.resolve(
        "Post", "author", source={"id": "p1", key: "u7"}, selection=SELECTION
    )
    user = stubber.resolve("Query", "getUser", args={"id": "u7"}, selection=SELECTION)
    assert author == user


def test_a_foreign_key_only_applies_to_its_own_field(stubber):
    editor = stubber.resolve(
        "Post", "editor", source={"id": "p1", "authorId": "u7"}, selection=SELECTION
    )
    assert editor["id"] != "u7"
