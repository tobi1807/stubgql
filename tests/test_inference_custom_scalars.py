import json
import re
import uuid
from datetime import datetime

import pytest

from stubgql import Stubber

SAMPLES = range(20)


def stubs_of(scalar_name):
    """Stubs of a field typed with a custom scalar, for several arguments."""
    stubber = Stubber(
        f"scalar {scalar_name}\ntype Query {{ value(n: Int): {scalar_name} }}"
    )
    return [stubber.resolve("Query", "value", args={"n": n}) for n in SAMPLES]


@pytest.mark.parametrize("scalar_name", ["UUID", "GUID", "Uuid", "guid"])
def test_infers_uuids_for_uuid_scalars(scalar_name):
    for value in stubs_of(scalar_name):
        assert isinstance(value, str)
        assert str(uuid.UUID(value)) == value


@pytest.mark.parametrize(
    "scalar_name",
    ["DateTime", "DateTimeISO", "Instant", "Timestamp", "DATETIME", "LocalDateTime"],
)
def test_infers_iso_date_times_for_date_time_scalars(scalar_name):
    for value in stubs_of(scalar_name):
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z", value)
        datetime.fromisoformat(value)


@pytest.mark.parametrize("scalar_name", ["Date", "date", "LocalDate"])
def test_infers_iso_dates_for_date_scalars(scalar_name):
    for value in stubs_of(scalar_name):
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", value)
        datetime.strptime(value, "%Y-%m-%d")


@pytest.mark.parametrize("scalar_name", ["Time", "LocalTime"])
def test_infers_times_of_day_for_time_scalars(scalar_name):
    for value in stubs_of(scalar_name):
        assert re.fullmatch(r"\d{2}:\d{2}:\d{2}\.\d{3}", value)
        datetime.strptime(value, "%H:%M:%S.%f")


@pytest.mark.parametrize("scalar_name", ["JSON", "JSONObject", "Json"])
def test_infers_json_objects_for_json_scalars(scalar_name):
    for value in stubs_of(scalar_name):
        assert isinstance(value, dict)
        assert value
        assert json.loads(json.dumps(value)) == value


@pytest.mark.parametrize("scalar_name", ["URL", "URI", "Url"])
def test_infers_https_urls_for_url_scalars(scalar_name):
    for value in stubs_of(scalar_name):
        assert re.fullmatch(r"https://[\w.-]+(/\S*)?", value)


@pytest.mark.parametrize("scalar_name", ["Email", "EmailAddress", "EMAIL"])
def test_infers_email_addresses_for_email_scalars(scalar_name):
    for value in stubs_of(scalar_name):
        assert re.fullmatch(r"[\w.+-]+@[\w-]+(\.[\w-]+)+", value)


@pytest.mark.parametrize("scalar_name", ["PhoneNumber", "Phone"])
def test_infers_fictional_phone_numbers_for_phone_scalars(scalar_name):
    for value in stubs_of(scalar_name):
        assert re.fullmatch(r"\+1 \d{3} 555 01\d{2}", value)


@pytest.mark.parametrize("scalar_name", ["BigInt", "Long", "BIGINT"])
def test_infers_integers_for_big_integer_scalars(scalar_name):
    for value in stubs_of(scalar_name):
        assert isinstance(value, int)
        assert not isinstance(value, bool)
        assert value >= 0


@pytest.mark.parametrize("scalar_name", ["Decimal", "BigDecimal"])
def test_infers_two_decimal_floats_for_decimal_scalars(scalar_name):
    for value in stubs_of(scalar_name):
        assert isinstance(value, float)
        assert round(value, 2) == value
        assert 0 <= value <= 1000


@pytest.mark.parametrize("scalar_name", ["Money", "TimeZone", "Locale", "LocalPhone"])
def test_unknown_custom_scalars_still_resolve_to_strings(scalar_name):
    for value in stubs_of(scalar_name):
        assert isinstance(value, str)
        assert re.fullmatch(r"[A-Za-z]+", value)


