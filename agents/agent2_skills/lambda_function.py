"""
Agent 2: Skills Extractor
Extracts all skills from resume with proficiency levels using Claude via Bedrock.
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

PROMPT = """You are a senior technical recruiter and skills assessment expert.
Extract ALL skills from the resume below with proficiency assessment.

Return ONLY valid JSON with this exact schema:
{{
  "skills": [
    {{
      "name": "string (concise skill name e.g. Python, AWS, Docker)",
      "level": "junior | mid | senior | expert",
      "years": number or null,
      "category": "language | framework | cloud | devops | database | soft | domain | tool",
      "context": "brief description of how this skill was used",
      "is_primary": true or false
    }}
  ],
  "primary_stack": ["top 3-5 most important skills for this candidate"],
  "total_skills_count": number
}}

Rules:
- level = candidate's current proficiency (not what a job requires)
- is_primary = true if this is a core/featured skill
- Extract EVERY technical and soft skill mentioned explicitly or implied
- Infer years from work history duration if not explicitly stated
- category must be one of the listed values

Resume:
{resume_text}

Work History Context:
{work_history}
"""


def call_bedrock(prompt: str) -> dict:
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
    logger.info("Agent 2 — Skills Extractor invoked")

    resume_text = event.get("resume_text", "").strip()
    if not resume_text:
        raise ValueError("'resume_text' is required.")

    parsed_resume = event.get("parsed_resume", {})
    work_history = json.dumps(parsed_resume.get("work_history", []), indent=2)

    extracted = call_bedrock(PROMPT.format(
        resume_text=resume_text,
        work_history=work_history
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