"""
Aggregator: Combines all agent outputs into a final match report and stores in DynamoDB.
Runs BEFORE resume_coach (Agent 6), so match status is set to "processing".
resume_coach will flip it to "completed" after adding suggestions.
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
JOBS_TABLE       = os.environ.get("JOBS_TABLE_NAME", "Jobs")
MATCHES_TABLE    = os.environ.get("MATCHES_TABLE_NAME", "Matches")


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

    now          = datetime.now(timezone.utc).isoformat()
    match_id     = event.get("match_id", getattr(context, "aws_request_id", "local"))
    candidate_id = event.get("candidate_id", match_id)
    job_id       = event.get("job_id", "")

    parsed_resume    = event.get("parsed_resume", {})
    extracted_skills = event.get("extracted_skills", {})
    market_analysis  = event.get("market_analysis", {})
    match_result     = event.get("match_result", {})
    gap_analysis     = event.get("gap_analysis", {})

    # ── Build candidate record ──────────────────────────────────────────
    candidate_item = {
        "candidate_id":    candidate_id,
        "created_at":      now,
        "updated_at":      now,
        "name":            parsed_resume.get("name", "Unknown"),
        "email":           parsed_resume.get("email", ""),
        "current_role":    parsed_resume.get("current_role", ""),
        "years_experience": parsed_resume.get("years_experience", 0),
        "education":       parsed_resume.get("education", []),
        "certifications":  parsed_resume.get("certifications", []),
        "work_history":    parsed_resume.get("work_history", []),
        "skills":          extracted_skills.get("skills", []),
        "primary_stack":   extracted_skills.get("primary_stack", []),
        "market_value": {
            "salary_low":    market_analysis.get("salary_low", 0),
            "salary_median": market_analysis.get("salary_median", 0),
            "salary_high":   market_analysis.get("salary_high", 0),
        },
        "market_position":  market_analysis.get("market_position", ""),
        "market_demand":    market_analysis.get("market_demand", ""),
        "best_suited_roles": market_analysis.get("best_suited_roles", []),
        "last_match_id":    match_id,
        "status":           "analyzed",
    }

    # ── Store candidate ─────────────────────────────────────────────────
    try:
        dynamodb.Table(CANDIDATES_TABLE).put_item(Item=float_to_decimal(candidate_item))
        logger.info(f"Stored candidate: {candidate_id}")
    except ClientError as e:
        logger.error(f"Failed to store candidate: {e}")

    # ── Update match record (use update_item to preserve execution_arn) ─
    # post_match() already created the item with execution_arn + status="processing".
    # We add analysis fields here without overwriting execution_arn.
    # status stays "processing" — resume_coach (Agent 6) will set it to "completed".
    match_score = match_result.get("match_score", 0)

    try:
        dynamodb.Table(MATCHES_TABLE).update_item(
            Key={"match_id": match_id},
            UpdateExpression="""SET
                candidate_id            = :cid,
                job_id                  = :jid,
                updated_at              = :ua,
                match_score             = :ms,
                recommendation          = :rec,
                score_breakdown         = :sb,
                effort_to_match         = :etm,
                explanation             = :exp,
                job_title_detected      = :jtd,
                skills_analysis         = :sa,
                gaps                    = :gaps,
                learning_plan           = :lp,
                overall_recommendation  = :or_rec,
                salary_insights         = :si
            """,
            ExpressionAttributeValues=float_to_decimal({
                ":cid":    candidate_id,
                ":jid":    job_id,
                ":ua":     now,
                ":ms":     match_score,
                ":rec":    match_result.get("recommendation", ""),
                ":sb":     match_result.get("score_breakdown", {}),
                ":etm":    match_result.get("effort_to_match", ""),
                ":exp":    match_result.get("explanation", ""),
                ":jtd":    match_result.get("job_title_detected", ""),
                ":sa":     gap_analysis.get("skills_analysis", {}),
                ":gaps":   gap_analysis.get("gaps", {}),
                ":lp":     gap_analysis.get("learning_plan", {}),
                ":or_rec": gap_analysis.get("overall_recommendation", ""),
                ":si": {
                    "candidate_market_value":       market_analysis.get("salary_median", 0),
                    "market_position":              market_analysis.get("market_position", ""),
                    "earning_potential_6months":    market_analysis.get("earning_potential_6months", 0),
                    "market_insight":               market_analysis.get("market_insight", ""),
                },
            })
        )
        logger.info(f"Updated match record: {match_id} (status=processing, awaiting resume coach)")
    except ClientError as e:
        logger.warning(f"Could not update match record: {e}")

    logger.info(
        f"Aggregation complete. Score: {match_score}% — "
        f"{match_result.get('recommendation')}"
    )

    # This return value becomes $.aggregator_result in Step Functions,
    # passed directly into resume_coach (Agent 6).
    return {
        "match_id":              match_id,
        "candidate_id":          candidate_id,
        "job_id":                job_id,
        "match_score":           match_score,
        "recommendation":        match_result.get("recommendation", ""),
        "overall_recommendation": gap_analysis.get("overall_recommendation", ""),
        "status":                "processing",
        "created_at":            now,
    }