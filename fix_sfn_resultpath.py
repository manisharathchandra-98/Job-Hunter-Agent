import subprocess
import json

SM_ARN = "arn:aws:states:us-east-1:596432516213:stateMachine:JobAnalyzerWorkflow"

# Fetch current definition
result = subprocess.run(
    ["aws", "stepfunctions", "describe-state-machine", "--state-machine-arn", SM_ARN],
    capture_output=True, text=True
)
definition = json.loads(json.loads(result.stdout)["definition"])

# Show current AggregateResults config
agg = definition["States"]["AggregateResults"]
print("Before:", json.dumps(agg, indent=2))

# Add ResultPath so aggregator output is stored at $.aggregator_result
# instead of replacing the entire state (which loses resume_text, job_description etc.)
agg["ResultPath"] = "$.aggregator_result"

print("\nAfter:", json.dumps(agg, indent=2))

# Push updated definition
new_def = json.dumps(definition, separators=(",", ":"))
r = subprocess.run(
    ["aws", "stepfunctions", "update-state-machine",
     "--state-machine-arn", SM_ARN,
     "--definition", new_def],
    capture_output=True, text=True
)

if r.returncode == 0:
    print("\n✅ State machine updated — AggregateResults now uses ResultPath: $.aggregator_result")
    print(r.stdout)
else:
    print("\n❌ Error:", r.stderr)