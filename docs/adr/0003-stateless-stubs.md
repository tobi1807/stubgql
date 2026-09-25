# Stateless stubs

stubgql stores nothing between calls. A mutation returns a stub with its arguments echoed, but later reads don't see the change: after `updateUser(input: {id: "1", name: "Bob"})`, `getUser(id: "1")` still returns the generated name. The tool exists to exercise a schema and its access rules, not to behave like a data source, so read-after-write consistency and correct pagination are non-goals.

## Considered options

- **In-memory or pluggable store**: rejected. An in-memory store only lasts while a Lambda container stays warm, and a durable store would need infrastructure, which [ADR 0002](./0002-infrastructure-agnostic-boundary.md) rules out.
- **Pagination inference from `limit`, `first`, `nextToken` or connection shapes**: out of scope for the same reason.
