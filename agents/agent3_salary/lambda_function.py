"""
Agent 3: Market Salary Analyzer
Queries DynamoDB for salary benchmarks and uses Claude for range estimates.
"""
import json
import logging
import os
import re
from decimal import Decimal
import boto3
from boto3.dynamodb.conditions import Key, Attr

logger = logging.getLogger()
logger.setLevel(logging.INFO)

bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")
dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"

SALARY_TABLE = os.environ.get("SALARY_TABLE_NAME", "SalaryData")

PROMPT = """You are a compensation analyst specializing in tech roles.

Return ONLY valid JSON:
{{
  "salary_low": number,
  "salary_median": number,
  "salary_high": number,
  "percentile_25": number,
  "percentile_75": number,
  "currency": "USD",
  "confidence": "low | medium | high",
  "market_insights": "2–3 sentence summary",
  "factors": ["key factors affecting this range"],
  "remote_premium_pct": number
}}

Job Details:
- Title: {job_title}
- Seniority: {seniority}
- Location: {location}
- Primary Skills: {primary_skills}
- Experience Required: {years_exp}

Market Reference Data:
{market_data}
"""


def query_salary(job_title: str, seniority: str) -> list:
    table = dynamodb.Table(SALARY_TABLE)
    keyword = next(
        (w for w in job_title.lower().split()
         if w in {"engineer", "developer", "analyst", "architect", "scientist", "manager", "lead"}),
        None
    )
    results = []
    if keyword:
        try:
            resp = table.query(
                IndexName="TitleIndex",
                KeyConditionExpression=Key("job_title_lower").eq(keyword) & Key("level").eq(seniority),
                Limit=5,
            )
            results = resp.get("Items", [])
        except Exception as e:
            logger.warning(f"DynamoDB query error: {e}")

    if not results:
        try:
            resp = table.scan(
                FilterExpression=Attr("level").eq(seniority),
                Limit=8,
            )
            results = resp.get("Items", [])
        except Exception as e:
            logger.warning(f"DynamoDB scan error: {e}")

    return results


def format_market_data(items: list) -> str:
    if not items:
        return "No exact DB match; use general industry knowledge."
    lines = []
    for i in items[:5]:
        low = float(i.get("salary_low", 0))
        high = float(i.get("salary_high", 0))
        med = float(i.get("salary_median", 0))
        lines.append(
            f"- {i.get('job_title','N/A')} ({i.get('level','N/A')}) "
            f"in {i.get('location','US')}: ${low:,.0f}–${high:,.0f} (median ${med:,.0f})"
        )
    return "\n".join(lines)


def call_bedrock(prompt: str) -> dict:
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
    })
    resp = bedrock.invoke_model(modelId=MODEL_ID, body=body)
    content = json.loads(resp["body"].read())["content"][0]["text"].strip()
    content = re.sub(r"^```(?:json)?\n?", "", content)
    content = re.sub(r"\n?```$", "", content)
    return json.loads(content)


def lambda_handler(event: dict, context) -> dict:
    logger.info("Agent 3 — Salary Analyzer invoked")
    parsed = event.get("parsed_job", {})
    skills_analysis = event.get("skills_analysis", {})
    if not parsed:
        raise ValueError("'parsed_job' missing.")

    job_title = parsed.get("job_title", "Software Engineer")
    seniority = parsed.get("seniority_level", "mid")
    location = parsed.get("location", "United States")

    skills = skills_analysis.get("skills", [])
    primary_skills = [s["name"] for s in skills if s.get("is_primary")][:6]
    if not primary_skills:
        primary_skills = parsed.get("required_skills", [])[:6]

    years_min = parsed.get("years_experience_min")
    years_max = parsed.get("years_experience_max")
    years_exp = f"{years_min}–{years_max}" if (years_min and years_max) else str(years_min or "N/A")

    db_items = query_salary(job_title, seniority)
    market_data = format_market_data(db_items)

    salary = call_bedrock(PROMPT.format(
        job_title=job_title,
        seniority=seniority,
        location=location,
        primary_skills=", ".join(primary_skills),
        years_exp=years_exp,
        market_data=market_data,
    ))

    logger.info(
        f"Salary: ${salary.get('salary_low'):,}–${salary.get('salary_high'):,} "
        f"(confidence: {salary.get('confidence')})"
    )

    return {**event, "salary_data": salary, "status": "salary_analyzed"}