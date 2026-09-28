import json
import os
import subprocess
import sys

from stubgql import Stubber

SCHEMA = """
type Query {
  title: String
  subtitle: String
  greet(name: String): String
}
"""


def test_different_fields_get_different_values():
    stubber = Stubber(SCHEMA)
    assert stubber.resolve("Query", "title") != stubber.resolve("Query", "subtitle")


def test_different_arguments_get_different_values():
    stubber = Stubber(SCHEMA)
    ada = stubber.resolve("Query", "greet", args={"name": "Ada"})
    grace = stubber.resolve("Query", "greet", args={"name": "Grace"})
    assert ada != grace


def test_the_same_call_gives_the_same_value_from_any_stubber():
    first = Stubber(SCHEMA).resolve("Query", "greet", args={"name": "Ada"})
    second = Stubber(SCHEMA).resolve("Query", "greet", args={"name": "Ada"})
    assert first == second


RESOLVE_IN_SUBPROCESS = """
import json, sys
from stubgql import Stubber
stubber = Stubber(sys.argv[1])
print(json.dumps([
    stubber.resolve("Query", "title"),
    stubber.resolve("Query", "greet", args={"name": "Ada", "tags": ["a", "b"]}),
]))
"""


def resolve_in_subprocess(hash_seed):
    result = subprocess.run(
        [sys.executable, "-c", RESOLVE_IN_SUBPROCESS, SCHEMA],
        env={**os.environ, "PYTHONHASHSEED": hash_seed},
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def test_the_same_call_gives_the_same_value_in_every_process():
    assert resolve_in_subprocess("1") == resolve_in_subprocess("2")
