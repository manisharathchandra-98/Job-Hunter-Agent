import json
import boto3

bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")
EMBEDDING_MODEL = "amazon.titan-embed-text-v1"  # 1536-dim, free tier eligible


def get_embedding(text: str) -> list[float]:
    """Generate a 1536-dim vector from text using Amazon Titan."""
    # Titan has a 8192 token input limit
    truncated = text[:8000]
    response = bedrock.invoke_model(
        modelId=EMBEDDING_MODEL,
        body=json.dumps({"inputText": truncated})
    )
    body = json.loads(response["body"].read())
    return body["embedding"]