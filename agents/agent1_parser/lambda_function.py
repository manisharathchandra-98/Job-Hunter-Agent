"""
Agent 1: Resume Parser
Extracts structured candidate information from resume text using Claude via Bedrock.
"""
import json
import logging
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")
MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"

PROMPT = """You are an expert resume parser and HR specialist.
Extract structured information from the resume below.

Return ONLY valid JSON with this exact schema:
{{
  "name": "string or null",
  "email": "string or null",
  "phone": "string or null",
  "current_role": "string or null",
  "years_experience": number or null,
  "location": "string or null",
  "education": ["string"],
  "certifications": ["string"],
  "work_history": [
    {{
      "company": "string",
      "role": "string",
      "duration": "string",
      "years": number or null
    }}
  ],
  "summary": "2-3 sentence summary of the candidate profile"
}}

Rules:
- years_experience = total professional experience in years (number only)
- If a field is missing use null, never empty string
- education = list of degrees e.g. "BS Computer Science, MIT"
- certifications = professional certs only, keep list short (max 5)
- work_history = most recent 3 roles maximum (keep response concise)
- summary = keep to 2 sentences maximum

Resume:
{resume_text}
"""


def call_bedrock(prompt: str) -> dict:
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
    })
    resp = bedrock.invoke_model(
        modelId=MODEL_ID, body=body,
        contentType="application/json", accept="application/json"
    )
    content = json.loads(resp["body"].read())["content"][0]["text"].strip()

    # Strip markdown code fences if present
    if content.startswith("```"):
        lines = content.splitlines()
        # Remove first line (```json or ```) and last line (```)
        inner = lines[1:] if len(lines) > 1 else lines
        if inner and inner[-1].strip() == "```":
            inner = inner[:-1]
        content = "\n".join(inner).strip()

    # Attempt direct parse
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # Repair truncated JSON — walk back to last clean delimiter
    logger.warning("JSON truncated — attempting repair")
    try:
        repaired = content
        # Walk backwards to find the last clean comma or opening brace/bracket
        for i in range(len(repaired) - 1, 0, -1):
            if repaired[i] in (',', '{', '['):
                repaired = repaired[:i]
                break
        # Close any unclosed arrays and objects
        open_brackets = repaired.count('[') - repaired.count(']')
        open_braces   = repaired.count('{') - repaired.count('}')
        repaired += ']' * max(open_brackets, 0)
        repaired += '}' * max(open_braces, 0)
        return json.loads(repaired)
    except Exception as e:
        logger.error(f"JSON repair failed: {e} | Raw content[:300]: {content[:300]}")
        raise ValueError(f"Bedrock returned malformed JSON: {e}")


def lambda_handler(event: dict, context) -> dict:
    logger.info("Agent 1 — Resume Parser invoked")

    resume_text = event.get("resume_text", "").strip()
    if not resume_text:
        raise ValueError("'resume_text' is required and cannot be empty.")

    # Truncate to 5000 chars — keeps Bedrock output well within 4096 token limit
    resume_text = resume_text[:5000]

    match_id     = event.get("match_id",     getattr(context, "aws_request_id", "local"))
    candidate_id = event.get("candidate_id", match_id)

    parsed_resume = call_bedrock(PROMPT.format(resume_text=resume_text))

    for f in ["education", "certifications", "work_history"]:
        if not isinstance(parsed_resume.get(f), list):
            parsed_resume[f] = []

    logger.info(f"Parsed: name={parsed_resume.get('name')}, "
                f"years={parsed_resume.get('years_experience')}, "
                f"role={parsed_resume.get('current_role')}")

    return {
        "match_id":        match_id,
        "candidate_id":    candidate_id,
        "resume_text":     resume_text,
        "job_description": event.get("job_description", ""),
        "job_id":          event.get("job_id", ""),
        "parsed_resume":   parsed_resume,
        "status":          "parsed",
    }