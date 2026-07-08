import os
import subprocess

import uvicorn
from mcp.server.fastmcp import FastMCP
from starlette.middleware.cors import CORSMiddleware

OUTPUT_LIMIT = 100_000
TIMEOUT_SECONDS = 60
PORT = 8642


def build_args(*base: str, **flags) -> list[str]:
    """Build an aws CLI argv from positional parts and optional --flags.

    None/False flags are skipped, True becomes a bare flag, lists splat into
    repeated values, everything else is stringified. Underscores in flag names
    become hyphens.
    """
    args = list(base)
    for name, value in flags.items():
        if value is None or value is False:
            continue
        flag = "--" + name.replace("_", "-")
        if value is True:
            args.append(flag)
        elif isinstance(value, list):
            args += [flag, *(str(v) for v in value)]
        else:
            args += [flag, str(value)]
    return args


def run(env: dict, *args: str) -> str:
    result = subprocess.run(
        ["aws", *args],
        capture_output=True,
        text=True,
        env=env,
        timeout=TIMEOUT_SECONDS,
    )
    output = result.stdout
    if result.returncode != 0:
        output += f"\n[exit code {result.returncode}]\n{result.stderr}"
    if len(output) > OUTPUT_LIMIT:
        output = output[:OUTPUT_LIMIT] + f"\n... truncated at {OUTPUT_LIMIT} chars"
    return output


