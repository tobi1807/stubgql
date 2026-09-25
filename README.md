# stubgql

Schema-aware stub data for GraphQL, with built-in AWS AppSync support.

> **Status: pre-alpha.** The API below is the design target and isn't implemented yet.

stubgql stands in for resolvers that don't exist yet. Give it a schema and it returns realistic, schema-conformant data for any field, so you can exercise the schema and its access rules before the real data sources are built.

```python
from stubgql import Stubber

stubber = Stubber("schema.graphql")


# As an AppSync direct resolver (in Lambda or anywhere else that receives AppSync events)
def handler(event, context):
    return stubber.handle(event)


# Or directly
stubber.resolve("Query", "getUser", args={"id": "1"})
```

## What it does automatically

- **Realistic values from names.** `email`, `firstName`, `avatarUrl`, `createdAt`, `price` and many more are inferred from field and type names.
- **AppSync without setup.** AWS scalars (`AWSDateTime`, `AWSJSON`, `AWSEmail`, …) and directives (`@aws_iam`, `@aws_subscribe`, …) work even though AppSync schemas don't declare them. Single and batch events are both handled.
- **Deterministic output.** The same query returns the same data every time.
- **Consistent entities.** An object with an `id` looks the same wherever it appears.
- **Argument echo.** `getUser(id: "1")` returns `id: "1"`, and mutation inputs show up in the result.

## What it doesn't do

- **Configuration.** There are no options. If you need a specific value, write the real resolver for that field.
- **State.** A mutation doesn't change what later queries return.
- **Infrastructure.** No Lambda, CDK or AWS SDK code. You write the handler; stubgql only works with the event data.

## Installation

```sh
pip install stubgql
```

Requires Python 3.11+.

## License

MIT
