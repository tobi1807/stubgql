# stubgql

stubgql stands in for GraphQL resolvers that don't exist yet. It returns schema-conformant data so a schema and its access rules can be exercised end to end. It is not a substitute for a real data source.

## Language

### Stubs

**Stub**:
A generated value for a field that conforms to the field's schema type.
_Avoid_: mock, fake, dummy data

**Stubber**:
The thing that holds one schema and produces stubs for it.
_Avoid_: mocker, generator

**Resolve**:
To produce a stub for a schema coordinate.
_Avoid_: generate, mock

**Inference**:
Choosing how to generate a value from a field name, its parent type name, or a scalar name.
_Avoid_: heuristics, guessing

### Schema

**Schema coordinate**:
A `Type.field` reference such as `Query.getUser`, as defined by the GraphQL spec.
_Avoid_: field path, field key

**Selection**:
The subset of a type's fields that the caller asked for.
_Avoid_: projection, fields list

**Entity**:
An object type with a field named `id`. Its stubs are identified by type and id together. No other field makes a type an entity.
_Avoid_: record, model

### Determinism

**Seed**:
The deterministic input to generation, derived from the schema coordinate, the arguments, or an entity's identity.

**Argument echo**:
Argument values that reappear in the stub, such as `id` or the fields of an `input` argument.
_Avoid_: reflection, passthrough

### AppSync

**AppSync event**:
The payload AppSync sends to a direct resolver. A **batch event** is a list of them.
_Avoid_: request, payload

**Handle**:
To turn an AppSync event or batch event into its response.
_Avoid_: process, invoke

**AppSync prelude**:
Declarations for AWS scalars and directives, added to a schema that references them without declaring them.
_Avoid_: AWS preset, shim
