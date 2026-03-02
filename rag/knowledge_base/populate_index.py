"""
Run once to embed all career documents and upload to S3.
python rag/knowledge_base/build_index.py --bucket your-bucket-name
"""
import argparse, boto3, json, time, os, sys

REGION      = "us-east-1"
EMBED_MODEL = "amazon.titan-embed-text-v1"

def get_embedding(text: str) -> list:
    bedrock = boto3.client("bedrock-runtime", region_name=REGION)
    response = bedrock.invoke_model(
        modelId=EMBED_MODEL,
        body=json.dumps({"inputText": text[:8000]})
    )
    return json.loads(response["body"].read())["embedding"]

def build_index(bucket: str):
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
    from rag.knowledge_base.career_data import CAREER_DOCUMENTS

    print(f"Embedding {len(CAREER_DOCUMENTS)} documents...")
    indexed = []
    for i, doc in enumerate(CAREER_DOCUMENTS):
        text = f"{doc['title']}\n{doc['content']}\nKeywords: {', '.join(doc.get('keywords', []))}"
        print(f"  [{i+1}/{len(CAREER_DOCUMENTS)}] {doc['title']}")
        embedding = get_embedding(text)
        indexed.append({
            "id":        i,
            "role":      doc["role"],
            "doc_type":  doc["doc_type"],
            "title":     doc["title"],
            "content":   doc["content"].strip(),
            "keywords":  doc.get("keywords", []),
            "embedding": embedding
        })
        time.sleep(0.3)  # avoid Bedrock throttling

    # Save locally first
    local_path = "/tmp/career_index.json"
    with open(local_path, "w") as f:
        json.dump(indexed, f)
    print(f"\nIndex built: {len(indexed)} documents")

    # Upload to S3
    s3_key = "rag/career_index.json"
    boto3.client("s3").upload_file(local_path, bucket, s3_key)
    print(f"Uploaded to s3://{bucket}/{s3_key}")
    print(f"\nSet env var: RAG_INDEX_BUCKET={bucket}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--bucket", required=True, help="S3 bucket name")
    args = parser.parse_args()
    build_index(args.bucket)