"""
Aggregator: Final pipeline stage.
Combines all agent outputs, stores in DynamoDB, returns clean API response.
"""
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from decimal import Decimal
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
JOBS_TABLE = os.environ.get("JOBS_TABLE_NAME", "Jobs")


def to_decimal(obj):
    if isinstance(obj, float):
        return Decimal(str(obj))
    if isinstance(obj, dict):
        return {k: to_decimal(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [to_decimal(i) for i in obj]
    return obj


def build_summary(event: dict) -> dict:
    p = event.get("parsed_job", {})
    sa = event.get("skills_analysis", {})
    sd = event.get("salary_data", {})
    d = event.get("difficulty_score", {})
    g = event.get("skills_gap", {})

    return {
        "job_title": p.get("job_title"),
        "company": p.get("company_name"),
        "location": p.get("location"),
        "seniority": p.get("seniority_level"),
        "skills_summary": {
            "total": sa.get("total_skills", 0),
            "primary": sa.get("primary_skills_count", 0),
            "top_skills": [s["name"] for s in sa.get("skills", []) if s.get("is_primary")][:6],
        },
        "salary_summary": {
            "low": sd.get("salary_low"),
            "median": sd.get("salary_median"),
            "high": sd.get("salary_high"),
            "currency": sd.get("currency", "USD"),
            "confidence": sd.get("confidence"),
            "insights": sd.get("market_insights"),
        },
        "difficulty_summary": {
            "score": d.get("score"),
            "label": d.get("label"),
            "learning_curve": d.get("learning_curve"),
            "top_challenges": d.get("top_challenges", []),
        },
        "gap_summary": {
            "match_score": g.get("match_score"),
            "match_label": g.get("match_label"),
            "missing_critical": [
                x["name"] for x in g.get("missing_skills", [])
                if x.get("priority") == "critical"
            ],
            "total_prep_weeks": g.get("total_preparation_weeks"),
        },
    }


def lambda_handler(event: dict, context) -> dict:
    logger.info("Aggregator invoked")
    job_id = event.get("job_id") or str(uuid.uuid4())
    summary = build_summary(event)
    now = datetime.now(timezone.utc).isoformat()

    item = {
        "job_id": job_id,
        "raw_description": event.get("job_description", "")[:3000],
        "parsed_job": event.get("parsed_job", {}),
        "skills_analysis": event.get("skills_analysis", {}),
        "salary_data": event.get("salary_data", {}),
        "difficulty_score": event.get("difficulty_score", {}),
        "skills_gap": event.get("skills_gap", {}),
        "summary": summary,
        "has_candidate": bool(event.get("candidate_profile")),
        "status": "completed",
        "created_at": now,
        "updated_at": now,
        "ttl": int(datetime.now(timezone.utc).timestamp()) + (90 * 86400),
    }

    try:
        dynamodb.Table(JOBS_TABLE).put_item(Item=to_decimal(item))
        stored = True
        logger.info(f"Stored job_id={job_id} in DynamoDB")
    except ClientError as e:
        stored = False
        logger.error(f"DynamoDB store failed: {e}")

    return {
        "job_id": job_id,
        "status": "completed",
        "summary": summary,
        "full_analysis": {
            "parsed_job": event.get("parsed_job", {}),
            "skills_analysis": event.get("skills_analysis", {}),
            "salary_data": event.get("salary_data", {}),
            "difficulty_score": event.get("difficulty_score", {}),
            "skills_gap": event.get("skills_gap", {}),
        },
        "stored_in_db": stored,
    }