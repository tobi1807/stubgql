# Determinism contract

The same input always produces the same stub. Seeds are derived with `hashlib` from the schema coordinate and arguments, or from `(type, id)` for entities, so an entity looks the same wherever it appears. Python's built-in `hash()` is never used because it varies between processes, and the global `random` state is never touched.

The guarantee holds for a given stubgql version and Faker version. Faker doesn't promise stable seeded output across its releases, so snapshot tests watch for drift on dependency upgrades. Once stubgql reaches 1.0, any intentional change to generated output is a breaking change.
