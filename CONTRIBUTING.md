# Contributing

Thanks for helping with stubgql.

## Setup

You need [uv](https://docs.astral.sh/uv/).

```sh
uv sync
uv run prek install
```

## Before opening a PR

- Read [`CONTEXT.md`](./CONTEXT.md) for the project's vocabulary and [`docs/adr/`](./docs/adr/) for decisions about scope.
- Follow the rules and the definition of done in [`AGENTS.md`](./AGENTS.md). They apply to people as much as to coding agents.
- Use a [Conventional Commits](https://www.conventionalcommits.org/) PR title, such as `feat: infer phone numbers from mobile fields`.

stubgql deliberately has no configuration and stores no state. Feature requests that add either are likely to be declined, so please open an issue to discuss before building one.
