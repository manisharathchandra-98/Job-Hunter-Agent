"""Unit tests for Agent 2 — Skill Estimator."""
import json
import pytest
from unittest.mock import patch, MagicMock

MOCK_SKILLS = [
    {"name": "Python", "level": "senior", "category": "language",
     "years_required": 5, "market_demand": "very_high", "is_primary": True},
    {"name": "AWS", "level": "mid", "category": "cloud",
     "years_required": 3, "market_demand": "high", "is_primary": True},
    {"name": "Docker", "level": "mid", "category": "devops",
     "years_required": 2, "market_demand": "high", "is_primary": False},
]


def make_bedrock_response(payload):
    mock = MagicMock()
    mock.__getitem__ = lambda s, k: {
        "body": MagicMock(read=lambda: json.dumps({
            "content": [{"text": json.dumps(payload)}]
        }).encode())
    }[k]
    return mock


@patch("boto3.client")
def test_estimate_skills_success(mock_boto):
    mock_client = MagicMock()
    mock_client.invoke_model.return_value = make_bedrock_response(MOCK_SKILLS)
    mock_boto.return_value = mock_client

    from agents.agent2_skills.lambda_function import lambda_handler
    event = {
        "job_id": "test-1",
        "parsed_job": {
            "job_title": "Senior Engineer",
            "seniority_level": "senior",
            "required_skills": ["Python", "AWS", "Docker"],
            "nice_to_have_skills": [],
            "key_responsibilities": ["Build APIs"],
            "years_experience_min": 5,
            "years_experience_max": 8,
        }
    }
    result = lambda_handler(event, None)
    assert result["status"] == "skills_estimated"
    assert result["skills_analysis"]["total_skills"] == 3
    assert result["skills_analysis"]["primary_skills_count"] == 2


@patch("boto3.client")
def test_estimate_skills_missing_parsed_job(mock_boto):
    from agents.agent2_skills.lambda_function import lambda_handler
    with pytest.raises(ValueError, match="parsed_job"):
        lambda_handler({}, None)