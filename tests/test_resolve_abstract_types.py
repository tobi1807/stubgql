import pytest

from stubgql import Stubber

SCHEMA = """
interface Node { id: ID! }

type User implements Node {
  id: ID!
  name: String!
}

type Post implements Node {
  id: ID!
  title: String!
}

union SearchResult = User | Post

type Query {
  search(term: String!): [SearchResult!]!
  node(id: ID!): Node
}
"""

FIELDS_BY_TYPE = {"User": {"__typename", "name"}, "Post": {"__typename", "title"}}


@pytest.fixture
def stubber():
    return Stubber(SCHEMA)


def test_resolves_a_union_to_members_with_their_fragment_fields(stubber):
    results = stubber.resolve(
        "Query",
        "search",
        args={"term": "a"},
        selection="{ __typename ... on User { name } ... on Post { title } }",
    )
    assert results
    for result in results:
        assert set(result) == FIELDS_BY_TYPE[result["__typename"]]


def test_includes_typename_for_abstract_types_even_when_not_selected(stubber):
    results = stubber.resolve(
        "Query", "search", args={"term": "a"}, selection="{ ... on User { name } }"
    )
    assert all("__typename" in result for result in results)


def test_resolves_an_interface_to_its_fields_plus_matching_fragment_fields(stubber):
    seen = set()
    for node_id in map(str, range(20)):
        node = stubber.resolve(
            "Query",
            "node",
            args={"id": node_id},
            selection="{ id ... on User { name } }",
        )
        expected = {"__typename", "id"} | (
            {"name"} if node["__typename"] == "User" else set()
        )
        assert set(node) == expected
        seen.add(node["__typename"])
    assert seen == {"User", "Post"}


def test_applies_a_fragment_on_an_interface_to_union_members_implementing_it(stubber):
    results = stubber.resolve(
        "Query", "search", args={"term": "a"}, selection="{ ... on Node { id } }"
    )
    assert all("id" in result for result in results)


ALL_FIELDS_BY_TYPE = {
    "User": {"__typename", "id", "name"},
    "Post": {"__typename", "id", "title"},
}


def test_resolves_abstract_types_to_all_fields_without_a_selection(stubber):
    for result in stubber.resolve("Query", "search", args={"term": "a"}):
        assert set(result) == ALL_FIELDS_BY_TYPE[result["__typename"]]


def test_includes_all_fields_for_a_named_fragment_whose_definition_is_missing(
    stubber,
):
    # AppSync's selectionSetGraphQL keeps "...UserFields" but not its definition.
    node = stubber.resolve(
        "Query", "node", args={"id": "1"}, selection="{ __typename ...NodeFields }"
    )
    assert set(node) == ALL_FIELDS_BY_TYPE[node["__typename"]]
