from __future__ import annotations

from dataclasses import dataclass, field

from graphql import (
    FieldNode,
    FragmentSpreadNode,
    GraphQLError,
    GraphQLInterfaceType,
    GraphQLObjectType,
    GraphQLSchema,
    GraphQLUnionType,
    InlineFragmentNode,
    OperationDefinitionNode,
    SelectionSetNode,
    get_named_type,
    is_leaf_type,
    parse,
)

from stubgql._errors import InvalidSelectionError

# Object levels included when every field is selected: when the caller gives
# no selection, or uses a named fragment whose fields are unknown.
FULL_SELECTION_DEPTH = 3


@dataclass
class Selection:
    """What the caller asked for under one field."""

    # Field name -> what's selected under it. Aliases are dropped, because
    # AppSync reads resolver results by field name.
    fields: dict[str, Selection] = field(default_factory=dict)
    # Type condition of an inline fragment -> what it selects.
    fragments: dict[str, Selection] = field(default_factory=dict)
    # A named fragment was spread here. AppSync doesn't send fragment
    # definitions, so every field is included instead; AppSync drops the extras.
    has_named_fragment: bool = False

    def is_empty(self) -> bool:
        return not (self.fields or self.fragments or self.has_named_fragment)

    def merge(self, other: Selection) -> None:
        _merge_into(self.fields, other.fields)
        _merge_into(self.fragments, other.fragments)
        self.has_named_fragment |= other.has_named_fragment


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


def fields_for(
    selection: Selection, type_: GraphQLObjectType, schema: GraphQLSchema
) -> dict[str, Selection]:
    """The fields selected on a concrete type, including matching fragments."""
    fields = {name: _copy(sub) for name, sub in selection.fields.items()}
    if selection.has_named_fragment:
        _merge_into(fields, full_selection(type_, FULL_SELECTION_DEPTH, schema).fields)
    for condition, fragment in selection.fragments.items():
        if _applies_to(condition, type_, schema):
            _merge_into(fields, fields_for(fragment, type_, schema))
    return fields


CompositeType = GraphQLObjectType | GraphQLInterfaceType | GraphQLUnionType


def full_selection(
    type_: CompositeType, depth: int, schema: GraphQLSchema
) -> Selection:
    """Select every field, descending at most `depth` object levels."""
    selection = Selection()
    if not isinstance(type_, GraphQLObjectType):
        for possible_type in schema.get_possible_types(type_):
            selection.fragments[possible_type.name] = full_selection(
                possible_type, depth, schema
            )
        return selection
    for name, schema_field in type_.fields.items():
        named = get_named_type(schema_field.type)
        if is_leaf_type(named):
            selection.fields[name] = Selection()
        elif isinstance(named, CompositeType) and depth > 1:
            subselection = full_selection(named, depth - 1, schema)
            # A composite field needs at least one subfield to be selectable.
            if not subselection.is_empty():
                selection.fields[name] = subselection
    return selection


def _to_selection(selection_set: SelectionSetNode | None) -> Selection:
    selection = Selection()
    if selection_set is None:
        return selection
    for node in selection_set.selections:
        if isinstance(node, FieldNode):
            _merge_into(
                selection.fields, {node.name.value: _to_selection(node.selection_set)}
            )
        elif isinstance(node, InlineFragmentNode):
            inner = _to_selection(node.selection_set)
            if node.type_condition is None:
                selection.merge(inner)
            else:
                _merge_into(
                    selection.fragments, {node.type_condition.name.value: inner}
                )
        elif isinstance(node, FragmentSpreadNode):
            selection.has_named_fragment = True
    return selection


def _applies_to(
    condition: str, type_: GraphQLObjectType, schema: GraphQLSchema
) -> bool:
    if condition == type_.name:
        return True
    condition_type = schema.get_type(condition)
    return isinstance(
        condition_type, GraphQLInterfaceType | GraphQLUnionType
    ) and schema.is_sub_type(condition_type, type_)


def _merge_into(target: dict[str, Selection], source: dict[str, Selection]) -> None:
    for name, selection in source.items():
        if name in target:
            target[name].merge(selection)
        else:
            target[name] = _copy(selection)


def _copy(selection: Selection) -> Selection:
    copy = Selection()
    copy.merge(selection)
    return copy
