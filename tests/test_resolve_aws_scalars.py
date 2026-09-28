import ipaddress
import json
import re
from datetime import date, datetime, time
from urllib.parse import urlparse

import pytest

from stubgql import Stubber

SCHEMA = """
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


def is_aws_date(value):
    # Documented format: YYYY-MM-DD
    return re.fullmatch(r"\d{4}-\d{2}-\d{2}", value) and date.fromisoformat(value)


def is_aws_time(value):
    # Documented format: hh:mm:ss.sss
    return re.fullmatch(r"\d{2}:\d{2}:\d{2}\.\d{3}", value) and time.fromisoformat(
        value
    )


def is_aws_date_time(value):
    # Documented format: YYYY-MM-DDThh:mm:ss.sssZ
    pattern = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z"
    return re.fullmatch(pattern, value) and datetime.fromisoformat(value)


def is_aws_timestamp(value):
    # Documented as an integer number of seconds since the epoch
    return type(value) is int


def is_aws_email(value):
    return re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value)


def is_aws_json(value):
    # Documented as a JSON string
    return isinstance(value, str) and json.loads(value) is not None


def is_aws_url(value):
    # Documented: must have a scheme and no "//" in the path
    parsed = urlparse(value)
    return (
        parsed.scheme in {"http", "https"} and parsed.netloc and "//" not in parsed.path
    )


def is_aws_phone(value):
    # Documented: digit groups separated by spaces or hyphens, optional country code
    return re.fullmatch(r"\+?\d+([ -]\d+)*", value)


def is_aws_ip_address(value):
    return ipaddress.ip_address(value)


@pytest.mark.parametrize(
    ("field", "is_valid"),
    [
        ("date", is_aws_date),
        ("time", is_aws_time),
        ("dateTime", is_aws_date_time),
        ("timestamp", is_aws_timestamp),
        ("email", is_aws_email),
        ("json", is_aws_json),
        ("url", is_aws_url),
        ("phone", is_aws_phone),
        ("ip", is_aws_ip_address),
    ],
)
def test_resolves_aws_scalars_in_their_documented_format(field, is_valid):
    value = Stubber(SCHEMA).resolve("Query", field)
    assert is_valid(value), f"{field}: {value!r}"