def create_server(env: dict) -> FastMCP:
    mcp = FastMCP("aws-readonly", host="127.0.0.1", port=PORT, instructions="Read-only AWS tools")

    @mcp.tool()
    def logs_describe_log_groups(log_group_name_prefix: str | None = None, limit: int | None = None,
                                 include_linked_accounts: bool | None = None,
                                 account_identifiers: list[str] | None = None) -> str:
        return run(env, *build_args("logs", "describe-log-groups",
                                    log_group_name_prefix=log_group_name_prefix, limit=limit,
                                    include_linked_accounts=include_linked_accounts,
                                    account_identifiers=account_identifiers))

    @mcp.tool()
    def logs_describe_log_streams(log_group_name: str | None = None, log_group_identifier: str | None = None,
                                  order_by: str | None = None,
                                  descending: bool | None = None, log_stream_name_prefix: str | None = None,
                                  limit: int | None = None) -> str:
        return run(env, *build_args("logs", "describe-log-streams", log_group_name=log_group_name,
                                    log_group_identifier=log_group_identifier,
                                    order_by=order_by, descending=descending,
                                    log_stream_name_prefix=log_stream_name_prefix, limit=limit))

    @mcp.tool()
    def logs_get_log_events(log_stream_name: str, log_group_name: str | None = None,
                            log_group_identifier: str | None = None, start_time: int | None = None,
                            end_time: int | None = None, limit: int | None = None,
                            start_from_head: bool | None = None) -> str:
        return run(env, *build_args("logs", "get-log-events", log_group_name=log_group_name,
                                    log_group_identifier=log_group_identifier,
                                    log_stream_name=log_stream_name, start_time=start_time,
                                    end_time=end_time, limit=limit, start_from_head=start_from_head))

    @mcp.tool()
    def logs_filter_log_events(log_group_name: str | None = None, log_group_identifier: str | None = None,
                               start_time: int | None = None,
                               end_time: int | None = None, filter_pattern: str | None = None,
                               limit: int | None = None) -> str:
        return run(env, *build_args("logs", "filter-log-events", log_group_name=log_group_name,
                                    log_group_identifier=log_group_identifier,
                                    start_time=start_time, end_time=end_time,
                                    filter_pattern=filter_pattern, limit=limit))

    @mcp.tool()
    def logs_tail(log_group_name: str, since: str | None = None, filter_pattern: str | None = None,
                  format: str | None = None) -> str:
        return run(env, *build_args("logs", "tail", log_group_name,
                                    since=since, filter_pattern=filter_pattern, format=format))

    @mcp.tool()
    def logs_start_query(start_time: int, end_time: int, query_string: str,
                         log_group_name: str | None = None, log_group_names: list[str] | None = None,
                         log_group_identifiers: list[str] | None = None,
                         limit: int | None = None) -> str:
        return run(env, *build_args("logs", "start-query", log_group_name=log_group_name,
                                    log_group_names=log_group_names,
                                    log_group_identifiers=log_group_identifiers,
                                    start_time=start_time, end_time=end_time,
                                    query_string=query_string, limit=limit))

    @mcp.tool()
    def logs_get_query_results(query_id: str) -> str:
        return run(env, *build_args("logs", "get-query-results", query_id=query_id))

    @mcp.tool()
    def logs_stop_query(query_id: str) -> str:
        return run(env, *build_args("logs", "stop-query", query_id=query_id))

    @mcp.tool()
    def cloudwatch_describe_alarms(alarm_names: list[str] | None = None, alarm_name_prefix: str | None = None,
                                   state_value: str | None = None, max_records: int | None = None) -> str:
        return run(env, *build_args("cloudwatch", "describe-alarms", alarm_names=alarm_names,
                                    alarm_name_prefix=alarm_name_prefix, state_value=state_value,
                                    max_records=max_records))

    @mcp.tool()
    def cloudwatch_describe_alarm_history(alarm_name: str | None = None, history_item_type: str | None = None,
                                          start_date: str | None = None, end_date: str | None = None,
                                          max_records: int | None = None) -> str:
        return run(env, *build_args("cloudwatch", "describe-alarm-history", alarm_name=alarm_name,
                                    history_item_type=history_item_type, start_date=start_date,
                                    end_date=end_date, max_records=max_records))

    @mcp.tool()
    def cloudwatch_list_metrics(namespace: str | None = None, metric_name: str | None = None) -> str:
        return run(env, *build_args("cloudwatch", "list-metrics", namespace=namespace, metric_name=metric_name))

    @mcp.tool()
    def cloudwatch_get_metric_data(metric_data_queries: str, start_time: str, end_time: str) -> str:
        return run(env, *build_args("cloudwatch", "get-metric-data", metric_data_queries=metric_data_queries,
                                    start_time=start_time, end_time=end_time))

    @mcp.tool()
    def cloudwatch_get_metric_statistics(namespace: str, metric_name: str, start_time: str, end_time: str,
                                         period: int, statistics: list[str] | None = None,
                                         dimensions: list[str] | None = None) -> str:
        return run(env, *build_args("cloudwatch", "get-metric-statistics", namespace=namespace,
                                    metric_name=metric_name, start_time=start_time, end_time=end_time,
                                    period=period, statistics=statistics, dimensions=dimensions))

    @mcp.tool()
    def s3_ls(path: str | None = None, recursive: bool | None = None,
              human_readable: bool | None = None, summarize: bool | None = None) -> str:
        base = ["s3", "ls"] + ([path] if path else [])
        return run(env, *build_args(*base, recursive=recursive,
                                    human_readable=human_readable, summarize=summarize))

    @mcp.tool()
    def s3api_list_buckets() -> str:
        return run(env, *build_args("s3api", "list-buckets"))

    @mcp.tool()
    def s3api_list_objects_v2(bucket: str, prefix: str | None = None, max_keys: int | None = None,
                              delimiter: str | None = None, start_after: str | None = None) -> str:
        return run(env, *build_args("s3api", "list-objects-v2", bucket=bucket, prefix=prefix,
                                    max_keys=max_keys, delimiter=delimiter, start_after=start_after))

    @mcp.tool()
    def s3api_head_object(bucket: str, key: str) -> str:
        return run(env, *build_args("s3api", "head-object", bucket=bucket, key=key))

    @mcp.tool()
    def sts_get_caller_identity() -> str:
        return run(env, *build_args("sts", "get-caller-identity"))

    @mcp.tool()
    def cloudformation_list_stacks(stack_status_filter: list[str] | None = None) -> str:
        return run(env, *build_args("cloudformation", "list-stacks", stack_status_filter=stack_status_filter))

    @mcp.tool()
    def cloudformation_describe_stacks(stack_name: str | None = None) -> str:
        return run(env, *build_args("cloudformation", "describe-stacks", stack_name=stack_name))

    @mcp.tool()
    def cloudformation_describe_stack_events(stack_name: str) -> str:
        return run(env, *build_args("cloudformation", "describe-stack-events", stack_name=stack_name))

    @mcp.tool()
    def cloudformation_list_exports() -> str:
        return run(env, *build_args("cloudformation", "list-exports"))

    @mcp.tool()
    def cloudformation_list_imports(export_name: str) -> str:
        return run(env, *build_args("cloudformation", "list-imports", export_name=export_name))

    @mcp.tool()
    def ecs_list_clusters() -> str:
        return run(env, *build_args("ecs", "list-clusters"))

    @mcp.tool()
    def ecs_list_services(cluster: str | None = None) -> str:
        return run(env, *build_args("ecs", "list-services", cluster=cluster))

    @mcp.tool()
    def ecs_list_tasks(cluster: str | None = None, service_name: str | None = None,
                       desired_status: str | None = None) -> str:
        return run(env, *build_args("ecs", "list-tasks", cluster=cluster,
                                    service_name=service_name, desired_status=desired_status))

    @mcp.tool()
    def ecs_describe_clusters(clusters: list[str] | None = None) -> str:
        return run(env, *build_args("ecs", "describe-clusters", clusters=clusters))

    @mcp.tool()
    def ecs_describe_services(cluster: str, services: list[str]) -> str:
        return run(env, *build_args("ecs", "describe-services", cluster=cluster, services=services))

    @mcp.tool()
    def ecs_describe_tasks(cluster: str, tasks: list[str]) -> str:
        return run(env, *build_args("ecs", "describe-tasks", cluster=cluster, tasks=tasks))

    @mcp.tool()
    def ecs_describe_task_definition(task_definition: str) -> str:
        return run(env, *build_args("ecs", "describe-task-definition", task_definition=task_definition))

    @mcp.tool()
    def autoscaling_describe_auto_scaling_groups(auto_scaling_group_names: list[str] | None = None,
                                                 max_records: int | None = None) -> str:
        return run(env, *build_args("autoscaling", "describe-auto-scaling-groups",
                                    auto_scaling_group_names=auto_scaling_group_names,
                                    max_records=max_records))

    @mcp.tool()
    def codebuild_batch_get_builds(ids: list[str]) -> str:
        return run(env, *build_args("codebuild", "batch-get-builds", ids=ids))

    @mcp.tool()
    def cloudtrail_lookup_events(attribute_key: str | None = None, attribute_value: str | None = None,
                                 start_time: str | None = None, end_time: str | None = None,
                                 max_results: int | None = None) -> str:
        lookup_attributes = None
        if attribute_key:
            lookup_attributes = f"AttributeKey={attribute_key},AttributeValue={attribute_value}"
        return run(env, *build_args("cloudtrail", "lookup-events", lookup_attributes=lookup_attributes,
                                    start_time=start_time, end_time=end_time, max_results=max_results))

    @mcp.tool()
    def ec2_describe_instances(instance_ids: list[str] | None = None, filter_name: str | None = None,
                               filter_values: list[str] | None = None, max_results: int | None = None) -> str:
        filters = None
        if filter_name:
            filters = f"Name={filter_name},Values={','.join(filter_values or [])}"
        return run(env, *build_args("ec2", "describe-instances", instance_ids=instance_ids,
                                    filters=filters, max_results=max_results))

    @mcp.tool()
    def oam_list_sinks(max_results: int | None = None) -> str:
        return run(env, *build_args("oam", "list-sinks", max_results=max_results))

    @mcp.tool()
    def dynamodb_describe_table(table_name: str) -> str:
        return run(env, *build_args("dynamodb", "describe-table", table_name=table_name))

    return mcp


def main():
    env = os.environ.copy()
    env["AWS_PAGER"] = ""

    mcp = create_server(env)
    app = mcp.streamable_http_app()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["Mcp-Session-Id"],
    )
    print(f"aws-readonly MCP on http://127.0.0.1:{PORT}/mcp")
    uvicorn.run(app, host="127.0.0.1", port=PORT)


if __name__ == "__main__":
    main()
