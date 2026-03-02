import subprocess
import json

API_ID = "frapi46611"
REGION = "us-east-1"
STAGE  = "prod"

CORS_PARAMS = {
    "method.response.header.Access-Control-Allow-Headers": "'Content-Type,Authorization,X-Api-Key,x-api-key'",
    "method.response.header.Access-Control-Allow-Methods": "'GET,POST,PUT,DELETE,OPTIONS'",
    "method.response.header.Access-Control-Allow-Origin":  "'*'"
}

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r

# Get all resources
resources = json.loads(run([
    "aws", "apigateway", "get-resources",
    "--rest-api-id", API_ID, "--region", REGION
]).stdout)["items"]

for res in resources:
    rid     = res["id"]
    path    = res.get("path", "")
    methods = res.get("resourceMethods", {})

    if "OPTIONS" not in methods:
        continue

    print(f"Recreating OPTIONS on {path}...")

    # Step 1: Delete existing OPTIONS method
    run(["aws", "apigateway", "delete-method",
         "--rest-api-id", API_ID, "--resource-id", rid,
         "--http-method", "OPTIONS", "--region", REGION])

    # Step 2: Create OPTIONS method (no auth, no API key)
    run(["aws", "apigateway", "put-method",
         "--rest-api-id", API_ID, "--resource-id", rid,
         "--http-method", "OPTIONS",
         "--authorization-type", "NONE",
         "--no-api-key-required",
         "--region", REGION])

    # Step 3: Mock integration
    run(["aws", "apigateway", "put-integration",
         "--rest-api-id", API_ID, "--resource-id", rid,
         "--http-method", "OPTIONS",
         "--type", "MOCK",
         "--request-templates", json.dumps({"application/json": '{"statusCode":200}'}),
         "--region", REGION])

    # Step 4: Method response with CORS headers declared
    run(["aws", "apigateway", "put-method-response",
         "--rest-api-id", API_ID, "--resource-id", rid,
         "--http-method", "OPTIONS",
         "--status-code", "200",
         "--response-parameters", json.dumps({
             "method.response.header.Access-Control-Allow-Headers": False,
             "method.response.header.Access-Control-Allow-Methods": False,
             "method.response.header.Access-Control-Allow-Origin":  False
         }),
         "--region", REGION])

    # Step 5: Integration response with actual CORS header values
    run(["aws", "apigateway", "put-integration-response",
         "--rest-api-id", API_ID, "--resource-id", rid,
         "--http-method", "OPTIONS",
         "--status-code", "200",
         "--response-parameters", json.dumps(CORS_PARAMS),
         "--region", REGION])

    print(f"  ✅ {path} done")

# Redeploy
print("\nRedeploying API...")
r = run(["aws", "apigateway", "create-deployment",
         "--rest-api-id", API_ID, "--stage-name", STAGE, "--region", REGION])
if r.returncode == 0:
    print("✅ API redeployed successfully!")
else:
    print("❌ Redeploy failed:", r.stderr)