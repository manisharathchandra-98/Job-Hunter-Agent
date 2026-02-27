from aws_cdk import (
    Stack, RemovalPolicy, Duration,
    aws_dynamodb as dynamodb,
    aws_s3 as s3,
)
from constructs import Construct


class DatabaseStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        self.jobs_table = dynamodb.Table(
            self, "JobsTable",
            table_name="Jobs",
            partition_key=dynamodb.Attribute(
                name="job_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
            time_to_live_attribute="ttl",
        )
        self.jobs_table.add_global_secondary_index(
            index_name="StatusCreatedIndex",
            partition_key=dynamodb.Attribute(
                name="status",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="created_at",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.INCLUDE,
            non_key_attributes=["summary", "job_id"],
        )

        self.candidates_table = dynamodb.Table(
            self, "CandidatesTable",
            table_name="Candidates",
            partition_key=dynamodb.Attribute(
                name="candidate_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
        )

        self.skills_table = dynamodb.Table(
            self, "SkillsTaxonomyTable",
            table_name="SkillsTaxonomy",
            partition_key=dynamodb.Attribute(
                name="skill_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
        )

        self.salary_table = dynamodb.Table(
            self, "SalaryDataTable",
            table_name="SalaryData",
            partition_key=dynamodb.Attribute(
                name="salary_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
        )
        self.salary_table.add_global_secondary_index(
            index_name="TitleIndex",
            partition_key=dynamodb.Attribute(
                name="job_title_lower",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="level",
                type=dynamodb.AttributeType.STRING
            ),
        )

        self.documents_bucket = s3.Bucket(
            self, "DocumentsBucket",
            bucket_name=f"job-analyzer-docs-{self.account}",
            versioned=True,
            removal_policy=RemovalPolicy.RETAIN,
        )

        self.frontend_bucket = s3.Bucket(
            self, "FrontendBucket",
            bucket_name=f"job-analyzer-frontend-{self.account}",
            website_index_document="index.html",
            website_error_document="index.html",
            removal_policy=RemovalPolicy.DESTROY,
            public_read_access=True,
            block_public_access=s3.BlockPublicAccess(
                block_public_acls=False,
                block_public_policy=False,
                ignore_public_acls=False,
                restrict_public_buckets=False,
            ),
        )
