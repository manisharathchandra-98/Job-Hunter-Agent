"""
Agent 5: Skills Gap Analyzer & Learning Planner
Identifies skill gaps between candidate and job, creates a learning plan.
"""
import json
import logging
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

bedrock  = boto3.client("bedrock-runtime", region_name="us-east-1")
MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"

PROMPT = """You are a career coach specializing in tech careers.

CANDIDATE SKILLS (top 15):
{skills_list}

JOB DESCRIPTION:
{job_description}

MATCH SCORE: {match_score}%

Analyze the skills gap. Keep your response concise.

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
    "critical":     [{{"skill": "string", "learning_time_weeks": number, "resource": "string"}}],
    "important":    [{{"skill": "string", "learning_time_weeks": number, "resource": "string"}}],
    "nice_to_have": [{{"skill": "string", "learning_time_weeks": number, "resource": "string"}}]
  }},
  "learning_plan": {{
    "total_weeks": number,
    "timeline": [
      {{"month": number, "focus": "string", "action": "string"}}
    ]
  }},
  "overall_recommendation": "2 sentence summary with actionable advice"
}}

Rules:
- matched_skills: max 10 items
- partial_skills: max 5 items
- missing_skills: max 8 items
- critical/important/nice_to_have gaps: max 3 items each
- timeline: max 3 months
- overall_recommendation: 2 sentences only
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
    logger.info("Agent 5 — Gap Analyzer invoked")

    job_description = event.get("job_description", "").strip()
    if not job_description:
        raise ValueError("'job_description' is required for gap analysis.")

    extracted_skills = event.get("extracted_skills", {})
    skills           = extracted_skills.get("skills", [])
    match_result     = event.get("match_result",     {})
    match_score      = match_result.get("match_score", 0)

    # ✅ Limit to 15 skills
    skills_list = "\n".join([
        f"  - {s['name']}: {s.get('level','unknown')} level, "
        f"{s.get('years','?')} years ({s.get('category','general')})"
        for s in skills[:15]
    ])

    gap_analysis = call_bedrock(PROMPT.format(
        skills_list=skills_list or "No skills provided",
        job_description=job_description[:3000],
        match_score=match_score,
    ))

    critical_gaps = len(gap_analysis.get("gaps", {}).get("critical", []))
    logger.info(f"Gap analysis done. Critical gaps: {critical_gaps}")

    return {
        **event,
        "gap_analysis": gap_analysis,
        "status":       "gaps_analyzed",
    }