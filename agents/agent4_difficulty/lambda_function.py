"""
Agent 4: Job-Candidate Match Scorer
Scores how well a candidate matches a job posting (0-100).
"""
import json
import logging
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

bedrock  = boto3.client("bedrock-runtime", region_name="us-east-1")
MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"

PROMPT = """You are a senior technical recruiter scoring candidate-job fit.

CANDIDATE PROFILE:
- Current Role: {current_role}
- Years of Experience: {years_experience}
- Skills:
{skills_list}

JOB DESCRIPTION:
{job_description}

Score the match from 0 to 100 based on:
1. Skill coverage — what % of required skills does the candidate have?
2. Skill level match — does the candidate meet the proficiency requirements?
3. Experience match — years of experience vs what the job requires
4. Overall holistic fit

Return ONLY valid JSON:
{{
  "match_score": number (0-100),
  "score_breakdown": {{
    "skill_coverage": number (0-100),
    "skill_level_match": number (0-100),
    "experience_match": number (0-100),
    "overall": number (0-100)
  }},
  "recommendation": "Strong Fit | Good Fit | Partial Fit | Weak Fit",
  "effort_to_match": "low | medium | high",
  "explanation": "2 sentence explanation of the score",
  "job_title_detected": "string or null",
  "experience_required_detected": number or null
}}
"""


def call_bedrock(prompt: str) -> dict:
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 4096,
        "temperature": 0.1,
        "messages": [{"role": "user", "content": prompt}],
    })
    resp = bedrock.invoke_model(
        modelId=MODEL_ID, body=body,
        contentType="application/json", accept="application/json"
    )
    content = json.loads(resp["body"].read())["content"][0]["text"].strip()

    # Strip markdown code fences
    if content.startswith("```"):
        lines = content.splitlines()
        inner = lines[1:] if len(lines) > 1 else lines
        if inner and inner[-1].strip() == "```":
            inner = inner[:-1]
        content = "\n".join(inner).strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    logger.warning("JSON truncated — attempting repair")
    try:
        repaired = content
        for i in range(len(repaired) - 1, 0, -1):
            if repaired[i] in (',', '{', '['):
                repaired = repaired[:i]
                break
        # ✅ Count AFTER trimming
        open_brackets = repaired.count('[') - repaired.count(']')
        open_braces   = repaired.count('{') - repaired.count('}')
        repaired += ']' * max(open_brackets, 0)
        repaired += '}' * max(open_braces, 0)
        return json.loads(repaired)
    except Exception as e:
        logger.error(f"JSON repair failed: {e} | content[:300]: {content[:300]}")
        raise ValueError(f"Bedrock returned malformed JSON: {e}")


def lambda_handler(event: dict, context) -> dict:
    logger.info("Agent 4 — Match Scorer invoked")

    job_description = event.get("job_description", "").strip()

    if not job_description:
        logger.warning("Empty job_description — returning zero score.")
        return {
            **event,
            "match_result": {
                "match_score": 0,
                "score_breakdown": {
                    "skill_coverage": 0, "skill_level_match": 0,
                    "experience_match": 0, "overall": 0,
                },
                "recommendation": "Weak Fit",
                "effort_to_match": "high",
                "explanation": "No job description provided.",
                "job_title_detected": None,
                "experience_required_detected": None,
            },
            "status": "match_scored",
        }

    parsed_resume    = event.get("parsed_resume",    {})
    extracted_skills = event.get("extracted_skills", {})
    skills           = extracted_skills.get("skills", [])

    # ✅ Limit to 20 skills — prevents oversized prompt
    skills_list = "\n".join([
        f"  - {s['name']}: {s.get('level','unknown')} level, "
        f"{s.get('years','?')} years ({s.get('category','general')})"
        for s in skills[:20]
    ])

    match_result = call_bedrock(PROMPT.format(
        current_role=parsed_resume.get("current_role", "Unknown"),
        years_experience=parsed_resume.get("years_experience", 0),
        skills_list=skills_list or "No skills extracted",
        job_description=job_description[:3000],
    ))

    logger.info(f"Match score: {match_result.get('match_score')}% — "
                f"{match_result.get('recommendation')}")

    return {
        **event,
        "match_result": match_result,
        "status":       "match_scored",
    }