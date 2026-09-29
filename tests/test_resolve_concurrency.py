import sys
from concurrent.futures import ThreadPoolExecutor

import pytest

from stubgql import Stubber

SCHEMA = """
type Query {
  tags(page: Int): [String!]!
}
"""


@pytest.fixture
def frequent_thread_switches():
    interval = sys.getswitchinterval()
    sys.setswitchinterval(1e-6)
    yield
    sys.setswitchinterval(interval)


def test_concurrent_calls_give_the_same_values_as_sequential_calls(
    frequent_thread_switches,
):
    stubber = Stubber(SCHEMA)
    pages = range(200)
    sequential = [stubber.resolve("Query", "tags", args={"page": p}) for p in pages]

    def resolve(page):
        return stubber.resolve("Query", "tags", args={"page": page})

    with ThreadPoolExecutor(max_workers=8) as pool:
        concurrent = list(pool.map(resolve, pages))

    assert concurrent == sequential
