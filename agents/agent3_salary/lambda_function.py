"""
Agent 3: Candidate Market Analyzer
Analyzes candidate's market value and earning potential using Claude via Bedrock.
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
dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"
SALARY_TABLE = os.environ.get("SALARY_TABLE_NAME", "SalaryData")

PROMPT = """You are a compensation expert and talent market analyst.
Based on this candidate's profile, estimate their market value.

Candidate Profile:
- Name: {name}
- Current Role: {current_role}
- Years of Experience: {years_experience}
- Education: {education}
- Certifications: {certifications}
- Primary Skills: {primary_stack}
- All Skills: {skills_summary}

Salary Benchmark Data:
{salary_data}

Return ONLY valid JSON:
{{
  "salary_low": number,
  "salary_median": number,
  "salary_high": number,
  "market_position": "entry | mid | senior | lead | principal",
  "market_demand": "low | medium | high | very_high",
  "earning_potential_6months": number,
  "best_suited_roles": ["string"],
  "market_insight": "2-3 sentence market commentary"
}}
"""


def get_salary_benchmarks() -> list:
    try:
        table = dynamodb.Table(SALARY_TABLE)
        result = table.scan(Limit=15)
        return result.get("Items", [])
    except ClientError as e:
        logger.warning(f"Could not fetch salary data: {e}")
        return []


def call_bedrock(prompt: str) -> dict:
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1500,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
    })
    resp = bedrock.invoke_model(modelId=MODEL_ID, body=body)
    content = json.loads(resp["body"].read())["content"][0]["text"].strip()
    content = re.sub(r"^```(?:json)?\n?", "", content)
    content = re.sub(r"\n?```$", "", content)
    return json.loads(content)


def lambda_handler(event: dict, context) -> dict:
    logger.info("Agent 3 — Candidate Market Analyzer invoked")

    parsed_resume = event.get("parsed_resume", {})
    extracted_skills = event.get("extracted_skills", {})
    skills = extracted_skills.get("skills", [])
    primary_stack = extracted_skills.get("primary_stack", [])

    salary_data = get_salary_benchmarks()
    skills_summary = ", ".join([
        f"{s['name']} ({s.get('level', 'unknown')})"
        for s in skills[:15]
    ])

    market_analysis = call_bedrock(PROMPT.format(
        name=parsed_resume.get("name", "Candidate"),
        current_role=parsed_resume.get("current_role", "Unknown"),
        years_experience=parsed_resume.get("years_experience", 0),
        education=", ".join(parsed_resume.get("education", [])) or "Not specified",
        certifications=", ".join(parsed_resume.get("certifications", [])) or "None",
        primary_stack=", ".join(primary_stack) or "Not specified",
        skills_summary=skills_summary or "Not specified",
        salary_data=json.dumps(salary_data[:5], default=str)
    ))

    logger.info(f"Market value: ${market_analysis.get('salary_median')} median, "
                f"position: {market_analysis.get('market_position')}")

    return {
        **event,
        "market_analysis": market_analysis,
        "status": "market_analyzed",
    }