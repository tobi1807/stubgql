from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from graphql import (
    DirectiveDefinitionNode,
    DirectiveNode,
    DocumentNode,
    GraphQLNamedType,
    NamedTypeNode,
    TypeDefinitionNode,
    Visitor,
    parse,
    visit,
)

from stubgql._errors import InvalidEventError
from stubgql._scalars import (
    ScalarGenerator,
    fictional_phone,
    iso_date_time,
    iso_time,
    json_object,
    moment,
)
from stubgql._selection import Selection

AWS_SCALARS = frozenset(
    {
        "AWSDate",
        "AWSTime",
        "AWSDateTime",
        "AWSTimestamp",
        "AWSEmail",
        "AWSJSON",
        "AWSURL",
        "AWSPhone",
        "AWSIPAddress",
    }
)

AWS_DIRECTIVES = {
    "aws_api_key": "directive @aws_api_key on OBJECT | FIELD_DEFINITION",
    "aws_iam": "directive @aws_iam on OBJECT | FIELD_DEFINITION",
    "aws_oidc": "directive @aws_oidc on OBJECT | FIELD_DEFINITION",
    "aws_lambda": "directive @aws_lambda on OBJECT | FIELD_DEFINITION",
    "aws_cognito_user_pools": (
        "directive @aws_cognito_user_pools(cognito_groups: [String])"
        " on OBJECT | FIELD_DEFINITION"
    ),
    "aws_auth": "directive @aws_auth(cognito_groups: [String]) on FIELD_DEFINITION",
    "aws_subscribe": (
        "directive @aws_subscribe(mutations: [String]) on FIELD_DEFINITION"
    ),
}


class _ReferenceCollector(Visitor):
    def __init__(self) -> None:
        super().__init__()
        self.types: set[str] = set()
        self.directives: set[str] = set()

    def enter_named_type(self, node: NamedTypeNode, *_: object) -> None:
        self.types.add(node.name.value)

    def enter_directive(self, node: DirectiveNode, *_: object) -> None:
        self.directives.add(node.name.value)


def with_appsync_prelude(document: DocumentNode) -> DocumentNode:
    """Declare the AWS scalars and directives the document uses but doesn't declare."""
    references = _ReferenceCollector()
    visit(document, references)
    declared_types = {
        definition.name.value
        for definition in document.definitions
        if isinstance(definition, TypeDefinitionNode)
    }
    declared_directives = {
        definition.name.value
        for definition in document.definitions
        if isinstance(definition, DirectiveDefinitionNode)
    }
    missing_scalars = (references.types & AWS_SCALARS) - declared_types
    used_directives = references.directives & AWS_DIRECTIVES.keys()
    missing_directives = used_directives - declared_directives
    declarations = [f"scalar {name}" for name in sorted(missing_scalars)] + [
        AWS_DIRECTIVES[name] for name in sorted(missing_directives)
    ]
    if not declarations:
        return document
    prelude = parse("\n".join(declarations))
    return DocumentNode(definitions=(*document.definitions, *prelude.definitions))


AWS_SCALAR_GENERATORS: dict[str, ScalarGenerator] = {
    "AWSDate": lambda faker: moment(faker.random).date().isoformat(),
    "AWSTime": lambda faker: iso_time(moment(faker.random)),
    "AWSDateTime": lambda faker: iso_date_time(moment(faker.random)),
    "AWSTimestamp": lambda faker: int(moment(faker.random).timestamp()),
    "AWSEmail": lambda faker: faker.email(),
    "AWSJSON": json_object,
    "AWSURL": lambda faker: faker.url(),
    "AWSPhone": fictional_phone,
    "AWSIPAddress": lambda faker: faker.ipv4(),
}


def unwrap_selection(
    selection: Selection, field_name: str, return_type: GraphQLNamedType
) -> Selection:
    """Strip the resolved field when selectionSetGraphQL is wrapped in it.

    The AppSync docs show `{ getPost(id: $id) { title } }` for `getPost`, where
    the selection under the field would be `{ title }`.
    """
    own_fields = getattr(return_type, "fields", {})
    wrapped = (
        list(selection.fields) == [field_name]
        and not selection.fragments
        and not selection.has_named_fragment
        and field_name not in own_fields
    )
    return selection.fields[field_name] if wrapped else selection


@dataclass(frozen=True)
class FieldRequest:
    """What an AppSync event asks for."""

    type_name: str
    field_name: str
    args: Mapping[str, Any]
    selection: str | None
    source: Mapping[str, Any] | None


def read_event(event: object) -> FieldRequest:
    """Read the parts of an AppSync direct resolver event that stubgql uses."""
    if not isinstance(event, Mapping):
        raise InvalidEventError(
            f"Expected an AppSync event (a dict), got {type(event).__name__}"
        )
    info = event.get("info")
    if not isinstance(info, Mapping):
        raise InvalidEventError("AppSync event is missing info")
    for key in ("parentTypeName", "fieldName"):
        if not isinstance(info.get(key), str):
            raise InvalidEventError(f"AppSync event is missing info.{key}")
    source = event.get("source")
    return FieldRequest(
        type_name=info["parentTypeName"],
        field_name=info["fieldName"],
        args=event.get("arguments") or {},
        selection=info.get("selectionSetGraphQL") or None,
        source=source if isinstance(source, Mapping) else None,
    )
