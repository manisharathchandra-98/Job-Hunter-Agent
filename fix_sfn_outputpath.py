import subprocess
import json

SM_ARN = "arn:aws:states:us-east-1:596432516213:stateMachine:JobAnalyzerWorkflow"

result = subprocess.run(
    ["aws", "stepfunctions", "describe-state-machine", "--state-machine-arn", SM_ARN],
    capture_output=True, text=True
)
definition = json.loads(json.loads(result.stdout)["definition"])

# Fix 1: Remove OutputPath from AggregateResults so the full state is preserved.
# ResultPath: "$.aggregator_result" will ADD the result to the state instead of replacing it.
# The Lambda invocation wrapper {StatusCode, Payload} is stored at $.aggregator_result.
agg = definition["States"]["AggregateResults"]
if "OutputPath" in agg:
    del agg["OutputPath"]
    print("✅ Removed OutputPath from AggregateResults")
agg["ResultPath"] = "$.aggregator_result"
print(f"✅ AggregateResults ResultPath = $.aggregator_result")

# Fix 2: Update Invoke_ResumeCoach Parameters to read $.aggregator_result.Payload
# because without OutputPath the Lambda invocation wrapper is preserved,
# so the actual return value is nested under .Payload.
coach = definition["States"]["Invoke_ResumeCoach"]
coach["Parameters"] = {
    "FunctionName": "arn:aws:lambda:us-east-1:596432516213:function:job-analyzer-agent-resume-coach",
    "Payload": {
        "match_id.$":          "$.match_id",
        "resume_text.$":       "$.resume_text",
        "job_description.$":   "$.job_description",
        "aggregator_result.$": "$.aggregator_result.Payload"
    }
}
# Keep existing Retry if present
if "Retry" not in coach:
    coach["Retry"] = [{
        "ErrorEquals": [
            "Lambda.ClientExecutionTimeoutException",
            "Lambda.ServiceException",
            "Lambda.AWSLambdaException",
            "Lambda.SdkClientException"
        ],
        "IntervalSeconds": 2,
        "MaxAttempts": 3,
        "BackoffRate": 2
    }]
coach["Type"]       = "Task"
coach["Resource"]   = "arn:aws:states:::lambda:invoke"
coach["OutputPath"] = "$.Payload"
coach["ResultPath"] = None   # will be cleaned below
if "ResultPath" in coach:
    del coach["ResultPath"]
coach["End"] = True
print("✅ Updated Invoke_ResumeCoach Parameters")

print("\nFinal AggregateResults:", json.dumps(agg, indent=2))
print("\nFinal Invoke_ResumeCoach:", json.dumps(coach, indent=2))

# Push
new_def = json.dumps(definition, separators=(",", ":"))
r = subprocess.run(
    ["aws", "stepfunctions", "update-state-machine",
     "--state-machine-arn", SM_ARN, "--definition", new_def],
    capture_output=True, text=True
)
if r.returncode == 0:
    print("\n✅ State machine updated successfully!")
    print(r.stdout)
else:
    print("\n❌ Error:", r.stderr)