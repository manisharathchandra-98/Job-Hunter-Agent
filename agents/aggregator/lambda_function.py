"""
Aggregator: Combines all agent outputs into a final match report and stores in DynamoDB.
"""
import json
import logging
import os
import boto3
from datetime import datetime, timezone
from decimal import Decimal
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
CANDIDATES_TABLE = os.environ.get("CANDIDATES_TABLE_NAME", "Candidates")
JOBS_TABLE = os.environ.get("JOBS_TABLE_NAME", "Jobs")
MATCHES_TABLE = os.environ.get("MATCHES_TABLE_NAME", "Matches")


def float_to_decimal(obj):
    """Recursively convert floats to Decimal for DynamoDB."""
    if isinstance(obj, float):
        return Decimal(str(obj))
    elif isinstance(obj, dict):
        return {k: float_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [float_to_decimal(i) for i in obj]
    return obj


def lambda_handler(event: dict, context) -> dict:
    logger.info("Aggregator — Combining all agent outputs")

    now = datetime.now(timezone.utc).isoformat()
    match_id = event.get("match_id", getattr(context, "aws_request_id", "local"))
    candidate_id = event.get("candidate_id", match_id)
    job_id = event.get("job_id", "")

    parsed_resume = event.get("parsed_resume", {})
    extracted_skills = event.get("extracted_skills", {})
    market_analysis = event.get("market_analysis", {})
    match_result = event.get("match_result", {})
    gap_analysis = event.get("gap_analysis", {})

    # ── Build candidate record ──────────────────────────────────────────
    candidate_item = {
        "candidate_id": candidate_id,
        "created_at": now,
        "updated_at": now,
        "name": parsed_resume.get("name", "Unknown"),
        "email": parsed_resume.get("email", ""),
        "current_role": parsed_resume.get("current_role", ""),
        "years_experience": parsed_resume.get("years_experience", 0),
        "education": parsed_resume.get("education", []),
        "certifications": parsed_resume.get("certifications", []),
        "work_history": parsed_resume.get("work_history", []),
        "skills": extracted_skills.get("skills", []),
        "primary_stack": extracted_skills.get("primary_stack", []),
        "market_value": {
            "salary_low": market_analysis.get("salary_low", 0),
            "salary_median": market_analysis.get("salary_median", 0),
            "salary_high": market_analysis.get("salary_high", 0),
        },
        "market_position": market_analysis.get("market_position", ""),
        "market_demand": market_analysis.get("market_demand", ""),
        "best_suited_roles": market_analysis.get("best_suited_roles", []),
        "last_match_id": match_id,
        "status": "analyzed",
    }

    # ── Build match record ──────────────────────────────────────────────
    match_item = {
        "match_id": match_id,
        "created_at": now,
        "updated_at": now,
        "candidate_id": candidate_id,
        "job_id": job_id,
        "match_score": match_result.get("match_score", 0),
        "recommendation": match_result.get("recommendation", ""),
        "score_breakdown": match_result.get("score_breakdown", {}),
        "effort_to_match": match_result.get("effort_to_match", ""),
        "explanation": match_result.get("explanation", ""),
        "job_title_detected": match_result.get("job_title_detected", ""),
        "skills_analysis": gap_analysis.get("skills_analysis", {}),
        "gaps": gap_analysis.get("gaps", {}),
        "learning_plan": gap_analysis.get("learning_plan", {}),
        "overall_recommendation": gap_analysis.get("overall_recommendation", ""),
        "salary_insights": {
            "candidate_market_value": market_analysis.get("salary_median", 0),
            "market_position": market_analysis.get("market_position", ""),
            "earning_potential_6months": market_analysis.get("earning_potential_6months", 0),
            "market_insight": market_analysis.get("market_insight", ""),
        },
        "status": "completed",
    }

    # ── Store candidate ─────────────────────────────────────────────────
    try:
        dynamodb.Table(CANDIDATES_TABLE).put_item(Item=float_to_decimal(candidate_item))
        logger.info(f"Stored candidate: {candidate_id}")
    except ClientError as e:
        logger.error(f"Failed to store candidate: {e}")

    # ── Store match ─────────────────────────────────────────────────────
    try:
        dynamodb.Table(MATCHES_TABLE).put_item(Item=float_to_decimal(match_item))
        logger.info(f"Stored match: {match_id}")
    except ClientError as e:
        logger.warning(f"Could not store match (Matches table may not exist yet): {e}")

    logger.info(f"Aggregation complete. Score: {match_result.get('match_score')}% — "
                f"{match_result.get('recommendation')}")

    return {
        "match_id": match_id,
        "candidate_id": candidate_id,
        "job_id": job_id,
        "match_score": match_result.get("match_score", 0),
        "recommendation": match_result.get("recommendation", ""),
        "overall_recommendation": gap_analysis.get("overall_recommendation", ""),
        "status": "completed",
        "created_at": now,
    }