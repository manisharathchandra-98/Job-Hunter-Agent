from aws_cdk import (
    Stack, Duration, RemovalPolicy,
    aws_lambda as lambda_,
    aws_iam as iam,
    aws_logs as logs,
    aws_apigateway as apigw,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as tasks,
)
from constructs import Construct
from stacks.database_stack import DatabaseStack

BEDROCK_MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"
REGION = "us-east-1"


class MainStack(Stack):
    def __init__(self, scope: Construct, construct_id: str,
                 db_stack: DatabaseStack, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        common_env = {
            "BEDROCK_MODEL_ID":      BEDROCK_MODEL_ID,
            "JOBS_TABLE_NAME":       db_stack.jobs_table.table_name,
            "CANDIDATES_TABLE_NAME": db_stack.candidates_table.table_name,
            "SKILLS_TABLE_NAME":     db_stack.skills_table.table_name,
            "SALARY_TABLE_NAME":     db_stack.salary_table.table_name,
            "MATCHES_TABLE_NAME":    db_stack.matches_table.table_name,  # NEW
            "LOG_LEVEL":             "INFO",
        }

        def make_lambda(name: str, code_path: str,
                        handler: str = "lambda_function.lambda_handler",
                        timeout: int = 60, memory: int = 256,
                        extra_env: dict = None) -> lambda_.Function:
            env = {**common_env, **(extra_env or {})}
            fn = lambda_.Function(
                self, name,
                function_name=f"job-analyzer-{name}",
                runtime=lambda_.Runtime.PYTHON_3_11,
                code=lambda_.Code.from_asset(code_path),
                handler=handler,
                timeout=Duration.seconds(timeout),
                memory_size=memory,
                environment=env,
                log_group=logs.LogGroup(
                    self, f"LG-{name}",
                    log_group_name=f"/aws/lambda/job-analyzer-{name}",
                    retention=logs.RetentionDays.TWO_WEEKS,
                    removal_policy=RemovalPolicy.DESTROY,
                ),
            )
            fn.role.add_managed_policy(
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AmazonBedrockFullAccess"
                )
            )
            return fn

        # ── Lambda Functions ──────────────────────────────────────────────────
        agent1     = make_lambda("agent-parser",     "../agents/agent1_parser",     timeout=60)
        agent2     = make_lambda("agent-skills",     "../agents/agent2_skills",     timeout=90)
        agent3     = make_lambda("agent-salary",     "../agents/agent3_salary",     timeout=60)
        agent4     = make_lambda("agent-difficulty", "../agents/agent4_difficulty", timeout=60)
        agent5     = make_lambda("agent-gaps",       "../agents/agent5_gaps",       timeout=90, memory=512)
        aggregator = make_lambda("agent-aggregator", "../agents/aggregator",        timeout=30)

        # ── DynamoDB permissions ──────────────────────────────────────────────
        db_stack.salary_table.grant_read_data(agent3)
        db_stack.jobs_table.grant_write_data(aggregator)
        db_stack.candidates_table.grant_write_data(aggregator)   # NEW
        db_stack.matches_table.grant_write_data(aggregator)      # NEW

        # ── Step Functions ────────────────────────────────────────────────────
        parse_job = tasks.LambdaInvoke(
            self, "ParseJob",
            lambda_function=agent1,
            output_path="$.Payload",
        )
        estimate_skills = tasks.LambdaInvoke(
            self, "EstimateSkills",
            lambda_function=agent2,
            output_path="$.Payload",
        )
        analyze_salary = tasks.LambdaInvoke(
            self, "AnalyzeSalary",
            lambda_function=agent3,
            output_path="$.Payload",
        )
        score_difficulty = tasks.LambdaInvoke(
            self, "ScoreDifficulty",
            lambda_function=agent4,
            output_path="$.Payload",
        )
        identify_gaps = tasks.LambdaInvoke(
            self, "IdentifyGaps",
            lambda_function=agent5,
            output_path="$.Payload",
        )
        aggregate = tasks.LambdaInvoke(
            self, "AggregateResults",
            lambda_function=aggregator,
            output_path="$.Payload",
        )

        definition = (
            parse_job
            .next(estimate_skills)
            .next(analyze_salary)
            .next(score_difficulty)
            .next(identify_gaps)
            .next(aggregate)
        )

        sfn_log_group = logs.LogGroup(
            self, "SFNLogs",
            log_group_name="/aws/states/job-analyzer-workflow",
            retention=logs.RetentionDays.TWO_WEEKS,
            removal_policy=RemovalPolicy.DESTROY,
        )

        state_machine = sfn.StateMachine(
            self, "JobAnalyzerWorkflow",
            state_machine_name="JobAnalyzerWorkflow",
            definition_body=sfn.DefinitionBody.from_chainable(definition),
            timeout=Duration.minutes(5),
            logs=sfn.LogOptions(
                destination=sfn_log_group,
                level=sfn.LogLevel.ERROR,
            ),
        )

        api_proxy = make_lambda(
            "api-proxy",
            "../api",
            handler="lambda_proxy.lambda_handler",
            extra_env={"STATE_MACHINE_ARN": state_machine.state_machine_arn},
        )

        # ── API proxy permissions ─────────────────────────────────────────────
        db_stack.jobs_table.grant_read_write_data(api_proxy)
        db_stack.candidates_table.grant_read_write_data(api_proxy)
        db_stack.matches_table.grant_read_data(api_proxy)        # NEW

        api_proxy.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "states:StartExecution",
                    "states:DescribeExecution",
                    "states:ListExecutions",    # NEW
                ],
                resources=[state_machine.state_machine_arn],
            )
        )

        # ── API Gateway ───────────────────────────────────────────────────────
        api = apigw.RestApi(
            self, "JobAnalyzerApi",
            rest_api_name="JobAnalyzerAPI",
            description="Job Fit Analyzer REST API",
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=apigw.Cors.ALL_METHODS,
                allow_headers=["Content-Type", "Authorization"],
            ),
            deploy_options=apigw.StageOptions(stage_name="prod"),
        )

        proxy_integration = apigw.LambdaIntegration(api_proxy, proxy=True)

        # /jobs
        jobs = api.root.add_resource("jobs")
        jobs.add_method("POST", proxy_integration)
        jobs.add_method("GET",  proxy_integration)
        job_item = jobs.add_resource("{job_id}")
        job_item.add_method("GET", proxy_integration)

        # NEW: /match  (trigger full resume+job pipeline)
        match_root = api.root.add_resource("match")
        match_root.add_method("POST", proxy_integration)

        # NEW: /matches/{match_id}
        matches = api.root.add_resource("matches")
        match_item = matches.add_resource("{match_id}")
        match_item.add_method("GET", proxy_integration)

        # /candidates
        candidates = api.root.add_resource("candidates")
        candidates.add_method("POST", proxy_integration)

        # NEW: /candidates/{candidate_id}
        candidate_item = candidates.add_resource("{candidate_id}")
        candidate_item.add_method("GET", proxy_integration)

        # NEW: /candidates/{candidate_id}/matches
        candidate_matches = candidate_item.add_resource("matches")
        candidate_matches.add_method("GET", proxy_integration)