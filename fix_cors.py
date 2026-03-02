import subprocess
import json

API_ID = "frapi46611"
REGION = "us-east-1"
STAGE  = "prod"

CORS_RESPONSE_PARAMS = {
    "method.response.header.Access-Control-Allow-Headers": "'Content-Type,Authorization,X-Api-Key,x-api-key'",
    "method.response.header.Access-Control-Allow-Methods": "'GET,POST,OPTIONS'",
    "method.response.header.Access-Control-Allow-Origin":  "'*'"
}

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  ⚠️  {r.stderr.strip()[:120]}")
    return r

# 1. Get all resources
resources = json.loads(run([
    "aws", "apigateway", "get-resources",
    "--rest-api-id", API_ID, "--region", REGION
]).stdout)["items"]

for res in resources:
    rid   = res["id"]
    path  = res.get("path", "")
    methods = res.get("resourceMethods", {})

    if path == "/" or not methods:
        continue

    if "OPTIONS" in methods:
        print(f"✅ OPTIONS already exists on {path}")
        continue

    print(f"Adding OPTIONS to {path} ({rid})...")

    # Put OPTIONS method — no auth, no API key
    run(["aws", "apigateway", "put-method",
         "--rest-api-id", API_ID, "--resource-id", rid,
         "--http-method", "OPTIONS",
         "--authorization-type", "NONE",
         "--no-api-key-required",
         "--region", REGION])

    # Mock integration
    run(["aws", "apigateway", "put-integration",
         "--rest-api-id", API_ID, "--resource-id", rid,
         "--http-method", "OPTIONS", "--type", "MOCK",
         "--request-templates", json.dumps({"application/json": '{"statusCode":200}'}),
         "--region", REGION])

    # Method response
    run(["aws", "apigateway", "put-method-response",
         "--rest-api-id", API_ID, "--resource-id", rid,
         "--http-method", "OPTIONS", "--status-code", "200",
         "--response-parameters", json.dumps({
             "method.response.header.Access-Control-Allow-Headers": False,
             "method.response.header.Access-Control-Allow-Methods": False,
             "method.response.header.Access-Control-Allow-Origin":  False
         }),
         "--region", REGION])

    # Integration response
    run(["aws", "apigateway", "put-integration-response",
         "--rest-api-id", API_ID, "--resource-id", rid,
         "--http-method", "OPTIONS", "--status-code", "200",
         "--response-parameters", json.dumps(CORS_RESPONSE_PARAMS),
         "--region", REGION])

    print(f"  ✅ Done")

# 2. Redeploy
print("\nRedeploying API...")
r = run(["aws", "apigateway", "create-deployment",
         "--rest-api-id", API_ID, "--stage-name", STAGE, "--region", REGION])
if r.returncode == 0:
    print("✅ API redeployed — CORS preflight should now work!")
else:
    print("❌ Redeploy failed:", r.stderr)