TEMPORAL_SCHEMA = """
scalar DateTime
scalar Date
scalar Time

type Event {
  createdAt: DateTime
  updatedAt: DateTime
  publishedOn: DateTime
  startDate: Date
  doorsOpenAt: Time
  birthday: Date
}

type Query {
  event(id: ID!): Event
}
"""


@pytest.fixture(scope="module")
def events():
    stubber = Stubber(TEMPORAL_SCHEMA)
    return [stubber.resolve("Query", "event", args={"id": str(i)}) for i in range(30)]


def test_updated_at_is_never_before_created_at_for_custom_date_time_scalars(events):
    for event in events:
        created = datetime.fromisoformat(event["createdAt"])
        assert datetime.fromisoformat(event["updatedAt"]) >= created
        assert datetime.fromisoformat(event["publishedOn"]) >= created


def test_formats_timestamp_fields_for_their_custom_scalar(events):
    for event in events:
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T[\d:.]+Z", event["updatedAt"])
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", event["startDate"])
        assert re.fullmatch(r"\d{2}:\d{2}:\d{2}\.\d{3}", event["doorsOpenAt"])
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", event["birthday"])


def test_infers_adult_birthdays_for_custom_date_scalars(events):
    for event in events:
        assert 1945 <= int(event["birthday"][:4]) <= 2007


ECHO_SCHEMA = """
scalar JSON
scalar BigInt
scalar Long
scalar Decimal
scalar DateTime
scalar Email

type Thing {
  payload: JSON
  views: BigInt
  size: Long
  price: Decimal
  seenAt: DateTime
  contact: Email
}

type Query {
  thing: Thing
}
"""


def echoed(field, value):
    stubber = Stubber(ECHO_SCHEMA)
    # Inside an input object, so a JSON object isn't mistaken for one.
    thing = stubber.resolve(
        "Query", "thing", args={"input": {field: value}}, selection=f"{{ {field} }}"
    )
    return thing[field]


@pytest.mark.parametrize(
    "value", [{"a": [1, 2]}, [1, "two", None], "text", 3, 2.5, True]
)
def test_echoes_any_json_value_into_json_fields(value):
    assert echoed("payload", value) == value


@pytest.mark.parametrize("field", ["views", "size"])
def test_echoes_integers_into_big_integer_fields(field):
    assert echoed(field, 5_000_000_000) == 5_000_000_000


@pytest.mark.parametrize("field", ["views", "size"])
@pytest.mark.parametrize("value", ["12", 1.5, True])
def test_does_not_echo_non_integers_into_big_integer_fields(field, value):
    result = echoed(field, value)
    assert result != value
    assert isinstance(result, int)
    assert not isinstance(result, bool)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("price", "19.99"),
        ("seenAt", "2024-05-01T10:00:00.000Z"),
        ("contact", "ada@example.com"),
    ],
)
def test_echoes_strings_into_the_other_custom_scalar_fields(field, value):
    assert echoed(field, value) == value


@pytest.mark.parametrize("field", ["price", "seenAt", "contact"])
def test_does_not_echo_numbers_into_string_like_custom_scalar_fields(field):
    assert echoed(field, 7) != 7


PRECEDENCE_SCHEMA = """
scalar Email
scalar JSON
scalar UUID

type Contact {
  phone: Email
  createdAt: JSON
  name: UUID
}

type Query {
  contact(id: ID!): Contact
}
"""


def test_field_names_do_not_override_what_a_custom_scalar_name_says():
    contact = Stubber(PRECEDENCE_SCHEMA).resolve("Query", "contact", args={"id": "1"})
    assert re.fullmatch(r"[\w.+-]+@[\w-]+(\.[\w-]+)+", contact["phone"])
    assert isinstance(contact["createdAt"], dict)
    assert str(uuid.UUID(contact["name"])) == contact["name"]


def test_custom_scalar_stubs_are_the_same_in_every_stubber():
    for scalar_name in ["UUID", "DateTime", "JSON", "Email", "BigInt", "Decimal"]:
        assert stubs_of(scalar_name) == stubs_of(scalar_name)
