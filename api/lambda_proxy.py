import json
import logging
import os
import uuid
from datetime import datetime, timezone
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from decimal import Decimal

logger = logging.getLogger()
logger.setLevel(logging.INFO)

sfn      = boto3.client("stepfunctions", region_name="us-east-1")
dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

STATE_MACHINE_ARN = os.environ.get("STATE_MACHINE_ARN", "")
JOBS_TABLE        = os.environ.get("JOBS_TABLE_NAME", "Jobs")
CANDIDATES_TABLE  = os.environ.get("CANDIDATES_TABLE_NAME", "Candidates")
MATCHES_TABLE     = os.environ.get("MATCHES_TABLE_NAME", "Matches")


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
            "Access-Control-Allow-Headers": "Content-Type,Authorization,X-Api-Key",
        },
        "body": json.dumps(body, default=decimal_default),
    }


def is_running(execution_name: str) -> bool:
    try:
        execs = sfn.list_executions(
            stateMachineArn=STATE_MACHINE_ARN,
            statusFilter="RUNNING",
        )
        return any(e["name"] == execution_name for e in execs["executions"])
    except Exception:
        return False


# ── Jobs ──────────────────────────────────────────────────────────────────────

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
        "job_id":     job_id,
        "status":     "processing",
        "message":    "Job submitted for analysis.",
        "check_url":  f"/prod/jobs/{job_id}",
    })


def get_job(job_id: str) -> dict:
    try:
        res  = dynamodb.Table(JOBS_TABLE).get_item(Key={"job_id": job_id})
        item = res.get("Item")
    except ClientError as e:
        logger.error(f"DynamoDB error: {e}")
        return resp(500, {"error": "Database error."})

    if not item:
        if is_running(f"job-{job_id}"):
            return resp(202, {"job_id": job_id, "status": "processing"})
        return resp(404, {"error": f"Job '{job_id}' not found."})

    item.pop("ttl", None)
    return resp(200, item)


def list_jobs() -> dict:
    try:
        res = dynamodb.Table(JOBS_TABLE).query(
            IndexName="StatusCreatedIndex",
            KeyConditionExpression=Key("status").eq("completed"),
            ScanIndexForward=False,
            Limit=20,
        )
        items = res.get("Items", [])
    except ClientError as e:
        logger.error(f"DynamoDB error: {e}")
        return resp(500, {"error": "Database error."})

    return resp(200, {"jobs": items, "count": len(items)})


# ── Candidates ────────────────────────────────────────────────────────────────

def post_candidate(body: dict) -> dict:
    candidate_id = str(uuid.uuid4())
    now  = datetime.now(timezone.utc).isoformat()
    item = {
        "candidate_id":     candidate_id,
        "name":             body.get("name", "Anonymous"),
        "email":            body.get("email", ""),
        "skills":           body.get("skills", []),
        "experience_years": body.get("experience_years", 0),
        "created_at":       now,
        "updated_at":       now,
    }
    try:
        dynamodb.Table(CANDIDATES_TABLE).put_item(Item=item)
    except ClientError as e:
        logger.error(f"DynamoDB error: {e}")
        return resp(500, {"error": "Failed to save candidate."})

    return resp(201, {"candidate_id": candidate_id, "message": "Candidate profile created."})


def get_candidate(candidate_id: str) -> dict:
    try:
        res  = dynamodb.Table(CANDIDATES_TABLE).get_item(
            Key={"candidate_id": candidate_id}
        )
        item = res.get("Item")
    except ClientError as e:
        logger.error(f"DynamoDB error: {e}")
        return resp(500, {"error": "Database error."})

    if not item:
        return resp(404, {"error": f"Candidate '{candidate_id}' not found."})
    return resp(200, item)


def get_candidate_matches(candidate_id: str) -> dict:
    try:
        res = dynamodb.Table(MATCHES_TABLE).query(
            IndexName="CandidateMatchesIndex",
            KeyConditionExpression=Key("candidate_id").eq(candidate_id),
            ScanIndexForward=False,
            Limit=20,
        )
        items = res.get("Items", [])
    except ClientError as e:
        logger.error(f"DynamoDB error: {e}")
        return resp(500, {"error": "Database error."})

    return resp(200, {
        "candidate_id": candidate_id,
        "matches":      items,
        "count":        len(items),
    })


# ── Match pipeline ────────────────────────────────────────────────────────────

