from collections.abc import Callable
from typing import Any

from faker import Faker

ScalarGenerator = Callable[[Faker], Any]

SCALAR_GENERATORS: dict[str, ScalarGenerator] = {
    "String": lambda faker: faker.word(),
    "Int": lambda faker: faker.random_int(0, 1000),
    "Float": lambda faker: round(faker.random.uniform(0, 1000), 2),
    "Boolean": lambda faker: faker.boolean(),
    "ID": lambda faker: faker.uuid4(),
}
