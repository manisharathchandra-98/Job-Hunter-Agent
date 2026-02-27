"""
Agent 4: Difficulty Scorer
Scores job difficulty 1–10 using weighted criteria and Claude reasoning.
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

PROMPT = """You are a career assessment expert.
Score this job's difficulty for a typical candidate (1=very easy, 10=extremely demanding).

Return ONLY valid JSON:
{{
  "score": number (1–10, decimals allowed),
  "label": "Entry Level | Junior | Mid-Level | Senior | Expert | Specialist",
  "explanation": "2–3 sentences justifying the score",
  "learning_curve": "low | medium | high | very_high",
  "estimated_prep_months": number,
  "top_challenges": ["3 biggest challenges in this role"],
  "scoring_breakdown": {{
    "technical_complexity": number,
    "experience_requirement": number,
    "skills_breadth": number,
    "domain_expertise": number
  }}
}}

Weights: technical_complexity 30%, experience_requirement 25%,
         skills_breadth 25%, domain_expertise 20%

Baseline estimate from rule-based analysis: {baseline}/10

Job Details:
- Title: {job_title}
- Seniority: {seniority}
- Experience Required: {years_exp}
- Skills Required: {skills}
- Skill Level Mix: {level_mix}
- Key Responsibilities: {responsibilities}
- Salary Range: {salary_range}
"""


def rule_based_baseline(parsed: dict, skills: list) -> float:
    seniority_map = {
        "junior": 2.5, "mid": 4.5, "senior": 6.5,
        "lead": 7.5, "executive": 8.5, "unknown": 3.5
    }
    score = seniority_map.get(parsed.get("seniority_level", "unknown"), 3.5)

    yrs = float(parsed.get("years_experience_min") or 0)
    if yrs >= 10: score += 2.0
    elif yrs >= 7: score += 1.5
    elif yrs >= 5: score += 1.0
    elif yrs >= 3: score += 0.5

    n = len(skills)
    if n > 15: score += 1.5
    elif n > 10: score += 1.0
    elif n > 5: score += 0.5

    senior_ratio = sum(1 for s in skills if s.get("level") in {"senior", "expert"}) / max(n, 1)
    score += senior_ratio * 1.5

    return min(10.0, max(1.0, score))


def call_bedrock(prompt: str) -> dict:
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
    })
    resp = bedrock.invoke_model(modelId=MODEL_ID, body=body)
    content = json.loads(resp["body"].read())["content"][0]["text"].strip()
    content = re.sub(r"^```(?:json)?\n?", "", content)
    content = re.sub(r"\n?```$", "", content)
    return json.loads(content)


def lambda_handler(event: dict, context) -> dict:
    logger.info("Agent 4 — Difficulty Scorer invoked")
    parsed = event.get("parsed_job", {})
    skills_analysis = event.get("skills_analysis", {})
    salary_data = event.get("salary_data", {})
    if not parsed:
        raise ValueError("'parsed_job' missing.")

    skills = skills_analysis.get("skills", [])
    level_mix = {}
    for s in skills:
        lv = s.get("level", "mid")
        level_mix[lv] = level_mix.get(lv, 0) + 1

    baseline = rule_based_baseline(parsed, skills)

    sal_low = salary_data.get("salary_low")
    sal_high = salary_data.get("salary_high")
    sal_str = f"${sal_low:,}–${sal_high:,}" if isinstance(sal_low, (int, float)) else "unknown"

    years_min = parsed.get("years_experience_min")
    years_max = parsed.get("years_experience_max")
    years_exp = f"{years_min}–{years_max}" if (years_min and years_max) else str(years_min or "N/A")

    result = call_bedrock(PROMPT.format(
        baseline=f"{baseline:.1f}",
        job_title=parsed.get("job_title", "Unknown"),
        seniority=parsed.get("seniority_level", "mid"),
        years_exp=years_exp,
        skills=", ".join(s["name"] for s in skills[:12]),
        level_mix=json.dumps(level_mix),
        responsibilities="; ".join(parsed.get("key_responsibilities", [])[:4]),
        salary_range=sal_str,
    ))

    result["score"] = max(1.0, min(10.0, float(result.get("score", baseline))))
    logger.info(f"Difficulty: {result['score']}/10 — {result.get('label')}")

    return {**event, "difficulty_score": result, "status": "difficulty_scored"}