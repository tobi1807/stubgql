from graphql import (
    FieldNode,
    GraphQLError,
    GraphQLObjectType,
    OperationDefinitionNode,
    SelectionSetNode,
    get_named_type,
    is_leaf_type,
    parse,
)

from stubgql._errors import InvalidSelectionError

# Field name -> the selection under that field ({} for leaf fields).
Selection = dict[str, "Selection"]


def parse_selection(text: str) -> Selection:
    """Parse a selection set such as AppSync's `selectionSetGraphQL`."""
    try:
        document = parse(text, no_location=True)
    except GraphQLError as error:
        raise InvalidSelectionError(f"Invalid selection: {error.message}") from error
    [operation, *rest] = document.definitions
    if rest or not isinstance(operation, OperationDefinitionNode):
        raise InvalidSelectionError(
            f"Invalid selection: expected one selection set such as "
            f"'{{ id name }}', got {text!r}"
        )
    return _to_selection(operation.selection_set)


def _to_selection(selection_set: SelectionSetNode | None) -> Selection:
    selection: Selection = {}
    if selection_set is None:
        return selection
    for node in selection_set.selections:
        if isinstance(node, FieldNode):
            selection[node.name.value] = _to_selection(node.selection_set)
    return selection


def full_selection(type_: GraphQLObjectType, depth: int) -> Selection:
    """Select every field, descending at most `depth` object levels."""
    selection: Selection = {}
    for name, field in type_.fields.items():
        named = get_named_type(field.type)
        if is_leaf_type(named):
            selection[name] = {}
        elif (
            isinstance(named, GraphQLObjectType)
            and depth > 1
            # An object field needs at least one subfield to be selectable.
            and (subselection := full_selection(named, depth - 1))
        ):
            selection[name] = subselection
    return selection
