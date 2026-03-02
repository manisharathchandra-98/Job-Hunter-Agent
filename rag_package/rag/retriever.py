"""
RAG retriever — loads career index from S3, searches in memory.
No OpenSearch required.
"""
import os, json, math, logging, boto3

logger   = logging.getLogger(__name__)
REGION   = os.environ.get("AWS_REGION", "us-east-1")
BUCKET   = os.environ.get("RAG_INDEX_BUCKET", "")
S3_KEY   = os.environ.get("RAG_INDEX_KEY", "rag/career_index.json")
EMBED_MODEL = "amazon.titan-embed-text-v1"
TOP_K    = int(os.environ.get("RAG_TOP_K", "4"))

# Cache index in Lambda memory across warm invocations
_index_cache = None

def _load_index() -> list:
    global _index_cache
    if _index_cache is not None:
        return _index_cache
    if not BUCKET:
        raise ValueError("RAG_INDEX_BUCKET env var not set")
    s3  = boto3.client("s3", region_name=REGION)
    obj = s3.get_object(Bucket=BUCKET, Key=S3_KEY)
    _index_cache = json.loads(obj["Body"].read())
    logger.info("RAG index loaded: %d documents", len(_index_cache))
    return _index_cache

def _get_embedding(text: str) -> list:
    bedrock  = boto3.client("bedrock-runtime", region_name=REGION)
    response = bedrock.invoke_model(
        modelId=EMBED_MODEL,
        body=json.dumps({"inputText": text[:8000]})
    )
    return json.loads(response["body"].read())["embedding"]

def _cosine_similarity(a: list, b: list) -> float:
    dot   = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)

def retrieve_career_context(job_title: str, required_skills: list,
                            top_k: int = TOP_K) -> str:
    """
    Find the top-K most relevant career documents for the given role.
    Returns a formatted context string for injection into the Bedrock prompt.
    Falls back to empty string if anything fails.
    """
    try:
        index       = _load_index()
        query_text  = f"Role: {job_title}. Skills: {', '.join(required_skills[:15])}"
        query_vec   = _get_embedding(query_text)

        # Score every document
        scored = []
        for doc in index:
            score = _cosine_similarity(query_vec, doc["embedding"])
            scored.append((score, doc))

        # Take top-K
        top_docs = sorted(scored, key=lambda x: x[0], reverse=True)[:top_k]

        if not top_docs:
            return ""

        parts = []
        for score, doc in top_docs:
            parts.append(
                f"### {doc['title']} (Role: {doc['role']}, relevance: {score:.2f})\n"
                f"{doc['content']}\n"
                f"Key terms: {', '.join(doc.get('keywords', []))}"
            )

        logger.info("RAG: retrieved %d docs for '%s' (top score: %.2f)",
                    len(top_docs), job_title, top_docs[0][0])
        return "\n\n".join(parts)

    except Exception as e:
        logger.warning("RAG retrieval skipped: %s", str(e))
        return ""