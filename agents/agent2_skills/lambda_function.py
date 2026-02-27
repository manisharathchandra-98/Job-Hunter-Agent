"""
Agent 2: Skill Level Estimator
Classifies each skill by level, category, and market demand.
"""
import json
import logging
import os
import re
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")
MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"

PROMPT = """You are a senior technical recruiter.
Classify each skill for the role described below.

Return ONLY a JSON array:
[
  {{
    "name": "skill name",
    "level": "junior | mid | senior | expert",
    "category": "language | framework | cloud | devops | database | soft | domain | tool",
    "years_required": number or null,
    "market_demand": "low | medium | high | very_high",
    "is_primary": true or false
  }}
]

Job Context:
- Title: {job_title}
- Seniority: {seniority}
- Experience Required: {years_exp} years
- Required Skills: {required_skills}
- Nice-to-Have: {nice_to_have}
- Responsibilities: {responsibilities}
"""


def call_bedrock(prompt: str) -> list:
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 3000,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
    })
    resp = bedrock.invoke_model(modelId=MODEL_ID, body=body)
    content = json.loads(resp["body"].read())["content"][0]["text"].strip()
    content = re.sub(r"^```(?:json)?\n?", "", content)
    content = re.sub(r"\n?```$", "", content)
    return json.loads(content)


def lambda_handler(event: dict, context) -> dict:
    logger.info("Agent 2 — Skill Estimator invoked")
    parsed = event.get("parsed_job", {})
    if not parsed:
        raise ValueError("'parsed_job' missing. Agent 1 must run first.")

    years_min = parsed.get("years_experience_min") or 0
    years_max = parsed.get("years_experience_max") or years_min
    years_exp = f"{years_min}–{years_max}" if years_max else str(years_min or "not specified")

    prompt = PROMPT.format(
        job_title=parsed.get("job_title", "Unknown"),
        seniority=parsed.get("seniority_level", "unknown"),
        years_exp=years_exp,
        required_skills=", ".join(parsed.get("required_skills", [])) or "not listed",
        nice_to_have=", ".join(parsed.get("nice_to_have_skills", [])) or "none",
        responsibilities="; ".join(parsed.get("key_responsibilities", [])[:5]) or "not listed",
    )

    skills = call_bedrock(prompt)

    # Validate each skill
    valid_levels = {"junior", "mid", "senior", "expert"}
    valid_cats = {"language", "framework", "cloud", "devops", "database", "soft", "domain", "tool"}
    for s in skills:
        if s.get("level") not in valid_levels:
            s["level"] = "mid"
        if s.get("category") not in valid_cats:
            s["category"] = "tool"
        s["is_primary"] = bool(s.get("is_primary", False))

    primary_count = sum(1 for s in skills if s["is_primary"])
    high_demand = sum(1 for s in skills if s.get("market_demand") in {"high", "very_high"})

    logger.info(f"Skills: total={len(skills)}, primary={primary_count}, high_demand={high_demand}")

    return {
        **event,
        "skills_analysis": {
            "skills": skills,
            "total_skills": len(skills),
            "primary_skills_count": primary_count,
            "high_demand_skills_count": high_demand,
        },
        "status": "skills_estimated",
    }