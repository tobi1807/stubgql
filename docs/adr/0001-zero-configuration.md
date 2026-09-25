# Zero configuration

stubgql has no config file, no scenarios, and no per-field overrides. Values come entirely from inference on field, type, and scalar names. When someone needs a specific value for a field, the answer is to write the real resolver for that field, since stubgql only stands in for resolvers that don't exist yet. When inference produces poor values, improve the inference rather than adding an option.

## Considered options

- **JSON config with field overrides and header-selected scenarios**: designed and then dropped. It added a second way to describe data alongside the schema, and every option became something users had to learn before the tool was useful.
