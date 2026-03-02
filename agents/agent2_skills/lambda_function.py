"""
Agent 2: Skills Extractor
Extracts skills from resume with proficiency levels using Claude via Bedrock.
"""
import json
import logging
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")
MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"

PROMPT = """You are a senior technical recruiter and skills assessment expert.
Extract the TOP 20 most important skills from the resume below.

Return ONLY valid JSON with this exact schema:
{{
  "skills": [
    {{
      "name": "string (concise skill name e.g. Python, AWS, Docker)",
      "level": "junior | mid | senior | expert",
      "years": number or null,
      "category": "language | framework | cloud | devops | database | soft | domain | tool",
      "is_primary": true or false
    }}
  ],
  "primary_stack": ["top 5 most important skills for this candidate"],
  "total_skills_count": number
}}

Rules:
- Limit to 20 skills maximum — prioritise primary/core skills
- level = candidate's current proficiency
- is_primary = true for core/featured skills only (max 8)
- category must be one of the listed values exactly
- years = number only, null if unknown

Resume (first 4000 chars):
{resume_text}
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

    # Attempt direct parse
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # Repair truncated JSON
    logger.warning("JSON truncated — attempting repair")
    try:
        repaired = content
        # Walk back to last clean delimiter
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
    logger.info("Agent 2 — Skills Extractor invoked")

    resume_text = event.get("resume_text", "").strip()
    if not resume_text:
        raise ValueError("'resume_text' is required.")

    # ✅ Truncate — keeps prompt + output within Bedrock's 4096 token limit
    resume_text_trimmed = resume_text[:4000]

    # ✅ Removed work_history from prompt — reduces input size significantly
    extracted = call_bedrock(PROMPT.format(
        resume_text=resume_text_trimmed,
    ))

    skills = extracted.get("skills", [])
    if not isinstance(skills, list):
        skills = []
        extracted["skills"] = skills

    logger.info(f"Extracted {len(skills)} skills. "
                f"Primary stack: {extracted.get('primary_stack', [])}")

    return {
        **event,
        "extracted_skills": extracted,
        "status": "skills_extracted",
    }