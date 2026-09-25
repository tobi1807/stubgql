# Infrastructure-agnostic boundary

stubgql understands AppSync's data shapes (events, AWS scalars and directives) but never touches infrastructure. It has no Lambda handler, no AWS SDK dependency, no schema fetching from AWS, and no CDK, SAM, or Terraform code. AppSync events arrive as plain dicts and responses leave as plain dicts, so the same code runs in Lambda, a container, or a test. Users write the handler and the deployment wiring themselves.

AppSync support is always on and needs no activation, but it lives in its own internal module so the core never depends on it.
