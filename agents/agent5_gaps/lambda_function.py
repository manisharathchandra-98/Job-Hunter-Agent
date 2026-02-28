"""
Agent 5: Skills Gap Analyzer & Learning Planner
Identifies skill gaps between candidate and job, creates personalized learning plan.
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

PROMPT = """You are a career coach and learning strategist specializing in tech careers.

CANDIDATE SKILLS:
{skills_list}

JOB DESCRIPTION:
{job_description}

MATCH SCORE: {match_score}%

Analyze the skills gap and create a personalized learning plan.

Return ONLY valid JSON:
{{
  "skills_analysis": {{
    "matched_skills": [
      {{"name": "string", "candidate_level": "string", "job_required": "string"}}
    ],
    "partial_skills": [
      {{"name": "string", "candidate_level": "string", "job_required": "string", "gap": "string"}}
    ],
    "missing_skills": [
      {{"name": "string", "job_required": "string", "importance": "critical | important | nice_to_have"}}
    ]
  }},
  "gaps": {{
    "critical": [
      {{
        "skill": "string",
        "importance": "critical",
        "learning_time_weeks": number,
        "resources": ["string"]
      }}
    ],
    "important": [
      {{
        "skill": "string",
        "importance": "important",
        "learning_time_weeks": number,
        "resources": ["string"]
      }}
    ],
    "nice_to_have": [
      {{
        "skill": "string",
        "importance": "nice_to_have",
        "learning_time_weeks": number,
        "resources": ["string"]
      }}
    ]
  }},
  "learning_plan": {{
    "total_weeks": number,
    "timeline": [
      {{
        "month": number,
        "focus": "string",
        "actions": ["string"],
        "estimated_hours_per_week": number
      }}
    ]
  }},
  "overall_recommendation": "2-3 sentence summary with actionable advice"
}}
"""


def call_bedrock(prompt: str) -> dict:
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 4000,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
    })
    resp = bedrock.invoke_model(modelId=MODEL_ID, body=body)
    content = json.loads(resp["body"].read())["content"][0]["text"].strip()
    content = re.sub(r"^```(?:json)?\n?", "", content)
    content = re.sub(r"\n?```$", "", content)
    return json.loads(content)


def lambda_handler(event: dict, context) -> dict:
    logger.info("Agent 5 — Gap Analyzer invoked")

    job_description = event.get("job_description", "").strip()
    if not job_description:
        raise ValueError("'job_description' is required for gap analysis.")

    extracted_skills = event.get("extracted_skills", {})
    skills = extracted_skills.get("skills", [])
    match_result = event.get("match_result", {})
    match_score = match_result.get("match_score", 0)

    skills_list = "\n".join([
        f"  - {s['name']}: {s.get('level', 'unknown')} level, "
        f"{s.get('years', '?')} years ({s.get('category', 'general')})"
        for s in skills
    ])

    gap_analysis = call_bedrock(PROMPT.format(
        skills_list=skills_list or "No skills provided",
        job_description=job_description[:3000],
        match_score=match_score
    ))

    critical_gaps = len(gap_analysis.get("gaps", {}).get("critical", []))
    logger.info(f"Gap analysis done. Critical gaps: {critical_gaps}")

    return {
        **event,
        "gap_analysis": gap_analysis,
        "status": "gaps_analyzed",
    }