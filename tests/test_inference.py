import re
from urllib.parse import urlparse

import pytest
from faker.providers.address.en_US import Provider as AddressProvider
from faker.providers.person.en_US import Provider as PersonProvider

from stubgql import Stubber

FIRST_NAMES = set(PersonProvider.first_names)
LAST_NAMES = set(PersonProvider.last_names)

SCHEMA = """
type User {
  email: String
  contactEmail: String
  email_address: String
  firstName: String
  last_name: String
  fullName: String
  name: String
  username: String
  age: Int
  phone: String
  mobileNumber: String
  website: String
  avatarUrl: AWSURL
  profile_photo: String
}

type Address {
  street: String
  addressLine1: String
  city: String
  state: String
  zipCode: String
  postal_code: String
  country: String
}

type Article {
  title: String
  headline: String
  description: String
  body: String
  authorBio: String
}

type Company {
  name: String
}

type Product {
  name: String
  price: Float
  totalAmount: Float
  shippingCost: Int
  stockCount: Int
  quantity: Int
  totalCount: Int
  currency: String
  color: String
}

type Location {
  lat: Float
  latitude: Float
  lng: Float
  longitude: Float
}

type Stats {
  email: Int
}

type Query {
  user: User
  stats: Stats
  company: Company
  product: Product
  address: Address
  article: Article
  location: Location
}
"""


@pytest.fixture(scope="module")
def user():
    return Stubber(SCHEMA).resolve("Query", "user")


def is_email(value):
    return isinstance(value, str) and re.fullmatch(r"[^@\s]+@[^@\s]+\.[a-z]+", value)


@pytest.mark.parametrize("field", ["email", "contactEmail", "email_address"])
def test_infers_email_addresses_from_email_field_names(user, field):
    assert is_email(user[field]), user[field]


def test_ignores_field_names_whose_type_does_not_fit_the_inferred_value():
    stats = Stubber(SCHEMA).resolve("Query", "stats")
    assert type(stats["email"]) is int


def test_infers_first_names(user):
    assert user["firstName"] in FIRST_NAMES


def test_infers_last_names(user):
    assert user["last_name"] in LAST_NAMES


@pytest.mark.parametrize("field", ["fullName", "name"])
def test_infers_full_names_for_people(user, field):
    first, last = user[field].split(" ")
    assert first in FIRST_NAMES
    assert last in LAST_NAMES


def test_infers_company_names_for_organizations():
    company = Stubber(SCHEMA).resolve("Query", "company")
    # Faker's company formats: "Smith LLC", "Smith-Jones", "Smith, Jones and Lee".
    last = r"[A-Z][A-Za-z']+"
    pattern = rf"{last}( (Inc|LLC|Group|PLC|Ltd)|-{last}|, {last} and {last})"
    assert re.fullmatch(pattern, company["name"]), company["name"]


def test_infers_title_case_names_for_other_types():
    product = Stubber(SCHEMA).resolve("Query", "product")
    assert re.fullmatch(r"[A-Z][a-z]+( [A-Z][a-z]+)+", product["name"]), product["name"]


def test_infers_usernames(user):
    username = user["username"]
    assert re.fullmatch(r"[a-z0-9._]+", username), username
    # Faker builds usernames from a person's first and/or last name.
    names = {name.lower() for name in FIRST_NAMES | LAST_NAMES if len(name) > 3}
    assert any(name in username for name in names), username


@pytest.mark.parametrize("field", ["phone", "mobileNumber"])
def test_infers_fictional_phone_numbers(user, field):
    # 555-0100 to 555-0199 are reserved for fiction in North America.
    assert re.fullmatch(r"\+1 \d{3} 555 01\d{2}", user[field]), user[field]


def test_infers_urls_for_web_addresses(user):
    url = urlparse(user["website"])
    assert url.scheme == "https"
    assert url.netloc


@pytest.mark.parametrize("field", ["avatarUrl", "profile_photo"])
def test_infers_image_urls_for_pictures(user, field):
    url = urlparse(user[field])
    assert url.netloc == "picsum.photos", user[field]
    assert re.fullmatch(r"/seed/\w+/\d+/\d+", url.path), user[field]


@pytest.fixture(scope="module")
def address():
    return Stubber(SCHEMA).resolve("Query", "address")


@pytest.fixture(scope="module")
def article():
    return Stubber(SCHEMA).resolve("Query", "article")


@pytest.mark.parametrize("field", ["street", "addressLine1"])
def test_infers_street_addresses(address, field):
    assert re.fullmatch(r"\d+ [A-Z][\w .']+", address[field]), address[field]


def test_infers_city_names(address):
    assert re.fullmatch(r"[A-Z][a-z]+( [A-Z][a-z]+)*", address["city"])


def test_infers_states(address):
    assert address["state"] in AddressProvider.states


@pytest.mark.parametrize("field", ["zipCode", "postal_code"])
def test_infers_postal_codes(address, field):
    assert re.fullmatch(r"\d{5}", address[field]), address[field]


def test_infers_countries(address):
    assert address["country"] in AddressProvider.countries


@pytest.mark.parametrize("field", ["title", "headline"])
def test_infers_short_titles(article, field):
    assert re.fullmatch(r"[A-Z][a-z]+( [a-z]+){1,6}", article[field]), article[field]


@pytest.mark.parametrize("field", ["description", "body", "authorBio"])
def test_infers_prose_for_longer_text(article, field):
    text = article[field]
    assert text.endswith(".")
    assert len(text.split()) >= 4, text


@pytest.fixture(scope="module")
def product():
    return Stubber(SCHEMA).resolve("Query", "product")


@pytest.mark.parametrize("field", ["price", "totalAmount"])
def test_infers_money_amounts_for_float_fields(product, field):
    value = product[field]
    assert type(value) is float
    assert 0 < value <= 1000
    assert round(value, 2) == value


def test_infers_money_amounts_for_int_fields(product):
    assert type(product["shippingCost"]) is int
    assert 0 < product["shippingCost"] <= 1000


@pytest.mark.parametrize("field", ["stockCount", "quantity", "totalCount"])
def test_infers_small_counts(product, field):
    assert 0 <= product[field] <= 100


def test_infers_adult_ages(user):
    assert 18 <= user["age"] <= 80


def test_infers_currency_codes(product):
    assert re.fullmatch(r"[A-Z]{3}", product["currency"]), product["currency"]


def test_infers_hex_colors(product):
    assert re.fullmatch(r"#[0-9a-f]{6}", product["color"]), product["color"]


def test_infers_coordinates():
    location = Stubber(SCHEMA).resolve("Query", "location")
    for field in ("lat", "latitude"):
        assert -90 <= location[field] <= 90
    for field in ("lng", "longitude"):
        assert -180 <= location[field] <= 180
    assert len({location[field] for field in location}) == 4, location
