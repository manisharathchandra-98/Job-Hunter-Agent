import json
import logging
import os
import uuid
from datetime import datetime, timezone
import boto3
from botocore.exceptions import ClientError
from decimal import Decimal

logger = logging.getLogger()
logger.setLevel(logging.INFO)

sfn = boto3.client("stepfunctions", region_name="us-east-1")
dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

STATE_MACHINE_ARN = os.environ.get("STATE_MACHINE_ARN", "")
JOBS_TABLE = os.environ.get("JOBS_TABLE_NAME", "Jobs")
CANDIDATES_TABLE = os.environ.get("CANDIDATES_TABLE_NAME", "Candidates")


def decimal_default(obj):
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    raise TypeError

def resp(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
        },
        "body": json.dumps(body, default=decimal_default),
    }


def post_job(body: dict) -> dict:
    description = body.get("description", "").strip()
    if not description:
        return resp(400, {"error": "'description' field is required."})

    job_id = str(uuid.uuid4())
    candidate_profile = None

    candidate_id = body.get("candidate_id")
    if candidate_id:
        try:
            res = dynamodb.Table(CANDIDATES_TABLE).get_item(
                Key={"candidate_id": candidate_id}
            )
            candidate_profile = res.get("Item")
        except ClientError as e:
            logger.warning(f"Could not fetch candidate: {e}")

    sfn_input = {"job_id": job_id, "job_description": description}
    if candidate_profile:
        sfn_input["candidate_profile"] = candidate_profile

    try:
        sfn.start_execution(
            stateMachineArn=STATE_MACHINE_ARN,
            name=f"job-{job_id}",
            input=json.dumps(sfn_input),
        )
    except ClientError as e:
        logger.error(f"Step Functions failed: {e}")
        return resp(500, {"error": "Failed to start analysis workflow."})

    return resp(202, {
        "job_id": job_id,
        "status": "processing",
        "message": "Job submitted for analysis.",
        "check_url": f"/prod/jobs/{job_id}",
    })


def get_job(job_id: str) -> dict:
    try:
        res = dynamodb.Table(JOBS_TABLE).get_item(Key={"job_id": job_id})
        item = res.get("Item")
    except ClientError as e:
        logger.error(f"DynamoDB error: {e}")
        return resp(500, {"error": "Database error."})

    if not item:
        try:
            executions = sfn.list_executions(
                stateMachineArn=STATE_MACHINE_ARN,
                statusFilter="RUNNING",
            )
            running = [e for e in executions["executions"]
                      if e["name"] == f"job-{job_id}"]
            if running:
                return resp(202, {"job_id": job_id, "status": "processing"})
        except Exception:
            pass
        return resp(404, {"error": f"Job '{job_id}' not found."})

    item.pop("ttl", None)
    return resp(200, item)


def list_jobs() -> dict:
    try:
        res = dynamodb.Table(JOBS_TABLE).query(
            IndexName="StatusCreatedIndex",
            KeyConditionExpression=boto3.dynamodb.conditions.Key("status").eq("completed"),
            ScanIndexForward=False,
            Limit=20,
        )
        items = res.get("Items", [])
    except ClientError as e:
        logger.error(f"DynamoDB error: {e}")
        return resp(500, {"error": "Database error."})

    return resp(200, {"jobs": items, "count": len(items)})


def post_candidate(body: dict) -> dict:
    candidate_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    item = {
        "candidate_id": candidate_id,
        "name": body.get("name", "Anonymous"),
        "email": body.get("email", ""),
        "skills": body.get("skills", []),
        "experience_years": body.get("experience_years", 0),
        "created_at": now,
        "updated_at": now,
    }
    try:
        dynamodb.Table(CANDIDATES_TABLE).put_item(Item=item)
    except ClientError as e:
        logger.error(f"DynamoDB error: {e}")
        return resp(500, {"error": "Failed to save candidate."})

    return resp(201, {
        "candidate_id": candidate_id,
        "message": "Candidate profile created.",
    })


def lambda_handler(event: dict, context) -> dict:
    method = event.get("httpMethod", "GET")
    path = event.get("path", "/")
    path_params = event.get("pathParameters") or {}

    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return resp(400, {"error": "Invalid JSON body."})

    logger.info(f"{method} {path}")

    if method == "POST" and path == "/jobs":
        return post_job(body)
    if method == "GET" and path == "/jobs":
        return list_jobs()
    if method == "GET" and path_params.get("job_id"):
        return get_job(path_params["job_id"])
    if method == "POST" and path == "/candidates":
        return post_candidate(body)

    return resp(404, {"error": f"Route not found: {method} {path}"})