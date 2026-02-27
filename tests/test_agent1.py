"""Unit tests for Agent 1 — Job Parser."""
import json
import pytest
from unittest.mock import patch, MagicMock


MOCK_PARSED = {
    "job_title": "Senior Python Developer",
    "company_name": "TechCorp",
    "location": "New York, NY",
    "employment_type": "full-time",
    "key_responsibilities": ["Build APIs", "Design databases"],
    "required_skills": ["Python", "AWS", "PostgreSQL"],
    "nice_to_have_skills": ["Kubernetes"],
    "years_experience_min": 5,
    "years_experience_max": 8,
    "education_required": "Bachelor's in CS",
    "industry": "Software",
    "seniority_level": "senior",
}


def make_bedrock_response(payload: dict):
    mock = MagicMock()
    mock.__getitem__ = lambda s, k: {
        "body": MagicMock(read=lambda: json.dumps({
            "content": [{"text": json.dumps(payload)}]
        }).encode())
    }[k]
    return mock


@patch("boto3.client")
def test_parse_valid_job(mock_boto):
    mock_client = MagicMock()
    mock_client.invoke_model.return_value = make_bedrock_response(MOCK_PARSED)
    mock_boto.return_value = mock_client

    from agents.agent1_parser.lambda_function import lambda_handler
    event = {"job_description": "Senior Python Developer at TechCorp...", "job_id": "test-123"}
    result = lambda_handler(event, MagicMock(aws_request_id="req-1"))

    assert result["status"] == "parsed"
    assert result["job_id"] == "test-123"
    assert result["parsed_job"]["job_title"] == "Senior Python Developer"
    assert "Python" in result["parsed_job"]["required_skills"]


@patch("boto3.client")
def test_parse_missing_description(mock_boto):
    from agents.agent1_parser.lambda_function import lambda_handler
    with pytest.raises(ValueError, match="job_description"):
        lambda_handler({}, MagicMock(aws_request_id="req-2"))


@patch("boto3.client")
def test_parse_truncates_long_description(mock_boto):
    mock_client = MagicMock()
    mock_client.invoke_model.return_value = make_bedrock_response(MOCK_PARSED)
    mock_boto.return_value = mock_client

    from agents.agent1_parser.lambda_function import lambda_handler
    long_text = "A" * 20000
    event = {"job_description": long_text}
    result = lambda_handler(event, MagicMock(aws_request_id="req-3"))
    # Verify truncation happened (job_description stored is max 15000)
    assert len(result["job_description"]) <= 15000