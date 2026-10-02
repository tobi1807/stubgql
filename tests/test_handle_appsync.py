import json
from pathlib import Path

import pytest

from stubgql import InvalidEventError, Stubber

FIXTURES = Path(__file__).parent


def load_event(name):
    return json.loads((FIXTURES / "events" / name).read_text())


@pytest.fixture(scope="module")
def stubber():
    return Stubber(FIXTURES / "schemas" / "appsync_blog.graphql")


def test_handles_a_single_event(stubber):
    user = stubber.handle_appsync(load_event("query_get_user.json"))
    assert user["id"] == "user-1"
    assert set(user) == {"id", "firstName", "email", "role", "posts"}
    assert all(set(post) == {"id", "title"} for post in user["posts"])


def test_handles_a_batch_event_with_one_result_per_event_in_order(stubber):
    events = load_event("batch_post_author.json")
    authors = stubber.handle_appsync(events)
    assert isinstance(authors, list)
    assert authors == [stubber.handle_appsync(event) for event in events]
    assert authors[0] != authors[1]


def test_unwraps_a_selection_that_includes_the_field_itself(stubber):
    # The AppSync docs show selectionSetGraphQL wrapped in the resolved field.
    event = load_event("query_get_user.json")
    event["info"]["selectionSetGraphQL"] = (
        "{\n  getUser(id: $id) {\n    id\n    firstName\n  }\n}"
    )
    assert set(stubber.handle_appsync(event)) == {"id", "firstName"}


@pytest.mark.parametrize(
    ("event", "missing"),
    [
        ({"arguments": {}}, "info"),
        ({"info": {"parentTypeName": "Query"}}, "info.fieldName"),
        ({"info": {"fieldName": "getUser"}}, "info.parentTypeName"),
    ],
)
def test_rejects_an_event_missing_what_identifies_the_field(stubber, event, missing):
    with pytest.raises(InvalidEventError, match=rf"missing {missing}\b"):
        stubber.handle_appsync(event)


@pytest.mark.parametrize("event", ["not an event", 42, None, [{"info": "nope"}]])
def test_rejects_something_that_is_not_an_event(stubber, event):
    with pytest.raises(InvalidEventError):
        stubber.handle_appsync(event)


def test_handles_a_scalar_field_whose_selection_is_empty(stubber):
    event = load_event("batch_post_author.json")[0]
    event["info"] |= {
        "fieldName": "title",
        "selectionSetList": [],
        "selectionSetGraphQL": "",
    }
    assert isinstance(stubber.handle_appsync(event), str)
