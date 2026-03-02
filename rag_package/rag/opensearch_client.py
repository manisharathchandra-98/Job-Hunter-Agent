"""
OpenSearch client — disabled in favour of S3-based vector store.
Kept for future use if OpenSearch is enabled.
"""

def get_opensearch_client():
    raise NotImplementedError(
        "OpenSearch is not configured. Using S3-based vector store instead. "
        "See rag/retriever.py"
    )