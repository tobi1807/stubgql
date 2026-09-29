import json
from pathlib import Path

from stubgql import Stubber

FIXTURES = Path(__file__).parent


def test_resolves_using_the_selection_from_a_real_appsync_event():
    event = json.loads((FIXTURES / "events" / "query_get_user.json").read_text())
    info = event["info"]
    stubber = Stubber(FIXTURES / "schemas" / "appsync_blog.graphql")

    user = stubber.resolve(
        info["parentTypeName"],
        info["fieldName"],
        args=event["arguments"],
        selection=info["selectionSetGraphQL"],
    )

    assert set(user) == {"id", "firstName", "email", "role", "posts"}
    assert all(set(post) == {"id", "title"} for post in user["posts"])
