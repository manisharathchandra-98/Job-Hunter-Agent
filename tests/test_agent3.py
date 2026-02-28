"""
tests/test_agent3.py — Unit tests for Agent 3: Market Analyzer
Run: python -m pytest tests/test_agent3.py -v
"""

import json
import unittest
from unittest.mock import patch, MagicMock

PARSED_RESUME = {
    "name": "John Doe",
    "current_role": "Senior Software Engineer",
    "years_experience": 7,
    "location": "San Francisco, CA",
}

EXTRACTED_SKILLS = {
    "skills": [
        {"name": "Python", "level": "senior", "years": 7, "category": "programming_language", "is_primary": True},
        {"name": "AWS",    "level": "senior", "years": 5, "category": "cloud",                "is_primary": True},
        {"name": "Docker", "level": "mid",    "years": 4, "category": "devops",               "is_primary": False},
    ],
    "primary_stack": ["Python", "AWS"],
    "total_skills_count": 3,
}

MOCK_MARKET_RESPONSE = {
    "salary_low": 130000,
    "salary_median": 155000,
    "salary_high": 185000,
    "market_position": "above_average",
    "market_demand": "very_high",
    "earning_potential_6months": 165000,
    "best_suited_roles": ["Senior Backend Engineer", "Cloud Architect", "Staff Engineer"],
    "market_insight": "Python + AWS combination is one of the most in-demand skill sets in 2024.",
}

MOCK_SALARY_TABLE_ITEMS = [
    {"skill": "Python", "level": "senior", "salary_low": 130000, "salary_median": 155000, "salary_high": 185000},
    {"skill": "AWS",    "level": "senior", "salary_low": 140000, "salary_median": 165000, "salary_high": 200000},
]


def _make_bedrock_response(payload: dict) -> dict:
    body_bytes = json.dumps({"content": [{"text": json.dumps(payload)}]}).encode()
    mock_body = MagicMock()
    mock_body.read.return_value = body_bytes
    return {"body": mock_body}


class TestAgent3MarketAnalyzer(unittest.TestCase):

    def _invoke(self, event: dict) -> dict:
        import sys, os, importlib.util

        if "agents.agent3_salary.lambda_function" in sys.modules:
            del sys.modules["agents.agent3_salary.lambda_function"]

        with patch("boto3.client") as mock_boto_client, \
             patch("boto3.resource") as mock_boto_resource:

            # Mock Bedrock
            mock_bedrock = MagicMock()
            mock_bedrock.invoke_model.return_value = _make_bedrock_response(MOCK_MARKET_RESPONSE)
            mock_boto_client.return_value = mock_bedrock

            # Mock DynamoDB SalaryData table
            mock_table = MagicMock()
            mock_table.scan.return_value = {"Items": MOCK_SALARY_TABLE_ITEMS}
            mock_dynamodb = MagicMock()
            mock_dynamodb.Table.return_value = mock_table
            mock_boto_resource.return_value = mock_dynamodb

            spec = importlib.util.spec_from_file_location(
                "lambda_function",
                os.path.join(os.path.dirname(__file__), "..", "agents", "agent3_salary", "lambda_function.py"),
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module.lambda_handler(event, {})

    def _default_event(self):
        return {
            "resume_text": "Senior Python and AWS engineer.",
            "parsed_resume": PARSED_RESUME,
            "extracted_skills": EXTRACTED_SKILLS,
            "match_id": "test-match-001",
            "candidate_id": "test-match-001",
            "job_description": "Senior Python backend engineer",
            "job_id": "job-001",
            "status": "skills_extracted",
        }

    # ── Happy-path tests ──────────────────────────────────────────────────────

    def test_returns_market_analysis_key(self):
        result = self._invoke(self._default_event())
        self.assertIn("market_analysis", result)

    def test_status_is_market_analyzed(self):
        result = self._invoke(self._default_event())
        self.assertEqual(result["status"], "market_analyzed")

    def test_salary_low_present_and_positive(self):
        result = self._invoke(self._default_event())
        salary_low = result["market_analysis"].get("salary_low", 0)
        self.assertGreater(salary_low, 0)

    def test_salary_median_greater_than_low(self):
        result = self._invoke(self._default_event())
        ma = result["market_analysis"]
        self.assertGreater(ma.get("salary_median", 0), ma.get("salary_low", 0))

    def test_salary_high_greater_than_median(self):
        result = self._invoke(self._default_event())
        ma = result["market_analysis"]
        self.assertGreater(ma.get("salary_high", 0), ma.get("salary_median", 0))

    def test_market_position_is_valid(self):
        valid_positions = {"below_average", "average", "above_average", "top_tier"}
        result = self._invoke(self._default_event())
        self.assertIn(result["market_analysis"].get("market_position"), valid_positions)

    def test_market_demand_is_valid(self):
        valid_demand = {"low", "medium", "high", "very_high"}
        result = self._invoke(self._default_event())
        self.assertIn(result["market_analysis"].get("market_demand"), valid_demand)

    def test_best_suited_roles_is_list(self):
        result = self._invoke(self._default_event())
        roles = result["market_analysis"].get("best_suited_roles", [])
        self.assertIsInstance(roles, list)
        self.assertGreater(len(roles), 0)

    def test_market_insight_is_string(self):
        result = self._invoke(self._default_event())
        self.assertIsInstance(result["market_analysis"].get("market_insight", ""), str)

    def test_upstream_keys_passed_through(self):
        result = self._invoke(self._default_event())
        for key in ["match_id", "candidate_id", "job_description", "parsed_resume", "extracted_skills"]:
            self.assertIn(key, result, f"Missing pass-through key: {key}")

    # ── Edge-case tests ───────────────────────────────────────────────────────

    def test_empty_skills_does_not_crash(self):
        event = self._default_event()
        event["extracted_skills"] = {"skills": [], "primary_stack": [], "total_skills_count": 0}
        try:
            result = self._invoke(event)
            self.assertIn("status", result)
        except Exception as e:
            self.fail(f"Empty skills raised: {e}")

    def test_missing_location_does_not_crash(self):
        event = self._default_event()
        event["parsed_resume"] = {**PARSED_RESUME}
        event["parsed_resume"].pop("location", None)
        try:
            result = self._invoke(event)
            self.assertIn("status", result)
        except Exception as e:
            self.fail(f"Missing location raised: {e}")

    def test_salary_values_are_numeric(self):
        result = self._invoke(self._default_event())
        ma = result["market_analysis"]
        for field in ["salary_low", "salary_median", "salary_high"]:
            self.assertIsInstance(ma.get(field, 0), (int, float))


if __name__ == "__main__":
    unittest.main(verbosity=2)