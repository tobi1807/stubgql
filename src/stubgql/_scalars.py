import random
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

from faker import Faker

ScalarGenerator = Callable[[Faker], Any]

# Generated moments fall in a fixed window, never relative to "now", so output
# doesn't change from one day to the next.
WINDOW_START = datetime(2020, 1, 1, tzinfo=UTC)
WINDOW_END = datetime(2026, 1, 1, tzinfo=UTC)


def moment(
    rng: random.Random, start: datetime = WINDOW_START, end: datetime = WINDOW_END
) -> datetime:
    milliseconds = int((end - start).total_seconds() * 1000)
    return start + timedelta(milliseconds=rng.randrange(milliseconds))


def iso_date_time(value: datetime) -> str:
    """Format as YYYY-MM-DDThh:mm:ss.sssZ."""
    return value.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def iso_time(value: datetime) -> str:
    """Format as hh:mm:ss.sss."""
    return value.time().isoformat(timespec="milliseconds")


def fictional_phone(faker: Faker) -> str:
    """A North American number in the 555-0100 to 555-0199 range kept for fiction."""
    return f"+1 {faker.random_int(201, 989)} 555 {faker.random_int(100, 199):04d}"


SCALAR_GENERATORS: dict[str, ScalarGenerator] = {
    "String": lambda faker: faker.word(),
    "Int": lambda faker: faker.random_int(0, 1000),
    "Float": lambda faker: round(faker.random.uniform(0, 1000), 2),
    "Boolean": lambda faker: faker.boolean(),
    "ID": lambda faker: faker.uuid4(),
}
