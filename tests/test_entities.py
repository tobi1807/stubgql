import pytest

from stubgql import Stubber

SCHEMA = """
enum Status { DRAFT PUBLISHED }

type User {
  id: ID!
  name: String!
  email: String!
  age: Int
  posts: [Post!]!
}

type Post {
  id: ID!
  title: String!
  status: Status!
  tags: [String!]
  author: User!
}

input CreatePostInput {
  title: String!
  status: Status
  tags: [String!]
}

input UpdatePostInput {
  id: ID!
  title: String
}

type Query {
  getUser(id: ID!): User
  getUserByEmail(email: String!): User
  getUserByAge(age: String!): User
  listUsers: [User!]!
  getPost(id: ID!): Post
  listPosts: [Post!]!
}

type Mutation {
  createPost(input: CreatePostInput!): Post!
  updatePost(input: UpdatePostInput!): Post!
}
"""


@pytest.fixture
def stubber():
    return Stubber(SCHEMA)


def test_returns_the_requested_id(stubber):
    user = stubber.resolve("Query", "getUser", args={"id": "u1"}, selection="{ id }")
    assert user["id"] == "u1"


def test_an_entity_looks_the_same_wherever_it_appears(stubber):
    selection = "{ id name email age }"
    listed = stubber.resolve("Query", "listUsers", selection=selection)[0]
    fetched = stubber.resolve(
        "Query", "getUser", args={"id": listed["id"]}, selection=selection
    )
    assert fetched == listed


def test_a_nested_entity_looks_the_same_as_when_fetched_directly(stubber):
    post = stubber.resolve("Query", "listPosts", selection="{ author { id name } }")[0]
    author = post["author"]
    fetched = stubber.resolve(
        "Query", "getUser", args={"id": author["id"]}, selection="{ id name }"
    )
    assert fetched == author


def test_a_mutation_returns_the_values_from_its_input(stubber):
    post = stubber.resolve(
        "Mutation",
        "createPost",
        args={"input": {"title": "Hello", "status": "PUBLISHED", "tags": ["a", "b"]}},
        selection="{ id title status tags }",
    )
    assert post["title"] == "Hello"
    assert post["status"] == "PUBLISHED"
    assert post["tags"] == ["a", "b"]
    assert post["id"]


def test_an_update_returns_the_entity_with_the_input_applied(stubber):
    before = stubber.resolve(
        "Query", "getPost", args={"id": "p1"}, selection="{ id title status }"
    )
    after = stubber.resolve(
        "Mutation",
        "updatePost",
        args={"input": {"id": "p1", "title": "New title"}},
        selection="{ id title status }",
    )
    assert after == {**before, "title": "New title"}


def test_echoes_a_plain_argument_that_matches_a_field(stubber):
    user = stubber.resolve(
        "Query",
        "getUserByEmail",
        args={"email": "ada@example.com"},
        selection="{ email }",
    )
    assert user["email"] == "ada@example.com"


def test_does_not_echo_an_argument_whose_type_does_not_fit_the_field(stubber):
    user = stubber.resolve(
        "Query", "getUserByAge", args={"age": "thirty"}, selection="{ age }"
    )
    assert type(user["age"]) is int


def test_echoes_arguments_into_interface_results():
    stubber = Stubber(
        """
        interface Node { id: ID! }
        type User implements Node { id: ID! name: String }
        type Query { node(id: ID!): Node }
        """
    )
    node = stubber.resolve("Query", "node", args={"id": "n1"}, selection="{ id }")
    assert node["id"] == "n1"
