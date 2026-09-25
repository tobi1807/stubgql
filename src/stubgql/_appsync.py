from graphql import (
    DirectiveDefinitionNode,
    DirectiveNode,
    DocumentNode,
    NamedTypeNode,
    TypeDefinitionNode,
    Visitor,
    parse,
    visit,
)

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
