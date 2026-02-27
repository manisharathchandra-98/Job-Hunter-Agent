"""Unit tests for Agent 3 — Salary Analyzer."""
import json
import pytest
from unittest.mock import patch, MagicMock

MOCK_SALARY = {
    "salary_low": 140000, "salary_median": 175000, "salary_high": 220000,
    "percentile_25": 155000, "percentile_75": 200000, "currency": "USD",
    "confidence": "high", "market_insights": "Strong demand for senior engineers.",
    "factors": ["AWS skills premium", "NYC location"], "remote_premium_pct": 5,
}


def make_bedrock_response(payload):
    mock = MagicMock()
    mock.__getitem__ = lambda s, k: {
        "body": MagicMock(read=lambda: json.dumps({
            "content": [{"text": json.dumps(payload)}]
        }).encode())
    }[k]
    return mock


@patch("boto3.resource")
@patch("boto3.client")
def test_salary_analysis_success(mock_boto_client, mock_boto_resource):
    mock_client = MagicMock()
    mock_client.invoke_model.return_value = make_bedrock_response(MOCK_SALARY)
    mock_boto_client.return_value = mock_client

    mock_table = MagicMock()
    mock_table.query.return_value = {"Items": []}
    mock_table.scan.return_value = {"Items": []}
    mock_boto_resource.return_value.Table.return_value = mock_table

    from agents.agent3_salary.lambda_function import lambda_handler
    event = {
        "job_id": "test-1",
        "parsed_job": {
            "job_title": "Senior Engineer", "seniority_level": "senior",
            "location": "New York", "required_skills": ["Python", "AWS"],
            "years_experience_min": 5, "years_experience_max": 8,
        },
        "skills_analysis": {"skills": [
            {"name": "Python", "is_primary": True},
            {"name": "AWS", "is_primary": True},
        ]},
    }
    result = lambda_handler(event, None)
    assert result["status"] == "salary_analyzed"
    assert result["salary_data"]["salary_low"] == 140000
    assert result["salary_data"]["confidence"] == "high"