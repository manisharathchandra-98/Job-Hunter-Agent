from rag.embeddings import get_embedding
from rag.opensearch_client import client, INDEX_RESUMES, INDEX_JOBS


def retrieve_similar_resumes(resume_text: str, top_k: int = 3) -> list[dict]:
    """Find top-K similar high-scoring resumes to use as RAG examples."""
    embedding = get_embedding(resume_text)
    query = {
        "size": top_k,
        "query": {
            "knn": {
                "embedding": {
                    "vector": embedding,
                    "k": top_k
                }
            }
        },
        "_source": ["resume_text", "match_score", "job_title", "bullet_examples"]
    }
    response = client.search(index=INDEX_RESUMES, body=query)
    hits = response["hits"]["hits"]
    return [
        {
            "score":           h["_score"],
            "match_score":     h["_source"]["match_score"],
            "job_title":       h["_source"]["job_title"],
            "bullet_examples": h["_source"].get("bullet_examples", ""),
            "resume_snippet":  h["_source"]["resume_text"][:500]
        }
        for h in hits
    ]


def retrieve_similar_jobs(job_description: str, top_k: int = 3) -> list[dict]:
    """Find top-K similar job descriptions — useful for skill taxonomy expansion."""
    embedding = get_embedding(job_description)
    query = {
        "size": top_k,
        "query": {
            "knn": {
                "embedding": {
                    "vector": embedding,
                    "k": top_k
                }
            }
        },
        "_source": ["job_description", "required_skills", "job_title"]
    }
    response = client.search(index=INDEX_JOBS, body=query)
    hits = response["hits"]["hits"]
    return [
        {
            "score":           h["_score"],
            "job_title":       h["_source"]["job_title"],
            "required_skills": h["_source"].get("required_skills", []),
            "jd_snippet":      h["_source"]["job_description"][:500]
        }
        for h in hits
    ]