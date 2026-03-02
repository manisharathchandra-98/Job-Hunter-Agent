"""
Agent 6 — Resume Coach with RAG grounding from OpenSearch knowledge base.
"""
import os
import json
import re
import boto3
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

REGION          = os.environ.get("AWS_REGION", "us-east-1")
MODEL_ID        = os.environ.get("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0")
DYNAMO_TABLE = os.environ.get("MATCHES_TABLE_NAME", os.environ.get("DYNAMODB_TABLE", "Matches"))
USE_RAG         = os.environ.get("USE_RAG", "true").lower() == "true"

bedrock  = boto3.client("bedrock-runtime", region_name=REGION)
dynamodb = boto3.resource("dynamodb", region_name=REGION)
table    = dynamodb.Table(DYNAMO_TABLE)

# ── RAG import (optional) ──────────────────────────────────────────────────
_retriever = None
if USE_RAG:
    try:
        from rag.retriever import retrieve_career_context
        _retriever = retrieve_career_context
        logger.info("RAG retriever loaded successfully")
    except ImportError as e:
        logger.warning("RAG retriever not available: %s", e)


def lambda_handler(event, context):
    logger.info("Resume Coach event: %s", json.dumps(event)[:500])

    try:
        # ── Extract inputs ──────────────────────────────────────────
        resume_text  = event.get("resume_text", "")
        jd_text      = event.get("jd_text", "")
        match_id     = event.get("match_id", "")
        overall_score = event.get("overall_score", 0)
        skill_gaps   = event.get("skill_gaps", [])
        job_title    = event.get("job_title", "Software Engineer")
        required_skills = event.get("required_skills", [])

        if not resume_text or not jd_text or not match_id:
            raise ValueError("Missing required fields: resume_text, jd_text, match_id")

        # ── RAG: retrieve role-specific context ─────────────────────
        rag_context = ""
        if _retriever and required_skills:
            rag_context = _retriever(job_title, required_skills)
            if rag_context:
                logger.info("RAG context retrieved (%d chars)", len(rag_context))

        # ── Build prompt ────────────────────────────────────────────
        prompt = _build_prompt(
            resume_text, jd_text, overall_score, skill_gaps, rag_context
        )

        # ── Call Bedrock ────────────────────────────────────────────
        suggestions = _call_bedrock(prompt)

        # ── Persist to DynamoDB ─────────────────────────────────────
        _save_suggestions(match_id, suggestions)

        return {
            "match_id": match_id,
            "resume_suggestions": suggestions,
            "rag_used": bool(rag_context),
            "status": "completed"
        }

    except Exception as e:
        logger.error("Resume Coach failed: %s", str(e), exc_info=True)
        _save_error(event.get("match_id", ""), str(e))
        raise


def _build_prompt(resume_text, jd_text, overall_score, skill_gaps, rag_context=""):
    rag_section = ""
    if rag_context:
        rag_section = f"""
## Career Knowledge Base (Role-Specific Guidance)
The following expert career guidance is relevant to this role. Use it to make your
suggestions more specific and grounded:

{rag_context}

---
"""

    gaps_str = "\n".join(f"- {g}" for g in skill_gaps[:10]) if skill_gaps else "- No major gaps identified"

    return f"""You are an expert resume coach and career advisor with 15+ years of experience
helping software engineers land senior roles at top tech companies.

{rag_section}
## Current Situation
Current fit score: {overall_score}/100
Identified skill gaps:
{gaps_str}

## Job Description
{jd_text[:3000]}

## Current Resume
{resume_text[:4000]}

## Your Task
Analyze the resume against the job description and provide highly specific, actionable
improvement suggestions. Be concrete — don't say "add more details", say exactly WHAT to add.

Return ONLY a valid JSON object with exactly these keys:

{{
  "ScoreProjection": {{
    "current_score": {overall_score},
    "projected_score": <number 0-100>,
    "improvement_delta": <projected - current>,
    "confidence": "High|Medium|Low"
  }},
  "PriorityChanges": [
    {{"rank": 1, "change": "<specific change>", "impact": "High|Medium|Low", "effort": "Low|Medium|High"}},
    {{"rank": 2, "change": "<specific change>", "impact": "High|Medium|Low", "effort": "Low|Medium|High"}},
    {{"rank": 3, "change": "<specific change>", "impact": "High|Medium|Low", "effort": "Low|Medium|High"}}
  ],
  "KeywordsToAdd": [
    {{"keyword": "<exact keyword from JD>", "context": "<where to add it in resume>"}},
    ...
  ],
  "BulletRewrites": [
    {{"original": "<existing bullet>", "improved": "<rewritten bullet with metrics>", "reason": "<why this is better>"}},
    ...
  ],
  "NewBullets": [
    "<new bullet point to add based on gaps>",
    ...
  ],
  "SummaryRewrite": "<full rewritten professional summary tailored to this JD>",
  "SkillsSectionRewrite": "<full rewritten skills section with missing keywords added>",
  "OverallStrategy": "<2-3 sentences of high-level positioning advice>"
}}

Return ONLY the JSON, no markdown, no explanation."""


def _call_bedrock(prompt: str) -> dict:
    try:
        response = bedrock.converse(
            modelId=MODEL_ID,
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"temperature": 0.3, "maxTokens": 3000}
        )
        raw = response["output"]["message"]["content"][0]["text"].strip()
        logger.info("Bedrock response length: %d chars", len(raw))

        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)

        return json.loads(raw)

    except json.JSONDecodeError as e:
        logger.error("Failed to parse Bedrock JSON: %s", str(e))
        return {"error": f"JSON parse error: {str(e)}", "raw": raw[:500]}
    except Exception as e:
        logger.error("Bedrock call failed: %s", str(e))
        return {"error": str(e)}


def _sanitise_for_dynamo(obj):
    if isinstance(obj, dict):
        return {k: _sanitise_for_dynamo(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitise_for_dynamo(i) for i in obj]
    if isinstance(obj, set):
        return [_sanitise_for_dynamo(i) for i in obj]
    if obj is None:
        return ""
    return obj


def _save_suggestions(match_id: str, suggestions: dict):
    table.update_item(
        Key={"match_id": match_id},
        UpdateExpression="SET resume_suggestions = :s, #st = :c, rag_enabled = :r",
        ExpressionAttributeNames={"#st": "status"},
        ExpressionAttributeValues={
            ":s": _sanitise_for_dynamo(suggestions),
            ":c": "completed",
            ":r": bool(_retriever)
        }
    )
    logger.info("Saved suggestions for match_id: %s", match_id)


def _save_error(match_id: str, error_msg: str):
    if not match_id:
        return
    try:
        table.update_item(
            Key={"match_id": match_id},
            UpdateExpression="SET resume_suggestions = :s, #st = :c",
            ExpressionAttributeNames={"#st": "status"},
            ExpressionAttributeValues={
                ":s": {"error": error_msg},
                ":c": "failed"
            }
        )
    except Exception:
        pass
