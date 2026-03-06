"""
Build RAG index: embed all career documents and upload to S3.
Run once: python rag/knowledge_base/build_index.py
"""
import sys
import os
import json
import time
import boto3

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from rag.knowledge_base.career_data import CAREER_DOCUMENTS

REGION      = "us-east-1"
EMBED_MODEL = "amazon.titan-embed-text-v1"
BUCKET      = "job-analyzer-rag-596432516213"
S3_KEY      = "rag/career_index.json"
LOCAL_PATH  = os.path.join(os.path.dirname(__file__), "career_index.json")


def get_embedding(text):
    bedrock = boto3.client("bedrock-runtime", region_name=REGION)
    response = bedrock.invoke_model(
        modelId=EMBED_MODEL,
        body=json.dumps({"inputText": text[:8000]})
    )
    return json.loads(response["body"].read())["embedding"]


def build():
    print(f"Embedding {len(CAREER_DOCUMENTS)} documents...")
    indexed = []

    for i, doc in enumerate(CAREER_DOCUMENTS):
        keywords = doc.get("keywords", [])
        text = doc["title"] + "\n" + doc["content"] + "\nKeywords: " + ", ".join(keywords)

        print(f"  [{i+1}/{len(CAREER_DOCUMENTS)}] {doc['title']}")

        indexed.append({
            "id":        i,
            "role":      doc["role"],
            "doc_type":  doc["doc_type"],
            "title":     doc["title"],
            "content":   doc["content"].strip(),
            "keywords":  keywords,
            "embedding": get_embedding(text)
        })
        time.sleep(0.3)

    # Save locally (Windows-safe path)
    with open(LOCAL_PATH, "w", encoding="utf-8") as f:
        json.dump(indexed, f)
    print(f"\nIndex saved locally: {LOCAL_PATH}")

    # Upload to S3
    boto3.client("s3").upload_file(LOCAL_PATH, BUCKET, S3_KEY)
    print(f"Uploaded to s3://{BUCKET}/{S3_KEY}")
    print("\nDone! RAG index is ready.")
    print(f"Set Lambda env var: RAG_INDEX_BUCKET={BUCKET}")


if __name__ == "__main__":
    build()