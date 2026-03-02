import subprocess
import json

SM_ARN = "arn:aws:states:us-east-1:596432516213:stateMachine:JobAnalyzerWorkflow"
RESUME_COACH_ARN = "arn:aws:lambda:us-east-1:596432516213:function:job-analyzer-agent-resume-coach"

# 1. Fetch current definition
result = subprocess.run(
    ["aws", "stepfunctions", "describe-state-machine", "--state-machine-arn", SM_ARN],
    capture_output=True, text=True
)
sm         = json.loads(result.stdout)
definition = json.loads(sm["definition"])

print("Current states:", list(definition["States"].keys()))

# 2. Patch AggregateResults — remove End, add Next
definition["States"]["AggregateResults"].pop("End", None)
definition["States"]["AggregateResults"]["Next"] = "Invoke_ResumeCoach"

# 3. Add / overwrite Invoke_ResumeCoach with correct config
definition["States"]["Invoke_ResumeCoach"] = {
    "Type": "Task",
    "Resource": RESUME_COACH_ARN,
    "Parameters": {
        "match_id.$":          "$.match_id",
        "resume_text.$":       "$.resume_text",
        "job_description.$":   "$.job_description",
        "skills_result.$":     "$.parallel_results[0]",
        "experience_result.$": "$.parallel_results[1]",
        "culture_result.$":    "$.parallel_results[2]",
        "aggregator_result.$": "$.aggregator_result"
    },
    "ResultPath": "$.coach_result",
    "End": True
}

print("Updated states:", list(definition["States"].keys()))

# 4. Serialize with proper quoting and push to AWS
new_def = json.dumps(definition, separators=(",", ":"))

update = subprocess.run(
    ["aws", "stepfunctions", "update-state-machine",
     "--state-machine-arn", SM_ARN,
     "--definition", new_def],
    capture_output=True, text=True
)

if update.returncode == 0:
    print("✅ State machine updated successfully!")
    print(update.stdout)
else:
    print("❌ Error:")
    print(update.stderr)