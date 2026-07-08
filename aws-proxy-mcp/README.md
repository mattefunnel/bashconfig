# aws-proxy-mcp

MCP web service that exposes a fixed set of read-only AWS operations as explicit,
typed tools. Meant for agent sessions that have no AWS credentials of their own:
the server runs with your credentials and exposes only benign investigation
commands (logs, alarms, S3 listing, CloudFormation, ECS).

There is no allow list to bypass: each tool is hand-written to build one exact
`aws` CLI invocation from typed parameters. A caller cannot reach any command or
flag that a tool does not emit.

## Run

```sh
aws-vault exec prod-eu -- uv run server.py
```

It uses the ambient AWS configuration (credentials and region from the
environment), so run it under whichever `aws-vault` profile you want. The MCP
endpoint is `http://127.0.0.1:8642/mcp`.

Add it to an agent session:

```sh
claude mcp add --scope user --transport http aws http://127.0.0.1:8642/mcp
```

## What it exposes

One tool per operation, named `<service>_<action>` with typed parameters, e.g.
`logs_filter_log_events(log_group_name, start_time, filter_pattern, limit)`,
`cloudwatch_describe_alarms(state_value, ...)`, `s3_ls(path, recursive, ...)`.
Agents discover the full set and each tool's parameters through MCP tool listing.

Covered services: `logs`, `cloudwatch`, `s3`/`s3api`, `sts`, `cloudformation`,
`ecs`, `autoscaling`, `codebuild`, `cloudtrail`, `ec2`, `oam`, `dynamodb`. To add
or remove an operation, edit the tools in `server.py` — there is no config file.

One process per account/region: pick the account/region with the `aws-vault`
profile you run it under.

## How it stays safe

Each tool builds an exact argv list with `build_args()` and runs it via
`subprocess.run(["aws", ...])` without a shell. Parameter values become separate
argv items, so a value that looks like `--profile evil` is passed as one literal
argument, not interpreted as a flag. There is no free-form command string and no
allow list to outsmart. Output is truncated at 100k chars; commands are killed
after 60s.

## Test

```sh
uv run pytest
uv run smoke.py http://127.0.0.1:8642/mcp                                    # against a running server
uv run probe.py http://127.0.0.1:8642/mcp s3_ls '{"path": "s3://my-bucket"}' # one-off tool call
```