def post_match(body: dict) -> dict:
    resume_text     = body.get("resume_text", "").strip()
    job_description = body.get("job_description", "").strip()

    # ── Validation ────────────────────────────────────────────────────────
    if not resume_text:
        return resp(400, {"error": "'resume_text' is required.", "code": "MISSING_RESUME"})
    if len(resume_text) < 50:
        return resp(400, {"error": "Resume is too short — please paste the full text (min 50 characters).", "code": "RESUME_TOO_SHORT"})
    if len(resume_text) > 25000:
        return resp(400, {"error": "Resume is too long — please trim to under 10,000 characters.", "code": "RESUME_TOO_LONG"})
    if not job_description:
        return resp(400, {"error": "'job_description' is required.", "code": "MISSING_JD"})
    if len(job_description) < 30:
        return resp(400, {"error": "Job description is too short (min 30 characters).", "code": "JD_TOO_SHORT"})
    if len(job_description) > 15000:
        return resp(400, {"error": "Job description is too long — please trim to under 8,000 characters.", "code": "JD_TOO_LONG"})
    # ─────────────────────────────────────────────────────────────────────

    match_id     = str(uuid.uuid4())
    candidate_id = body.get("candidate_id", match_id)
    job_id       = body.get("job_id", "")
    now          = datetime.now(timezone.utc).isoformat()

    # ── Start Step Functions execution ────────────────────────────────────
    sfn_input = {
        "match_id":        match_id,
        "candidate_id":    candidate_id,
        "job_id":          job_id,
        "resume_text":     resume_text,
        "job_description": job_description,
    }

    try:
        sfn_response  = sfn.start_execution(
            stateMachineArn=STATE_MACHINE_ARN,
            name=f"match-{match_id}",
            input=json.dumps(sfn_input),
        )
        execution_arn = sfn_response["executionArn"]
    except ClientError as e:
        logger.error(f"Step Functions failed: {e}")
        return resp(500, {"error": "Failed to start match workflow."})

    # ── Save initial match record immediately (execution_arn preserved) ───
    # aggregator will update_item (not put_item) so execution_arn is never lost.
    # resume_coach (Agent 6) will flip status → "completed" + add resume_suggestions.
    try:
        dynamodb.Table(MATCHES_TABLE).put_item(Item={
            "match_id":     match_id,
            "candidate_id": candidate_id,
            "job_id":       job_id,
            "status":       "processing",
            "execution_arn": execution_arn,
            "created_at":   now,
            "updated_at":   now,
        })
    except ClientError as e:
        logger.warning(f"Could not save initial match record: {e}")

    return resp(202, {
        "match_id":     match_id,
        "candidate_id": candidate_id,
        "status":       "processing",
        "message":      "Match analysis started.",
        "check_url":    f"/prod/matches/{match_id}",
    })


def get_match(match_id: str) -> dict:
    try:
        res  = dynamodb.Table(MATCHES_TABLE).get_item(Key={"match_id": match_id})
        item = res.get("Item")
    except ClientError as e:
        logger.error(f"DynamoDB error: {e}")
        return resp(500, {"error": "Database error."})

    if not item:
        # Record not in DynamoDB yet — check if execution is still running
        if is_running(f"match-{match_id}"):
            return resp(202, {"status": "processing", "match_id": match_id})
        return resp(404, {"error": f"Match '{match_id}' not found."})

    status = item.get("status", "processing")

    # ── Still running ─────────────────────────────────────────────────────
    if status == "processing":
        return resp(202, {"status": "processing", "match_id": match_id})

    # ── Completed ─────────────────────────────────────────────────────────
    # resume_suggestions is written by resume_coach (Agent 6).
    # If somehow missing, degrade gracefully with an empty dict.
    resume_suggestions = item.get("resume_suggestions", {})

    return resp(200, {
        "status":                 "completed",
        "match_id":               match_id,
        "candidate_id":           item.get("candidate_id", ""),
        "match_score":            int(item.get("match_score", 0)),
        "recommendation":         item.get("recommendation", ""),
        "overall_recommendation": item.get("overall_recommendation", ""),
        "score_breakdown":        item.get("score_breakdown", {}),
        "effort_to_match":        item.get("effort_to_match", ""),
        "explanation":            item.get("explanation", ""),
        "job_title_detected":     item.get("job_title_detected", ""),
        "skills_analysis":        item.get("skills_analysis", {}),
        "gaps":                   item.get("gaps", {}),
        "learning_plan":          item.get("learning_plan", {}),
        "salary_insights":        item.get("salary_insights", {}),
        "resume_suggestions":     resume_suggestions,
        "created_at":             item.get("created_at", ""),
    })


# ── Router ────────────────────────────────────────────────────────────────────

def lambda_handler(event: dict, context) -> dict:
    method      = event.get("httpMethod", "GET")
    path        = event.get("path", "/")
    path_params = event.get("pathParameters") or {}

    # Handle CORS preflight — must respond before API key check
    if method == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin":  "*",
                "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type,Authorization,X-Api-Key,x-api-key",
                "Access-Control-Max-Age":       "86400",
            },
            "body": "",
        }

    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return resp(400, {"error": "Invalid JSON body."})

    logger.info(f"{method} {path}")

    # Jobs
    if method == "POST" and path == "/jobs":
        return post_job(body)
    if method == "GET" and path == "/jobs":
        return list_jobs()
    if method == "GET" and path_params.get("job_id"):
        return get_job(path_params["job_id"])

    # Match pipeline
    if method == "POST" and path == "/match":
        return post_match(body)
    if method == "GET" and path_params.get("match_id"):
        return get_match(path_params["match_id"])

    # Candidates — /matches check MUST come before /{candidate_id}
    if method == "POST" and path == "/candidates":
        return post_candidate(body)
    if method == "GET" and path_params.get("candidate_id") and path.endswith("/matches"):
        return get_candidate_matches(path_params["candidate_id"])
    if method == "GET" and path_params.get("candidate_id"):
        return get_candidate(path_params["candidate_id"])

    return resp(404, {"error": f"Route not found: {method} {path}"})