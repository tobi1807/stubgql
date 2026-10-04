import random
import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from faker import Faker

from stubgql._scalars import (
    ScalarGenerator,
    fictional_phone,
    iso_date_time,
    iso_time,
    json_object,
    moment,
)
from stubgql._seeding import derive_seed

_WORD = re.compile(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|\d+")


@dataclass(frozen=True)
class FieldContext:
    """Where a value sits: its field, and the object that owns the field."""

    parent_name: str
    field_name: str
    parent_seed: int


def words(name: str) -> list[str]:
    """Split a camelCase, PascalCase or snake_case name into lowercase words."""
    return [word.lower() for word in _WORD.findall(name)]


@dataclass(frozen=True)
class Rule:
    """Generates values for fields whose name contains all of `words`.

    A rule with `parents` only applies to fields of those types.
    """

    words: frozenset[str]
    scalars: frozenset[str]
    generate: Callable[[Faker], Any]
    parents: frozenset[str] | None = None


def rule(
    words: str,
    scalars: frozenset[str],
    generate: Callable[[Faker], Any],
    parents: frozenset[str] | None = None,
) -> Rule:
    return Rule(frozenset(words.split()), scalars, generate, parents)


STRING = frozenset({"String"})
EMAIL = frozenset({"String", "AWSEmail"})
PHONE = frozenset({"String", "AWSPhone"})
URL = frozenset({"String", "AWSURL"})
INT = frozenset({"Int"})
FLOAT = frozenset({"Float"})

PERSON_TYPES = frozenset(
    {"User", "Person", "Customer", "Author", "Employee", "Member", "Contact", "Profile"}
)


ORGANIZATION_TYPES = frozenset(
    {"Company", "Organization", "Organisation", "Business", "Vendor", "Supplier"}
)


def _title(faker: Faker) -> str:
    return " ".join(word.capitalize() for word in faker.words(2, unique=True))


def _image_url(faker: Faker) -> str:
    # picsum.photos serves the same image for the same seed, so stubs stay stable.
    width, height = faker.random_element([(640, 480), (800, 600), (400, 400)])
    return f"https://picsum.photos/seed/{faker.word()}/{width}/{height}"


def _web_url(faker: Faker) -> str:
    return faker.url(schemes=["https"])


def _short_title(faker: Faker) -> str:
    return faker.sentence(nb_words=4).rstrip(".")


def _prose(faker: Faker) -> str:
    return " ".join(faker.sentences(2))


def _money(faker: Faker) -> float:
    return round(faker.random.uniform(1, 1000), 2)


def _full_name(faker: Faker) -> str:
    # faker.name() sometimes adds titles such as "Dr." or "MD".
    return f"{faker.first_name()} {faker.last_name()}"


# Checked in order; the first matching rule wins.
RULES: tuple[Rule, ...] = (
    rule("email", EMAIL, lambda faker: faker.email()),
    rule("phone", PHONE, fictional_phone),
    rule("telephone", PHONE, fictional_phone),
    rule("mobile", PHONE, fictional_phone),
    *(
        rule(word, URL, _image_url)
        for word in ("avatar", "image", "photo", "picture", "thumbnail", "logo")
    ),
    *(rule(word, URL, _web_url) for word in ("url", "website", "link", "homepage")),
    rule("first name", STRING, lambda faker: faker.first_name()),
    rule("last name", STRING, lambda faker: faker.last_name()),
    rule("surname", STRING, lambda faker: faker.last_name()),
    rule("full name", STRING, _full_name),
    rule("street", STRING, lambda faker: faker.street_address()),
    rule("address", STRING, lambda faker: faker.street_address()),
    rule("city", STRING, lambda faker: faker.city()),
    rule("state", STRING, lambda faker: faker.state()),
    *(
        rule(words, STRING, lambda faker: faker.postcode())
        for words in ("zip", "postal", "postcode")
    ),
    rule("country code", STRING, lambda faker: faker.country_code()),
    rule("country", STRING, lambda faker: faker.country()),
    *(rule(word, STRING, _short_title) for word in ("title", "headline", "subject")),
    *(
        rule(word, STRING, _prose)
        for word in (
            "description",
            "summary",
            "bio",
            "body",
            "content",
            "about",
            "notes",
            "comment",
            "message",
        )
    ),
    # Before money, so totalCount is a count.
    *(
        rule(word, INT, lambda faker: faker.random_int(0, 100))
        for word in ("count", "quantity", "qty")
    ),
    *(
        rule(word, FLOAT, _money)
        for word in ("price", "amount", "total", "cost", "fee", "balance", "salary")
    ),
    *(
        rule(word, INT, lambda faker: faker.random_int(1, 1000))
        for word in ("price", "amount", "total", "cost", "fee", "balance", "salary")
    ),
    rule("age", INT, lambda faker: faker.random_int(18, 80)),
    *(
        rule(word, FLOAT, lambda faker: float(faker.latitude()))
        for word in ("lat", "latitude")
    ),
    *(
        rule(word, FLOAT, lambda faker: float(faker.longitude()))
        for word in ("lng", "lon", "longitude")
    ),
    rule("currency", STRING, lambda faker: faker.currency_code()),
    rule("color", STRING, lambda faker: faker.hex_color()),
    rule("colour", STRING, lambda faker: faker.hex_color()),
    rule("user name", STRING, lambda faker: faker.user_name()),
    rule("username", STRING, lambda faker: faker.user_name()),
    rule("name", STRING, _full_name, parents=PERSON_TYPES),
    rule("name", STRING, lambda faker: faker.company(), parents=ORGANIZATION_TYPES),
    rule("name", STRING, _title),
)


TEMPORAL_SCALARS = frozenset(
    {"String", "AWSDate", "AWSTime", "AWSDateTime", "AWSTimestamp"}
)
BIRTHS_START = datetime(1945, 1, 1, tzinfo=UTC)
BIRTHS_END = datetime(2008, 1, 1, tzinfo=UTC)


# Scalar names, as lowercase words, mapped to the kind of value they hold.
SCALAR_KINDS: dict[tuple[str, ...], str] = {
    ("uuid",): "uuid",
    ("guid",): "uuid",
    ("date", "time"): "datetime",
    ("datetime",): "datetime",
    ("timestamp",): "datetime",
    ("instant",): "datetime",
    ("date",): "date",
    ("time",): "time",
    ("json",): "json",
    ("json", "object"): "json",
    ("url",): "url",
    ("uri",): "url",
    ("email",): "email",
    ("email", "address"): "email",
    ("phone",): "phone",
    ("phone", "number"): "phone",
    ("big", "int"): "integer",
    ("bigint",): "integer",
    ("long",): "integer",
    ("decimal",): "decimal",
    ("big", "decimal"): "decimal",
    ("bigdecimal",): "decimal",
}

# Words that say how a date or time is written, not what it is: DateTimeISO,
# LocalDate. Other kinds don't take them, so TimeZone or LocalPhone stay unknown.
MOMENT_QUALIFIERS = frozenset(
    {"iso", "8601", "rfc", "3339", "utc", "local", "zoned", "offset"}
)

MOMENT_FORMATS: dict[str, Callable[[datetime], str]] = {
    "datetime": iso_date_time,
    "date": lambda value: value.date().isoformat(),
    "time": iso_time,
}

SCALAR_KIND_GENERATORS: dict[str, ScalarGenerator] = {
    "uuid": lambda faker: faker.uuid4(),
    "json": json_object,
    "url": _web_url,
    "email": lambda faker: faker.email(),
    "phone": fictional_phone,
    "integer": lambda faker: faker.random_int(0, 10**12),
    "decimal": _money,
    **{
        kind: lambda faker, format=format: format(moment(faker.random))
        for kind, format in MOMENT_FORMATS.items()
    },
}


def scalar_kind(scalar_name: str) -> str | None:
    """The kind of value a custom scalar's name suggests, such as `"uuid"`."""
    name_words = tuple(words(scalar_name))
    if kind := SCALAR_KINDS.get(name_words):
        return kind
    unqualified = tuple(word for word in name_words if word not in MOMENT_QUALIFIERS)
    kind = SCALAR_KINDS.get(unqualified)
    return kind if kind in MOMENT_FORMATS else None


def infer_from_scalar_name(scalar_name: str) -> ScalarGenerator | None:
    """Pick a generator from a custom scalar's name, such as `UUID`."""
    kind = scalar_kind(scalar_name)
    return SCALAR_KIND_GENERATORS[kind] if kind else None


def infer(context: FieldContext, scalar_name: str) -> ScalarGenerator | None:
    """Pick a generator from a field's name, if a rule matches its scalar type."""
    field_words = words(context.field_name)
    if (
        scalar_name in TEMPORAL_SCALARS or scalar_kind(scalar_name) in MOMENT_FORMATS
    ) and (temporal := _temporal(context, field_words, scalar_name)):
        return temporal
    for candidate in RULES:
        if (
            scalar_name in candidate.scalars
            and candidate.words <= set(field_words)
            and (candidate.parents is None or context.parent_name in candidate.parents)
        ):
            return candidate.generate
    return None


def _temporal(
    context: FieldContext, field_words: list[str], scalar_name: str
) -> ScalarGenerator | None:
    word_set = set(field_words)
    date_only = "date" in word_set and "time" not in word_set
    if "birthday" in word_set or "dob" in word_set or {"birth", "date"} <= word_set:
        return lambda faker: _format_moment(
            moment(faker.random, BIRTHS_START, BIRTHS_END), scalar_name, date_only=True
        )
    if not (
        field_words[-1] in {"at", "on"} or word_set & {"date", "time", "timestamp"}
    ):
        return None

    def generate(faker: Faker) -> Any:
        # Every timestamp on an object is measured from the same "created"
        # moment, seeded by the object, so updatedAt never precedes createdAt.
        created = moment(random.Random(derive_seed(context.parent_seed, "created")))
        offset = timedelta(0)
        if "created" not in word_set:
            offset = timedelta(seconds=faker.random.randrange(365 * 24 * 60 * 60))
        return _format_moment(created + offset, scalar_name, date_only)

    return generate


def _format_moment(value: datetime, scalar_name: str, date_only: bool) -> Any:
    if scalar_name == "AWSTimestamp":
        return int(value.timestamp())
    if scalar_name == "AWSTime":
        return iso_time(value)
    if (kind := scalar_kind(scalar_name)) in MOMENT_FORMATS:
        return MOMENT_FORMATS[kind](value)  # a custom scalar is never cut short
    if scalar_name == "AWSDate" or date_only:
        return value.date().isoformat()
    return iso_date_time(value)
