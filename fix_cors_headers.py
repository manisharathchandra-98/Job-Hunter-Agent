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

    print(f"Updating OPTIONS headers on {path}...")

    # Update method response to expose the 3 CORS headers
    run(["aws", "apigateway", "update-method-response",
         "--rest-api-id", API_ID, "--resource-id", rid,
         "--http-method", "OPTIONS", "--status-code", "200",
         "--patch-operations",
         "op=add,path=/responseParameters/method.response.header.Access-Control-Allow-Headers,value=false",
         "op=add,path=/responseParameters/method.response.header.Access-Control-Allow-Methods,value=false",
         "op=add,path=/responseParameters/method.response.header.Access-Control-Allow-Origin,value=false",
         "--region", REGION])

    # Update integration response with correct header values
    run(["aws", "apigateway", "update-integration-response",
         "--rest-api-id", API_ID, "--resource-id", rid,
         "--http-method", "OPTIONS", "--status-code", "200",
         "--patch-operations",
         f"op=replace,path=/responseParameters/method.response.header.Access-Control-Allow-Headers,value=\"'Content-Type,Authorization,X-Api-Key,x-api-key'\"",
         f"op=replace,path=/responseParameters/method.response.header.Access-Control-Allow-Methods,value=\"'GET,POST,OPTIONS'\"",
         f"op=replace,path=/responseParameters/method.response.header.Access-Control-Allow-Origin,value=\"'*'\"",
         "--region", REGION])

    print(f"  ✅ {path} updated")

# Redeploy
print("\nRedeploying API...")
r = run(["aws", "apigateway", "create-deployment",
         "--rest-api-id", API_ID, "--stage-name", STAGE, "--region", REGION])
if r.returncode == 0:
    print("✅ API redeployed — X-Api-Key now allowed in CORS preflight!")
else:
    print("❌ Redeploy failed:", r.stderr)