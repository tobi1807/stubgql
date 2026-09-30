import re
from datetime import date, datetime

import pytest

from stubgql import Stubber

SCHEMA = """
type Event {
  createdAt: AWSDateTime
  updatedAt: AWSDateTime
  publishedOn: String
  deletedAt: AWSTimestamp
  startDate: String
  birthday: AWSDate
}

type Query {
  event(id: ID!): Event
}
"""


def parse_date_time(value):
    return datetime.fromisoformat(value)


@pytest.fixture(scope="module")
def events():
    stubber = Stubber(SCHEMA)
    return [stubber.resolve("Query", "event", args={"id": str(i)}) for i in range(30)]


def test_updated_at_is_never_before_created_at(events):
    for event in events:
        assert parse_date_time(event["updatedAt"]) >= parse_date_time(
            event["createdAt"]
        )


def test_infers_iso_timestamps_for_string_fields_named_like_moments(events):
    for event in events:
        published = parse_date_time(event["publishedOn"])
        assert published >= parse_date_time(event["createdAt"])


def test_infers_iso_dates_for_string_fields_named_like_dates(events):
    for event in events:
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", event["startDate"])


def test_orders_epoch_timestamps_after_created_at(events):
    for event in events:
        created = parse_date_time(event["createdAt"]).timestamp()
        assert event["deletedAt"] >= created


def test_infers_adult_birthdays(events):
    for event in events:
        assert (
            date(1945, 1, 1)
            <= date.fromisoformat(event["birthday"])
            <= date(2007, 12, 31)
        )


def test_timestamps_do_not_depend_on_which_fields_are_selected():
    stubber = Stubber(SCHEMA)
    both = stubber.resolve(
        "Query", "event", args={"id": "1"}, selection="{ createdAt updatedAt }"
    )
    alone = stubber.resolve(
        "Query", "event", args={"id": "1"}, selection="{ updatedAt }"
    )
    assert alone["updatedAt"] == both["updatedAt"]
