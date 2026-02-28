"""
scripts/seed_data.py
Seeds the SalaryData DynamoDB table with realistic market salary benchmarks.
Run: python scripts/seed_data.py
"""

import boto3
from decimal import Decimal

dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
table = dynamodb.Table("SalaryData")

# salary_id = "{skill}#{level}"  ← partition key required by table schema
SALARY_DATA = [
    # ── Python ───────────────────────────────────────────────────────────────
    {"salary_id": "Python#junior",  "skill": "Python", "level": "junior",  "role_category": "software_engineering", "salary_low": Decimal("65000"),  "salary_median": Decimal("80000"),  "salary_high": Decimal("95000"),  "market_demand": "high",      "yoe_min": Decimal("0"),  "yoe_max": Decimal("2")},
    {"salary_id": "Python#mid",     "skill": "Python", "level": "mid",     "role_category": "software_engineering", "salary_low": Decimal("90000"),  "salary_median": Decimal("110000"), "salary_high": Decimal("130000"), "market_demand": "very_high", "yoe_min": Decimal("2"),  "yoe_max": Decimal("5")},
    {"salary_id": "Python#senior",  "skill": "Python", "level": "senior",  "role_category": "software_engineering", "salary_low": Decimal("130000"), "salary_median": Decimal("155000"), "salary_high": Decimal("185000"), "market_demand": "very_high", "yoe_min": Decimal("5"),  "yoe_max": Decimal("10")},
    {"salary_id": "Python#expert",  "skill": "Python", "level": "expert",  "role_category": "software_engineering", "salary_low": Decimal("175000"), "salary_median": Decimal("210000"), "salary_high": Decimal("260000"), "market_demand": "very_high", "yoe_min": Decimal("10"), "yoe_max": Decimal("99")},

    # ── JavaScript ───────────────────────────────────────────────────────────
    {"salary_id": "JavaScript#junior", "skill": "JavaScript", "level": "junior", "role_category": "software_engineering", "salary_low": Decimal("60000"),  "salary_median": Decimal("75000"),  "salary_high": Decimal("90000"),  "market_demand": "high",      "yoe_min": Decimal("0"), "yoe_max": Decimal("2")},
    {"salary_id": "JavaScript#mid",    "skill": "JavaScript", "level": "mid",    "role_category": "software_engineering", "salary_low": Decimal("85000"),  "salary_median": Decimal("105000"), "salary_high": Decimal("125000"), "market_demand": "high",      "yoe_min": Decimal("2"), "yoe_max": Decimal("5")},
    {"salary_id": "JavaScript#senior", "skill": "JavaScript", "level": "senior", "role_category": "software_engineering", "salary_low": Decimal("120000"), "salary_median": Decimal("145000"), "salary_high": Decimal("175000"), "market_demand": "high",      "yoe_min": Decimal("5"), "yoe_max": Decimal("10")},

    # ── TypeScript ───────────────────────────────────────────────────────────
    {"salary_id": "TypeScript#mid",    "skill": "TypeScript", "level": "mid",    "role_category": "software_engineering", "salary_low": Decimal("95000"),  "salary_median": Decimal("115000"), "salary_high": Decimal("135000"), "market_demand": "very_high", "yoe_min": Decimal("2"), "yoe_max": Decimal("5")},
    {"salary_id": "TypeScript#senior", "skill": "TypeScript", "level": "senior", "role_category": "software_engineering", "salary_low": Decimal("130000"), "salary_median": Decimal("155000"), "salary_high": Decimal("185000"), "market_demand": "very_high", "yoe_min": Decimal("5"), "yoe_max": Decimal("10")},

    # ── Java ─────────────────────────────────────────────────────────────────
    {"salary_id": "Java#junior", "skill": "Java", "level": "junior", "role_category": "software_engineering", "salary_low": Decimal("70000"),  "salary_median": Decimal("85000"),  "salary_high": Decimal("100000"), "market_demand": "high", "yoe_min": Decimal("0"), "yoe_max": Decimal("2")},
    {"salary_id": "Java#mid",    "skill": "Java", "level": "mid",    "role_category": "software_engineering", "salary_low": Decimal("95000"),  "salary_median": Decimal("115000"), "salary_high": Decimal("135000"), "market_demand": "high", "yoe_min": Decimal("2"), "yoe_max": Decimal("5")},
    {"salary_id": "Java#senior", "skill": "Java", "level": "senior", "role_category": "software_engineering", "salary_low": Decimal("130000"), "salary_median": Decimal("155000"), "salary_high": Decimal("185000"), "market_demand": "high", "yoe_min": Decimal("5"), "yoe_max": Decimal("10")},

    # ── Go ───────────────────────────────────────────────────────────────────
    {"salary_id": "Go#mid",    "skill": "Go", "level": "mid",    "role_category": "software_engineering", "salary_low": Decimal("105000"), "salary_median": Decimal("125000"), "salary_high": Decimal("150000"), "market_demand": "high", "yoe_min": Decimal("2"), "yoe_max": Decimal("5")},
    {"salary_id": "Go#senior", "skill": "Go", "level": "senior", "role_category": "software_engineering", "salary_low": Decimal("140000"), "salary_median": Decimal("165000"), "salary_high": Decimal("195000"), "market_demand": "high", "yoe_min": Decimal("5"), "yoe_max": Decimal("10")},

    # ── Rust ─────────────────────────────────────────────────────────────────
    {"salary_id": "Rust#mid",    "skill": "Rust", "level": "mid",    "role_category": "software_engineering", "salary_low": Decimal("115000"), "salary_median": Decimal("140000"), "salary_high": Decimal("165000"), "market_demand": "medium", "yoe_min": Decimal("2"), "yoe_max": Decimal("5")},
    {"salary_id": "Rust#senior", "skill": "Rust", "level": "senior", "role_category": "software_engineering", "salary_low": Decimal("150000"), "salary_median": Decimal("180000"), "salary_high": Decimal("215000"), "market_demand": "medium", "yoe_min": Decimal("5"), "yoe_max": Decimal("10")},

    # ── AWS ──────────────────────────────────────────────────────────────────
    {"salary_id": "AWS#junior", "skill": "AWS", "level": "junior", "role_category": "cloud_devops", "salary_low": Decimal("75000"),  "salary_median": Decimal("90000"),  "salary_high": Decimal("108000"), "market_demand": "very_high", "yoe_min": Decimal("0"), "yoe_max": Decimal("2")},
    {"salary_id": "AWS#mid",    "skill": "AWS", "level": "mid",    "role_category": "cloud_devops", "salary_low": Decimal("105000"), "salary_median": Decimal("125000"), "salary_high": Decimal("150000"), "market_demand": "very_high", "yoe_min": Decimal("2"), "yoe_max": Decimal("5")},
    {"salary_id": "AWS#senior", "skill": "AWS", "level": "senior", "role_category": "cloud_devops", "salary_low": Decimal("140000"), "salary_median": Decimal("165000"), "salary_high": Decimal("200000"), "market_demand": "very_high", "yoe_min": Decimal("5"), "yoe_max": Decimal("10")},

    # ── Kubernetes ───────────────────────────────────────────────────────────
    {"salary_id": "Kubernetes#mid",    "skill": "Kubernetes", "level": "mid",    "role_category": "cloud_devops", "salary_low": Decimal("110000"), "salary_median": Decimal("130000"), "salary_high": Decimal("155000"), "market_demand": "very_high", "yoe_min": Decimal("2"), "yoe_max": Decimal("5")},
    {"salary_id": "Kubernetes#senior", "skill": "Kubernetes", "level": "senior", "role_category": "cloud_devops", "salary_low": Decimal("145000"), "salary_median": Decimal("170000"), "salary_high": Decimal("205000"), "market_demand": "very_high", "yoe_min": Decimal("5"), "yoe_max": Decimal("10")},

    # ── Docker ───────────────────────────────────────────────────────────────
    {"salary_id": "Docker#mid",    "skill": "Docker", "level": "mid",    "role_category": "cloud_devops", "salary_low": Decimal("95000"),  "salary_median": Decimal("115000"), "salary_high": Decimal("138000"), "market_demand": "high", "yoe_min": Decimal("2"), "yoe_max": Decimal("5")},
    {"salary_id": "Docker#senior", "skill": "Docker", "level": "senior", "role_category": "cloud_devops", "salary_low": Decimal("125000"), "salary_median": Decimal("148000"), "salary_high": Decimal("175000"), "market_demand": "high", "yoe_min": Decimal("5"), "yoe_max": Decimal("10")},

    # ── Terraform ────────────────────────────────────────────────────────────
    {"salary_id": "Terraform#mid",    "skill": "Terraform", "level": "mid",    "role_category": "cloud_devops", "salary_low": Decimal("105000"), "salary_median": Decimal("125000"), "salary_high": Decimal("150000"), "market_demand": "high", "yoe_min": Decimal("2"), "yoe_max": Decimal("5")},
    {"salary_id": "Terraform#senior", "skill": "Terraform", "level": "senior", "role_category": "cloud_devops", "salary_low": Decimal("140000"), "salary_median": Decimal("162000"), "salary_high": Decimal("192000"), "market_demand": "high", "yoe_min": Decimal("5"), "yoe_max": Decimal("10")},

    # ── CI/CD ────────────────────────────────────────────────────────────────
    {"salary_id": "CICD#mid",    "skill": "CI/CD", "level": "mid",    "role_category": "cloud_devops", "salary_low": Decimal("95000"),  "salary_median": Decimal("115000"), "salary_high": Decimal("138000"), "market_demand": "high", "yoe_min": Decimal("2"), "yoe_max": Decimal("5")},
    {"salary_id": "CICD#senior", "skill": "CI/CD", "level": "senior", "role_category": "cloud_devops", "salary_low": Decimal("120000"), "salary_median": Decimal("142000"), "salary_high": Decimal("168000"), "market_demand": "high", "yoe_min": Decimal("5"), "yoe_max": Decimal("10")},

    # ── Machine Learning ─────────────────────────────────────────────────────
    {"salary_id": "MachineLearning#mid",    "skill": "Machine Learning", "level": "mid",    "role_category": "data_ml", "salary_low": Decimal("115000"), "salary_median": Decimal("140000"), "salary_high": Decimal("168000"), "market_demand": "very_high", "yoe_min": Decimal("2"), "yoe_max": Decimal("5")},
    {"salary_id": "MachineLearning#senior", "skill": "Machine Learning", "level": "senior", "role_category": "data_ml", "salary_low": Decimal("155000"), "salary_median": Decimal("185000"), "salary_high": Decimal("225000"), "market_demand": "very_high", "yoe_min": Decimal("5"), "yoe_max": Decimal("10")},

    # ── Deep Learning ────────────────────────────────────────────────────────
    {"salary_id": "DeepLearning#mid",    "skill": "Deep Learning", "level": "mid",    "role_category": "data_ml", "salary_low": Decimal("125000"), "salary_median": Decimal("150000"), "salary_high": Decimal("180000"), "market_demand": "very_high", "yoe_min": Decimal("2"), "yoe_max": Decimal("5")},
    {"salary_id": "DeepLearning#senior", "skill": "Deep Learning", "level": "senior", "role_category": "data_ml", "salary_low": Decimal("165000"), "salary_median": Decimal("198000"), "salary_high": Decimal("240000"), "market_demand": "very_high", "yoe_min": Decimal("5"), "yoe_max": Decimal("10")},

    # ── Data Science ─────────────────────────────────────────────────────────
    {"salary_id": "DataScience#mid",    "skill": "Data Science", "level": "mid",    "role_category": "data_ml", "salary_low": Decimal("100000"), "salary_median": Decimal("120000"), "salary_high": Decimal("145000"), "market_demand": "high", "yoe_min": Decimal("2"), "yoe_max": Decimal("5")},
    {"salary_id": "DataScience#senior", "skill": "Data Science", "level": "senior", "role_category": "data_ml", "salary_low": Decimal("135000"), "salary_median": Decimal("160000"), "salary_high": Decimal("195000"), "market_demand": "high", "yoe_min": Decimal("5"), "yoe_max": Decimal("10")},

    # ── SQL ──────────────────────────────────────────────────────────────────
    {"salary_id": "SQL#mid",    "skill": "SQL", "level": "mid",    "role_category": "data_ml", "salary_low": Decimal("85000"),  "salary_median": Decimal("100000"), "salary_high": Decimal("118000"), "market_demand": "high", "yoe_min": Decimal("2"), "yoe_max": Decimal("5")},
    {"salary_id": "SQL#senior", "skill": "SQL", "level": "senior", "role_category": "data_ml", "salary_low": Decimal("110000"), "salary_median": Decimal("130000"), "salary_high": Decimal("155000"), "market_demand": "high", "yoe_min": Decimal("5"), "yoe_max": Decimal("10")},

    # ── Apache Spark ─────────────────────────────────────────────────────────
    {"salary_id": "ApacheSpark#mid",    "skill": "Apache Spark", "level": "mid",    "role_category": "data_ml", "salary_low": Decimal("110000"), "salary_median": Decimal("132000"), "salary_high": Decimal("158000"), "market_demand": "high", "yoe_min": Decimal("2"), "yoe_max": Decimal("5")},
    {"salary_id": "ApacheSpark#senior", "skill": "Apache Spark", "level": "senior", "role_category": "data_ml", "salary_low": Decimal("145000"), "salary_median": Decimal("172000"), "salary_high": Decimal("205000"), "market_demand": "high", "yoe_min": Decimal("5"), "yoe_max": Decimal("10")},

    # ── React ────────────────────────────────────────────────────────────────
    {"salary_id": "React#junior", "skill": "React", "level": "junior", "role_category": "frontend", "salary_low": Decimal("65000"),  "salary_median": Decimal("78000"),  "salary_high": Decimal("93000"),  "market_demand": "very_high", "yoe_min": Decimal("0"), "yoe_max": Decimal("2")},
    {"salary_id": "React#mid",    "skill": "React", "level": "mid",    "role_category": "frontend", "salary_low": Decimal("90000"),  "salary_median": Decimal("110000"), "salary_high": Decimal("132000"), "market_demand": "very_high", "yoe_min": Decimal("2"), "yoe_max": Decimal("5")},
    {"salary_id": "React#senior", "skill": "React", "level": "senior", "role_category": "frontend", "salary_low": Decimal("125000"), "salary_median": Decimal("148000"), "salary_high": Decimal("178000"), "market_demand": "very_high", "yoe_min": Decimal("5"), "yoe_max": Decimal("10")},

    # ── Vue.js ───────────────────────────────────────────────────────────────
    {"salary_id": "Vuejs#mid",    "skill": "Vue.js", "level": "mid",    "role_category": "frontend", "salary_low": Decimal("85000"),  "salary_median": Decimal("103000"), "salary_high": Decimal("122000"), "market_demand": "medium", "yoe_min": Decimal("2"), "yoe_max": Decimal("5")},
    {"salary_id": "Vuejs#senior", "skill": "Vue.js", "level": "senior", "role_category": "frontend", "salary_low": Decimal("115000"), "salary_median": Decimal("136000"), "salary_high": Decimal("162000"), "market_demand": "medium", "yoe_min": Decimal("5"), "yoe_max": Decimal("10")},

    # ── Node.js ──────────────────────────────────────────────────────────────
    {"salary_id": "Nodejs#mid",    "skill": "Node.js", "level": "mid",    "role_category": "backend", "salary_low": Decimal("90000"),  "salary_median": Decimal("110000"), "salary_high": Decimal("132000"), "market_demand": "high", "yoe_min": Decimal("2"), "yoe_max": Decimal("5")},
    {"salary_id": "Nodejs#senior", "skill": "Node.js", "level": "senior", "role_category": "backend", "salary_low": Decimal("120000"), "salary_median": Decimal("142000"), "salary_high": Decimal("170000"), "market_demand": "high", "yoe_min": Decimal("5"), "yoe_max": Decimal("10")},

    # ── FastAPI ──────────────────────────────────────────────────────────────
    {"salary_id": "FastAPI#mid",    "skill": "FastAPI", "level": "mid",    "role_category": "backend", "salary_low": Decimal("95000"),  "salary_median": Decimal("115000"), "salary_high": Decimal("138000"), "market_demand": "high", "yoe_min": Decimal("2"), "yoe_max": Decimal("5")},
    {"salary_id": "FastAPI#senior", "skill": "FastAPI", "level": "senior", "role_category": "backend", "salary_low": Decimal("125000"), "salary_median": Decimal("148000"), "salary_high": Decimal("175000"), "market_demand": "high", "yoe_min": Decimal("5"), "yoe_max": Decimal("10")},

    # ── Django ───────────────────────────────────────────────────────────────
    {"salary_id": "Django#mid",    "skill": "Django", "level": "mid",    "role_category": "backend", "salary_low": Decimal("88000"),  "salary_median": Decimal("107000"), "salary_high": Decimal("128000"), "market_demand": "medium", "yoe_min": Decimal("2"), "yoe_max": Decimal("5")},
    {"salary_id": "Django#senior", "skill": "Django", "level": "senior", "role_category": "backend", "salary_low": Decimal("115000"), "salary_median": Decimal("136000"), "salary_high": Decimal("162000"), "market_demand": "medium", "yoe_min": Decimal("5"), "yoe_max": Decimal("10")},

    # ── GraphQL ──────────────────────────────────────────────────────────────
    {"salary_id": "GraphQL#mid",    "skill": "GraphQL", "level": "mid",    "role_category": "backend", "salary_low": Decimal("95000"),  "salary_median": Decimal("115000"), "salary_high": Decimal("138000"), "market_demand": "medium", "yoe_min": Decimal("2"), "yoe_max": Decimal("5")},
    {"salary_id": "GraphQL#senior", "skill": "GraphQL", "level": "senior", "role_category": "backend", "salary_low": Decimal("125000"), "salary_median": Decimal("148000"), "salary_high": Decimal("175000"), "market_demand": "medium", "yoe_min": Decimal("5"), "yoe_max": Decimal("10")},

    # ── Cybersecurity ────────────────────────────────────────────────────────
    {"salary_id": "Cybersecurity#mid",    "skill": "Cybersecurity", "level": "mid",    "role_category": "security", "salary_low": Decimal("105000"), "salary_median": Decimal("128000"), "salary_high": Decimal("155000"), "market_demand": "very_high", "yoe_min": Decimal("2"), "yoe_max": Decimal("5")},
    {"salary_id": "Cybersecurity#senior", "skill": "Cybersecurity", "level": "senior", "role_category": "security", "salary_low": Decimal("145000"), "salary_median": Decimal("175000"), "salary_high": Decimal("215000"), "market_demand": "very_high", "yoe_min": Decimal("5"), "yoe_max": Decimal("10")},
]


def seed():
    print(f"Seeding {len(SALARY_DATA)} records into SalaryData table...")
    success = 0
    errors = 0

    with table.batch_writer() as batch:
        for item in SALARY_DATA:
            try:
                batch.put_item(Item=item)
                success += 1
            except Exception as e:
                print(f"  ERROR: {item['skill']} ({item['level']}): {e}")
                errors += 1

    print(f"\n✅ Done! {success} records inserted, {errors} errors.")
    print("\nSample verification — first 3 records:")
    resp = table.scan(Limit=3)
    for item in resp.get("Items", []):
        print(f"  {item['skill']} | {item['level']} | ${item['salary_median']:,} median")


if __name__ == "__main__":
    seed()