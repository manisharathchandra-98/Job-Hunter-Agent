"""
Agent 6 — Resume Coach
Generates specific, copy-paste-ready resume improvements based on all prior gap analyses.
Writes resume_suggestions to DynamoDB and flips match status → "completed".
"""
import json
import logging
import os
import re
import boto3
from datetime import datetime, timezone
from decimal import Decimal
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

bedrock  = boto3.client("bedrock-runtime", region_name="us-east-1")
dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0")
MATCHES_TABLE = os.environ.get("MATCHES_TABLE_NAME", "Matches")

# RAG retriever is optional — only active once OpenSearch is set up.
try:
    from rag.retriever import retrieve_similar_resumes
    RAG_ENABLED = True
except ImportError:
    RAG_ENABLED = False
    logger.info("RAG module not available — running without similar-resume examples.")


def lambda_handler(event: dict, context) -> dict:
    logger.info("Resume Coach (Agent 6) — Generating resume improvement suggestions")

    match_id     = event.get("match_id", getattr(context, "aws_request_id", "local"))
    resume_text     = event.get("resume_text", "")
    job_description = event.get("job_description", "")

    # Outputs from previous agents (passed via Step Functions ResultPath)
    skills_result     = event.get("skills_result", {})
    experience_result = event.get("experience_result", {})
    culture_result    = event.get("culture_result", {})
    aggregator_result = event.get("aggregator_result", {})

    # ── Optional RAG: fetch similar high-scoring resumes as examples ──────
    rag_context = ""
    if RAG_ENABLED:
        try:
            similar = retrieve_similar_resumes(resume_text, top_k=3)
            rag_context = _format_rag_examples(similar)
            logger.info(f"RAG: retrieved {len(similar)} similar resume examples")
        except Exception as e:
            logger.warning(f"RAG retrieval failed (non-fatal): {e}")

    # ── Call Bedrock ──────────────────────────────────────────────────────
    prompt = _build_prompt(
        resume_text, job_description,
        skills_result, experience_result,
        culture_result, aggregator_result,
        rag_context
    )

    try:
        response = bedrock.invoke_model(
            modelId=MODEL_ID,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 4096,
                "messages": [{"role": "user", "content": prompt}]
            })
        )
        body     = json.loads(response["body"].read())
        raw_text = body["content"][0]["text"]
        result   = _extract_json(raw_text)
        logger.info("Resume Coach — Bedrock response received and parsed")
    except Exception as e:
        logger.error(f"Bedrock call failed: {e}")
        result = {"error": str(e)}

    # ── Persist to DynamoDB + flip status → "completed" ──────────────────
    now = datetime.now(timezone.utc).isoformat()
    try:
        dynamodb.Table(MATCHES_TABLE).update_item(
            Key={"match_id": match_id},
            UpdateExpression="""SET
                resume_suggestions = :rs,
                #st                = :completed,
                updated_at         = :ua
            """,
            ExpressionAttributeNames={"#st": "status"},
            ExpressionAttributeValues={
                ":rs":        _sanitise_for_dynamo(result),
                ":completed": "completed",
                ":ua":        now,
            }
        )
        logger.info(f"Match {match_id} → status=completed, resume_suggestions stored")
    except ClientError as e:
        logger.error(f"Failed to update DynamoDB with resume suggestions: {e}")

    return {
        "statusCode":         200,
        "match_id":           match_id,
        "resume_suggestions": result,
    }


# ── Prompt builder ────────────────────────────────────────────────────────────

