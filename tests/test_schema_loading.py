from pathlib import Path

import pytest

from stubgql import SchemaError, Stubber

SCHEMAS = Path(__file__).parent / "schemas"


def test_loads_a_plain_graphql_schema_from_sdl():
    Stubber("type Query { hello: String }")


def test_loads_a_schema_using_undeclared_aws_scalars():
    Stubber(
        """
        type Query {
          date: AWSDate
          time: AWSTime
          dateTime: AWSDateTime
          timestamp: AWSTimestamp
          email: AWSEmail
          json: AWSJSON
          url: AWSURL
          phone: AWSPhone
          ip: AWSIPAddress
        }
        """
    )


def test_loads_a_schema_using_undeclared_aws_directives():
    Stubber(
        """
        type Post @aws_iam @aws_api_key @aws_oidc @aws_lambda
          @aws_cognito_user_pools(cognito_groups: ["admins"]) {
          id: ID!
          secret: String @aws_auth(cognito_groups: ["admins"])
        }
        type Query { getPost: Post }
        type Mutation { createPost: Post }
        type Subscription {
          onCreatePost: Post @aws_subscribe(mutations: ["createPost"])
        }
        """
    )


def test_keeps_aws_scalars_and_directives_the_schema_declares_itself():
    Stubber(
        """
        scalar AWSDateTime
        directive @aws_iam on OBJECT | FIELD_DEFINITION
        type Query { now: AWSDateTime @aws_iam }
        """
    )


def test_loads_a_schema_from_a_path_string():
    Stubber(str(SCHEMAS / "appsync_blog.graphql"))


def test_loads_a_schema_from_a_path_object():
    Stubber(SCHEMAS / "appsync_blog.graphql")


def test_rejects_sdl_with_a_syntax_error():
    with pytest.raises(SchemaError):
        Stubber("type Query { hello: String")


def test_rejects_a_schema_referencing_an_undefined_type():
    with pytest.raises(SchemaError, match="Missing"):
        Stubber("type Query { thing: Missing }")


def test_rejects_a_schema_using_an_undeclared_custom_directive():
    with pytest.raises(SchemaError, match="custom"):
        Stubber("type Query { hello: String @custom }")


def test_rejects_an_unknown_directive_even_with_an_aws_prefix():
    with pytest.raises(SchemaError, match="aws_made_up"):
        Stubber("type Query { hello: String @aws_made_up }")


def test_rejects_a_type_that_does_not_satisfy_its_interface():
    with pytest.raises(SchemaError, match=r"Node\.id"):
        Stubber(
            """
            interface Node { id: ID! }
            type User implements Node { name: String }
            type Query { user: User }
            """
        )


def test_rejects_a_schema_path_that_does_not_exist():
    with pytest.raises(SchemaError, match=r"missing\.graphql"):
        Stubber("missing.graphql")


def test_loads_sdl_whose_last_line_mentions_a_schema_file():
    Stubber("type Query { hello: String }\n# generated from schema.graphql")


def test_loads_single_line_sdl_ending_with_a_schema_file_name():
    Stubber("type Query { hello: String } # see schema.graphql")


def test_loads_a_schema_from_utf8_bytes():
    Stubber("type Query { greeting: String } # héllo".encode())


def test_rejects_bytes_that_are_not_utf8():
    with pytest.raises(SchemaError, match="UTF-8"):
        Stubber(b"type Query { greeting: String } # \xff")


def test_rejects_a_schema_file_that_is_not_utf8(tmp_path):
    schema_file = tmp_path / "schema.graphql"
    schema_file.write_bytes(b"type Query { greeting: String } # \xff")
    with pytest.raises(SchemaError, match="UTF-8"):
        Stubber(schema_file)
