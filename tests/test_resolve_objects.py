import pytest

from stubgql import InvalidSelectionError, Stubber, UnknownFieldError

SCHEMA = """
enum Role { ADMIN READER }

type User {
  id: ID!
  name: String!
  age: Int
  role: Role!
  posts: [Post!]!
  bestFriend: User
}

type Post {
  id: ID!
  title: String!
  author: User!
}

type Query {
  getUser(id: ID!): User
  listPosts: [Post!]!
}
"""


@pytest.fixture
def stubber():
    return Stubber(SCHEMA)


def test_resolves_an_object_to_exactly_the_selected_fields(stubber):
    user = stubber.resolve("Query", "getUser", selection="{ id name role }")
    assert set(user) == {"id", "name", "role"}
    assert isinstance(user["name"], str)
    assert user["role"] in {"ADMIN", "READER"}


def test_resolves_nested_objects_to_their_selected_fields(stubber):
    user = stubber.resolve(
        "Query", "getUser", selection="{ name bestFriend { id name } }"
    )
    assert set(user["bestFriend"]) == {"id", "name"}


def test_resolves_a_list_of_objects_to_objects_with_the_selected_fields(stubber):
    posts = stubber.resolve("Query", "listPosts", selection="{ title author { name } }")
    assert posts
    assert all(set(post) == {"title", "author"} for post in posts)
    assert all(set(post["author"]) == {"name"} for post in posts)


def test_resolves_typename_to_the_object_type_name(stubber):
    user = stubber.resolve("Query", "getUser", selection="{ __typename name }")
    assert user["__typename"] == "User"


def test_a_fields_value_does_not_depend_on_the_other_selected_fields(stubber):
    alone = stubber.resolve("Query", "getUser", args={"id": "1"}, selection="{ name }")
    among_others = stubber.resolve(
        "Query", "getUser", args={"id": "1"}, selection="{ id age posts { id } name }"
    )
    assert alone["name"] == among_others["name"]


def test_rejects_a_selected_field_that_the_type_does_not_have(stubber):
    with pytest.raises(UnknownFieldError, match=r"Post\.body"):
        stubber.resolve("Query", "getUser", selection="{ posts { title body } }")


def test_rejects_a_selection_that_is_not_valid_graphql(stubber):
    with pytest.raises(InvalidSelectionError):
        stubber.resolve("Query", "getUser", selection="{ id name")


def test_rejects_a_selection_that_is_valid_graphql_but_not_a_selection_set(stubber):
    with pytest.raises(InvalidSelectionError):
        stubber.resolve("Query", "getUser", selection="type User { id: ID }")


LEAF_USER_FIELDS = {"id", "name", "age", "role"}


def test_resolves_all_fields_to_three_object_levels_without_a_selection(stubber):
    user = stubber.resolve("Query", "getUser", args={"id": "1"})
    assert set(user) == LEAF_USER_FIELDS | {"posts", "bestFriend"}
    post = user["posts"][0]
    assert set(post) == {"id", "title", "author"}
    assert set(post["author"]) == LEAF_USER_FIELDS


def test_stops_for_types_without_leaf_fields():
    chain = Stubber("type Chain { next: Chain } type Query { chain: Chain }")
    # No field of Chain can ever be selected, so its stub has no fields.
    assert chain.resolve("Query", "chain") == {}


def test_rejects_a_selected_object_field_without_subfields(stubber):
    with pytest.raises(InvalidSelectionError, match=r"User\.posts"):
        stubber.resolve("Query", "getUser", selection="{ name posts }")
