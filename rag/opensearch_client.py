import json
import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

REGION       = "us-east-1"
OPENSEARCH_ENDPOINT = "https://<your-domain>.us-east-1.es.amazonaws.com"  # replace
INDEX_RESUMES = "resume-patterns"
INDEX_JOBS    = "job-descriptions"

credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(
    credentials.access_key,
    credentials.secret_key,
    REGION,
    "es",
    session_token=credentials.token
)

client = OpenSearch(
    hosts=[{"host": OPENSEARCH_ENDPOINT.replace("https://", ""), "port": 443}],
    http_auth=awsauth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection
)


def create_indexes():
    """Run once to create k-NN indexes."""
    resume_mapping = {
        "settings": {"index": {"knn": True}},
        "mappings": {
            "properties": {
                "embedding":   {"type": "knn_vector", "dimension": 1536},
                "resume_text": {"type": "text"},
                "match_score": {"type": "float"},
                "job_title":   {"type": "keyword"},
                "industry":    {"type": "keyword"},
                "bullet_examples": {"type": "text"}
            }
        }
    }
    job_mapping = {
        "settings": {"index": {"knn": True}},
        "mappings": {
            "properties": {
                "embedding":       {"type": "knn_vector", "dimension": 1536},
                "job_description": {"type": "text"},
                "required_skills": {"type": "keyword"},
                "job_title":       {"type": "keyword"},
                "industry":        {"type": "keyword"}
            }
        }
    }
    client.indices.create(index=INDEX_RESUMES, body=resume_mapping, ignore=400)
    client.indices.create(index=INDEX_JOBS,    body=job_mapping,    ignore=400)