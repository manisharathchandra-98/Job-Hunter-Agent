import json
from rag.embeddings import get_embedding
from rag.opensearch_client import client, INDEX_RESUMES, INDEX_JOBS


def index_completed_match(match_id: str, resume_text: str, job_description: str,
                           match_score: float, job_title: str, industry: str,
                           bullet_examples: list[str]):
    """
    After a match completes with a high score (>=75), index it so future
    candidates can benefit from it as a RAG example.
    """
    if match_score < 75:
        return  # Only index high-quality matches as examples

    resume_embedding = get_embedding(resume_text)
    job_embedding    = get_embedding(job_description)

    # Index resume pattern
    client.index(
        index=INDEX_RESUMES,
        id=f"resume-{match_id}",
        body={
            "embedding":       resume_embedding,
            "resume_text":     resume_text[:2000],
            "match_score":     match_score,
            "job_title":       job_title,
            "industry":        industry,
            "bullet_examples": "\n".join(bullet_examples)
        }
    )

    # Index job description
    client.index(
        index=INDEX_JOBS,
        id=f"job-{match_id}",
        body={
            "embedding":       job_embedding,
            "job_description": job_description[:2000],
            "job_title":       job_title,
            "industry":        industry,
            "required_skills": []  # populated by Agent 1's output
        }
    )