def _build_prompt(resume, jd, skills, experience, culture, aggregator, rag_context=""):
    missing_skills = skills.get("missing_skills", [])
    skills_gaps    = skills.get("gaps", [])
    exp_gaps       = experience.get("gaps", [])
    culture_gaps   = culture.get("gaps", [])
    match_score    = aggregator.get("match_score", "N/A")
    recommendation = aggregator.get("overall_recommendation", "")

    rag_section = f"""
---
SIMILAR HIGH-SCORING RESUME EXAMPLES (use as inspiration — do not copy directly):
{rag_context}
""" if rag_context else ""

    current_score = match_score if isinstance(match_score, (int, float)) else 0

    return f"""You are a senior resume coach and career strategist.

The candidate's resume scored {match_score}/100 for the job below.
Your job is to provide specific, copy-paste-ready resume improvements that directly address each identified gap.

---
CURRENT RESUME:
{resume[:3000]}

---
JOB DESCRIPTION:
{jd[:2000]}

---
GAP ANALYSIS:
- Missing Technical Skills : {json.dumps(missing_skills)}
- Skills Gaps              : {json.dumps(skills_gaps)}
- Experience Gaps          : {json.dumps(exp_gaps)}
- Culture / Soft Skill Gaps: {json.dumps(culture_gaps)}
- Overall Recommendation   : {recommendation}
{rag_section}
---
Return a JSON object with EXACTLY this structure (no markdown, no explanation outside JSON):

{{
  "priority_changes": [
    {{
      "priority": "HIGH | MEDIUM | LOW",
      "section": "SUMMARY | SKILLS | EXPERIENCE | EDUCATION | CERTIFICATIONS",
      "issue": "what gap or weakness this addresses",
      "action": "ADD | REWRITE | REMOVE | REORDER",
      "current_text": "exact current text, or null if adding new content",
      "suggested_text": "exact replacement or new text to add",
      "reason": "why this change improves the fit score"
    }}
  ],
  "keywords_to_add": [
    {{
      "keyword": "exact keyword or phrase from the job description",
      "frequency_in_jd": "high | medium | low",
      "suggested_placement": "Skills section / Experience bullet / Summary",
      "example_usage": "sentence showing natural incorporation"
    }}
  ],
  "bullet_rewrites": [
    {{
      "original": "exact original bullet point from resume",
      "rewritten": "stronger version with action verb, scope, and quantified impact",
      "improvement_type": "added metric | stronger verb | added relevance | added scope"
    }}
  ],
  "new_bullets_to_add": [
    {{
      "target_role_or_project": "which experience entry to add it under",
      "bullet": "new bullet point that bridges a specific gap",
      "gap_addressed": "which gap from the analysis this covers"
    }}
  ],
  "summary_rewrite": {{
    "original": "current summary from resume, or null",
    "suggested": "optimised 2-3 sentence professional summary for this exact role",
    "ats_keywords_included": ["keyword1", "keyword2", "keyword3"]
  }},
  "skills_section_rewrite": {{
    "add": ["skill1", "skill2"],
    "remove": ["irrelevant skill1"],
    "reorder_advice": "put X, Y first — they match primary JD requirements"
  }},
  "estimated_score_after_changes": {{
    "current_score": {current_score},
    "projected_score": 0,
    "improvement_breakdown": {{
      "keywords": "+X points",
      "bullet_quality": "+X points",
      "skills_alignment": "+X points"
    }}
  }},
  "overall_strategy": "3-4 sentence strategic advice for this specific application"
}}
"""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _format_rag_examples(similar_resumes: list) -> str:
    if not similar_resumes:
        return ""
    lines = []
    for i, r in enumerate(similar_resumes, 1):
        lines.append(
            f"Example {i} (Match Score: {r['match_score']}, Role: {r['job_title']}):\n"
            f"{r.get('bullet_examples', '')}\n"
        )
    return "\n".join(lines)


def _extract_json(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                pass
    return {"error": "Failed to parse agent response", "raw": text[:500]}


def _sanitise_for_dynamo(obj):
    """Recursively convert floats → Decimal and strip empty strings for DynamoDB."""
    if isinstance(obj, float):
        return Decimal(str(obj))
    elif isinstance(obj, dict):
        return {k: _sanitise_for_dynamo(v) for k, v in obj.items() if v != ""}
    elif isinstance(obj, list):
        return [_sanitise_for_dynamo(i) for i in obj]
    return obj