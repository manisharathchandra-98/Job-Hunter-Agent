"""
Seed Data Script — Run once on Day 1 to populate DynamoDB salary data.
Usage: python scripts/seed_data.py
"""
import boto3
import uuid
from datetime import datetime, timezone
from decimal import Decimal

dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
table = dynamodb.Table("SalaryData")

SALARY_DATA = [
    # Software Engineers
    {"job_title": "Software Engineer", "job_title_lower": "engineer", "level": "junior",
     "location": "United States", "salary_low": 70000, "salary_median": 85000,
     "salary_high": 105000, "salary_percentile_25": 75000, "salary_percentile_75": 98000, "currency": "USD"},
    {"job_title": "Software Engineer", "job_title_lower": "engineer", "level": "mid",
     "location": "United States", "salary_low": 100000, "salary_median": 130000,
     "salary_high": 165000, "salary_percentile_25": 115000, "salary_percentile_75": 150000, "currency": "USD"},
    {"job_title": "Software Engineer", "job_title_lower": "engineer", "level": "senior",
     "location": "United States", "salary_low": 140000, "salary_median": 175000,
     "salary_high": 220000, "salary_percentile_25": 155000, "salary_percentile_75": 200000, "currency": "USD"},
    {"job_title": "Software Engineer", "job_title_lower": "engineer", "level": "lead",
     "location": "United States", "salary_low": 170000, "salary_median": 210000,
     "salary_high": 270000, "salary_percentile_25": 185000, "salary_percentile_75": 245000, "currency": "USD"},

    # Data Scientists
    {"job_title": "Data Scientist", "job_title_lower": "scientist", "level": "junior",
     "location": "United States", "salary_low": 75000, "salary_median": 95000,
     "salary_high": 115000, "salary_percentile_25": 82000, "salary_percentile_75": 108000, "currency": "USD"},
    {"job_title": "Data Scientist", "job_title_lower": "scientist", "level": "mid",
     "location": "United States", "salary_low": 110000, "salary_median": 138000,
     "salary_high": 170000, "salary_percentile_25": 120000, "salary_percentile_75": 158000, "currency": "USD"},
    {"job_title": "Data Scientist", "job_title_lower": "scientist", "level": "senior",
     "location": "United States", "salary_low": 150000, "salary_median": 185000,
     "salary_high": 230000, "salary_percentile_25": 163000, "salary_percentile_75": 210000, "currency": "USD"},

    # DevOps / Cloud Engineers
    {"job_title": "DevOps Engineer", "job_title_lower": "engineer", "level": "mid",
     "location": "United States", "salary_low": 105000, "salary_median": 135000,
     "salary_high": 165000, "salary_percentile_25": 118000, "salary_percentile_75": 152000, "currency": "USD"},
    {"job_title": "Cloud Architect", "job_title_lower": "architect", "level": "senior",
     "location": "United States", "salary_low": 155000, "salary_median": 195000,
     "salary_high": 250000, "salary_percentile_25": 170000, "salary_percentile_75": 225000, "currency": "USD"},

    # Analysts
    {"job_title": "Data Analyst", "job_title_lower": "analyst", "level": "junior",
     "location": "United States", "salary_low": 55000, "salary_median": 70000,
     "salary_high": 88000, "salary_percentile_25": 62000, "salary_percentile_75": 80000, "currency": "USD"},
    {"job_title": "Data Analyst", "job_title_lower": "analyst", "level": "mid",
     "location": "United States", "salary_low": 80000, "salary_median": 100000,
     "salary_high": 125000, "salary_percentile_25": 88000, "salary_percentile_75": 115000, "currency": "USD"},
    {"job_title": "Product Manager", "job_title_lower": "manager", "level": "senior",
     "location": "United States", "salary_low": 140000, "salary_median": 175000,
     "salary_high": 220000, "salary_percentile_25": 152000, "salary_percentile_75": 200000, "currency": "USD"},
]


def seed():
    now = datetime.now(timezone.utc).isoformat()
    with table.batch_writer() as batch:
        for row in SALARY_DATA:
            item = {
                "salary_id": str(uuid.uuid4()),
                "created_at": now,
                **{k: Decimal(str(v)) if isinstance(v, (int, float)) else v
                   for k, v in row.items()}
            }
            batch.put_item(Item=item)
    print(f"✅ Seeded {len(SALARY_DATA)} salary records into DynamoDB.")


if __name__ == "__main__":
    seed()