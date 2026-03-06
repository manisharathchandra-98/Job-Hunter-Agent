"""
Day 7 - Create Amazon OpenSearch Serverless collection for RAG.
Run once: python infrastructure/create_opensearch.py
"""
import boto3
import json
import time
import sys

COLLECTION_NAME = "job-analyzer-rag"
REGION = "us-east-1"

def get_account_id():
    return boto3.client("sts").get_caller_identity()["Account"]

def create_collection():
    client = boto3.client("opensearchserverless", region_name=REGION)
    account_id = get_account_id()

    print("Creating encryption policy...")
    try:
        client.create_security_policy(
            name=f"{COLLECTION_NAME}-enc",
            type="encryption",
            policy=json.dumps({
                "Rules": [{"ResourceType": "collection", "Resource": [f"collection/{COLLECTION_NAME}"]}],
                "AWSOwnedKey": True
            })
        )
    except client.exceptions.ConflictException:
        print("  Encryption policy already exists, skipping.")

    print("Creating network policy...")
    try:
        client.create_security_policy(
            name=f"{COLLECTION_NAME}-net",
            type="network",
            policy=json.dumps([{
                "Rules": [
                    {"ResourceType": "collection", "Resource": [f"collection/{COLLECTION_NAME}"]},
                    {"ResourceType": "dashboard", "Resource": [f"collection/{COLLECTION_NAME}"]}
                ],
                "AllowFromPublic": True
            }])
        )
    except client.exceptions.ConflictException:
        print("  Network policy already exists, skipping.")

    print("Creating data access policy...")
    try:
        # Allow Lambda execution roles + current caller full access
        principals = [
            f"arn:aws:iam::{account_id}:root",
            f"arn:aws:iam::{account_id}:role/job-analyzer-resume-coach-role",
            f"arn:aws:iam::{account_id}:role/job-analyzer-lambda-role",
        ]
        client.create_access_policy(
            name=f"{COLLECTION_NAME}-access",
            type="data",
            policy=json.dumps([{
                "Rules": [
                    {
                        "ResourceType": "index",
                        "Resource": [f"index/{COLLECTION_NAME}/*"],
                        "Permission": [
                            "aoss:CreateIndex", "aoss:DeleteIndex", "aoss:UpdateIndex",
                            "aoss:DescribeIndex", "aoss:ReadDocument", "aoss:WriteDocument"
                        ]
                    },
                    {
                        "ResourceType": "collection",
                        "Resource": [f"collection/{COLLECTION_NAME}"],
                        "Permission": ["aoss:CreateCollectionItems", "aoss:DescribeCollectionItems", "aoss:UpdateCollectionItems"]
                    }
                ],
                "Principal": principals
            }])
        )
    except client.exceptions.ConflictException:
        print("  Data access policy already exists, skipping.")

    print("Creating OpenSearch Serverless collection (VECTORSEARCH)...")
    try:
        resp = client.create_collection(
            name=COLLECTION_NAME,
            type="VECTORSEARCH",
            description="Career knowledge base for Job Fit Analyzer RAG"
        )
        collection_id = resp["createCollectionDetail"]["id"]
    except client.exceptions.ConflictException:
        print("  Collection already exists, fetching endpoint...")
        collections = client.list_collections(collectionFilters={"name": COLLECTION_NAME})
        collection_id = collections["collectionSummaries"][0]["id"]

    print(f"Collection ID: {collection_id}")
    print("Waiting for collection to become ACTIVE (this takes 3–5 minutes)...")

    while True:
        status_resp = client.batch_get_collection(ids=[collection_id])
        detail = status_resp["collectionDetails"][0]
        status = detail["status"]
        print(f"  Status: {status}")
        if status == "ACTIVE":
            endpoint = detail["collectionEndpoint"]
            print(f"\nCollection ACTIVE!")
            print(f"Endpoint: {endpoint}")
            print(f"\nAdd this to your .env and GitHub Secrets:")
            print(f"  OPENSEARCH_ENDPOINT={endpoint}")
            print(f"  OPENSEARCH_INDEX=career-knowledge")
            return endpoint
        elif status in ("FAILED", "DELETING"):
            print(f"Collection creation failed with status: {status}")
            sys.exit(1)
        time.sleep(20)

if __name__ == "__main__":
    endpoint = create_collection()