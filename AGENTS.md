# AGENTS.md

stubgql generates schema-conformant stub data for GraphQL fields, with built-in support for AWS AppSync direct resolver events. It's a Python library; there is no service to run.

Read `CONTEXT.md` before naming anything, and `docs/adr/` before proposing changes to scope.

## Commands

```sh
uv sync                      # install the project and dev tools
uv run pytest                # run tests
uv run ruff check --fix      # lint
uv run ruff format           # format
uv run ty check              # type check
uv run prek run --all-files  # every pre-commit hook
```

Run `uv run prek install` once after cloning so hooks run on commit.

## Layout

```
src/stubgql/__init__.py   # the public API, and nothing else
src/stubgql/_*.py         # internals; free to refactor
tests/schemas/            # sample SDL files (AppSync and plain GraphQL)
tests/events/             # sample AppSync events as JSON
docs/adr/                 # decisions that are hard to reverse
```

## Rules

### Vocabulary
- Use the terms in `CONTEXT.md` in code, tests, docs and commit messages. The tool makes **stubs**: never call them mocks or fakes.
- If a new concept needs a name, add it to `CONTEXT.md` in the same change.

### Scope
- **No configuration.** Don't add options, config files, flags or override hooks. If generated values are poor, improve inference. See ADR 0001.
- **No infrastructure.** No Lambda handlers, AWS SDK calls, or deployment code. AppSync events are plain dicts. See ADR 0002.
- **No state.** Nothing is stored between calls. See ADR 0003.
- Runtime dependencies are `graphql-core` and `faker` only. Adding one requires an ADR and the maintainer's approval.

### Public API
- Only names exported from `src/stubgql/__init__.py` are public. Every other module has a leading underscore.
- Don't add, rename or change public names or signatures without the maintainer's approval.
- Docstrings (Google style) are required on public API and optional elsewhere.

### Determinism
- Derive seeds with `hashlib`. Never use the built-in `hash()` or the module-level `random` functions; use a `random.Random(seed)` instance or a seeded Faker instance. See ADR 0004.
- Any change to generated output must be called out in the PR description.

### Errors
- Raise subclasses of `StubgqlError`. Don't let `graphql-core` or Faker exceptions escape to callers unwrapped.

### Typing
- Annotate everything. Model AppSync event shapes as `TypedDict`s rather than `dict[str, Any]`.

## Testing

- Work test-first: write a failing test for the behavior, then make it pass.
- Name tests after behavior: `test_entity_with_same_id_is_identical_across_queries`, not `test_walker_3`.
- Use real AppSync shapes in `tests/events/` and realistic schemas in `tests/schemas/`.
- Never run `pytest --snapshot-update` just to make a failing test pass. A snapshot change means generated output changed; confirm it's intended and mention it in the PR.

## Git

- Branch from `main`; never commit to `main` directly.
- Commit messages and PR titles follow Conventional Commits: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`, `ci:`. PRs are squash-merged, so the PR title becomes the commit on `main` and feeds the release notes.

## Definition of done

1. Tests cover the new behavior and `uv run pytest` passes.
2. `uv run prek run --all-files` passes (ruff, ty, lockfile and file checks).
3. New terms are in `CONTEXT.md`; changes to scope have an ADR.
4. Any change to generated output is called out.
