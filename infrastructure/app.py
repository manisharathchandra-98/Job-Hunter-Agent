#!/usr/bin/env python3
"""
CDK App Entry Point
Run: cdk deploy --all
"""
#!/usr/bin/env python3
import os
import aws_cdk as cdk
from stacks.database_stack import DatabaseStack
from stacks.main_stack import MainStack

app = cdk.App()

env = cdk.Environment(
    account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
    region=os.environ.get("CDK_DEFAULT_REGION", "us-east-1"),
)

db_stack = DatabaseStack(app, "JobAnalyzerDBStack", env=env)
main_stack = MainStack(app, "JobAnalyzerMainStack", db_stack=db_stack, env=env)

app.synth()