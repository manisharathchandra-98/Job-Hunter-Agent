"""
Agent 1: Job Requirements Parser
Extracts structured data from raw job descriptions using Claude via Bedrock.
"""
import json
import logging
import os
import re
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")
MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"

PROMPT = """You are an expert job description analyzer.
Extract structured data from the job posting below.

Return ONLY valid JSON with this exact schema:
{{
  "job_title": "string",
  "company_name": "string or null",
  "location": "string or null",
  "employment_type": "full-time | part-time | contract | unknown",
  "key_responsibilities": ["string"],
  "required_skills": ["string"],
  "nice_to_have_skills": ["string"],
  "years_experience_min": number or null,
  "years_experience_max": number or null,
  "education_required": "string or null",
  "industry": "string",
  "seniority_level": "junior | mid | senior | lead | executive | unknown"
}}

Rules:
- Extract ALL skills mentioned (explicit and implied)
- Use null for missing fields, not empty strings
- Infer seniority from title and experience if not stated

Job Posting:
{job_text}
"""


def call_bedrock(prompt: str) -> dict:
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 2048,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
    })
    resp = bedrock.invoke_model(modelId=MODEL_ID, body=body)
    content = json.loads(resp["body"].read())["content"][0]["text"].strip()
    # Strip markdown fences if present
    content = re.sub(r"^```(?:json)?\n?", "", content)
    content = re.sub(r"\n?```$", "", content)
    return json.loads(content)


def lambda_handler(event: dict, context) -> dict:
    logger.info("Agent 1 — Job Parser invoked")

    job_text = event.get("job_description", "").strip()
    if not job_text:
        raise ValueError("'job_description' is required and cannot be empty.")

    job_text = job_text[:15000]  # Hard cap for token safety
    job_id = event.get("job_id", getattr(context, "aws_request_id", "local"))

    parsed = call_bedrock(PROMPT.format(job_text=job_text))

    # Sanitize list fields
    for f in ["required_skills", "nice_to_have_skills", "key_responsibilities"]:
        if not isinstance(parsed.get(f), list):
            parsed[f] = []

    logger.info(
        f"Parsed: title={parsed.get('job_title')}, "
        f"skills={len(parsed.get('required_skills', []))}, "
        f"seniority={parsed.get('seniority_level')}"
    )

    return {
        "job_id": job_id,
        "job_description": job_text,
        "parsed_job": parsed,
        "status": "parsed",
    }