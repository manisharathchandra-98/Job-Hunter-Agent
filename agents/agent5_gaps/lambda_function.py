"""
Agent 5: Skills Gap Identifier
Compares candidate vs job requirements and generates a personalized learning roadmap.
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

WITH_CANDIDATE_PROMPT = """You are a career development coach. Analyze the skills gap.

Return ONLY valid JSON:
{{
  "match_score": number (0–100),
  "match_label": "Poor Fit | Fair Fit | Good Fit | Strong Fit | Excellent Fit",
  "missing_skills": [
    {{
      "name": "string",
      "priority": "critical | important | nice_to_have",
      "estimated_learning_weeks": number,
      "resources": ["2–3 specific courses/platforms"]
    }}
  ],
  "skills_to_improve": [
    {{
      "name": "string",
      "current_level": "junior | mid | senior | expert",
      "required_level": "junior | mid | senior | expert",
      "gap_weeks": number
    }}
  ],
  "matching_skills": ["skills already at required level"],
  "total_preparation_weeks": number,
  "learning_roadmap": [
    {{
      "phase": number,
      "title": "string",
      "duration_weeks": number,
      "focus_skills": ["skills"],
      "milestone": "what candidate achieves"
    }}
  ],
  "recommendation": "1-paragraph actionable advice"
}}

Required Job Skills:
{required_skills}

Candidate Profile:
{candidate_profile}

Job: {job_title} ({seniority}), Difficulty: {difficulty}/10
"""

ROADMAP_ONLY_PROMPT = """You are a career coach. No candidate was provided.
Build a learning roadmap to qualify for this role from scratch (assume 2 yrs general experience).

Return ONLY valid JSON:
{{
  "match_score": null,
  "match_label": "No Candidate Provided",
  "missing_skills": [],
  "skills_to_improve": [],
  "matching_skills": [],
  "total_preparation_weeks": number,
  "learning_roadmap": [
    {{
      "phase": number,
      "title": "string",
      "duration_weeks": number,
      "focus_skills": ["skills"],
      "milestone": "string"
    }}
  ],
  "recommendation": "General preparation strategy"
}}

Role: {job_title} ({seniority})
Required Skills:
{required_skills}
Responsibilities: {responsibilities}
"""


def fmt_skills(skills: list) -> str:
    return "\n".join(
        f"- {s.get('name')} ({s.get('level', 'mid')}, {'PRIMARY' if s.get('is_primary') else 'secondary'})"
        for s in skills
    ) or "not specified"


def fmt_candidate(c: dict) -> str:
    lines = [f"Total Experience: {c.get('experience_years', '?')} years"]
    for s in c.get("skills", []):
        lines.append(f"- {s.get('name')}: {s.get('level', 'mid')} ({s.get('years_experience', '?')} yrs)")
    return "\n".join(lines)


def call_bedrock(prompt: str) -> dict:
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 3000,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
    })
    resp = bedrock.invoke_model(modelId=MODEL_ID, body=body)
    content = json.loads(resp["body"].read())["content"][0]["text"].strip()
    content = re.sub(r"^```(?:json)?\n?", "", content)
    content = re.sub(r"\n?```$", "", content)
    return json.loads(content)


def lambda_handler(event: dict, context) -> dict:
    logger.info("Agent 5 — Skills Gap Identifier invoked")
    parsed = event.get("parsed_job", {})
    skills_analysis = event.get("skills_analysis", {})
    difficulty = event.get("difficulty_score", {})
    candidate = event.get("candidate_profile")

    if not parsed:
        raise ValueError("'parsed_job' missing.")

    skills = skills_analysis.get("skills", [])
    req_skills_str = fmt_skills(skills)
    job_title = parsed.get("job_title", "Unknown")
    seniority = parsed.get("seniority_level", "mid")
    difficulty_score = difficulty.get("score", 5.0)

    if candidate:
        prompt = WITH_CANDIDATE_PROMPT.format(
            job_title=job_title,
            seniority=seniority,
            difficulty=difficulty_score,
            required_skills=req_skills_str,
            candidate_profile=fmt_candidate(candidate),
        )
    else:
        prompt = ROADMAP_ONLY_PROMPT.format(
            job_title=job_title,
            seniority=seniority,
            required_skills=req_skills_str,
            responsibilities="; ".join(parsed.get("key_responsibilities", [])[:5]),
        )

    gap = call_bedrock(prompt)
    logger.info(
        f"Gap: match={gap.get('match_score')}%, "
        f"prep={gap.get('total_preparation_weeks')} weeks, "
        f"roadmap phases={len(gap.get('learning_roadmap', []))}"
    )

    return {**event, "skills_gap": gap, "status": "gaps_identified"}