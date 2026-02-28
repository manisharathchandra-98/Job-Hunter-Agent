"""
tests/test_agent1.py — Unit tests for Agent 1: Resume Parser
Run: python -m pytest tests/test_agent1.py -v
     (or: python tests/test_agent1.py)
"""

import json
import unittest
from unittest.mock import patch, MagicMock

# ── Sample resume text used across tests ──────────────────────────────────────
SAMPLE_RESUME = """
John Doe
john.doe@email.com | +1-555-0100 | San Francisco, CA

SUMMARY
Senior Software Engineer with 7 years of experience building scalable backend systems.

EXPERIENCE
Senior Software Engineer — Acme Corp (2020–Present)
  - Led migration of monolith to microservices using Python and AWS Lambda
  - Reduced API latency by 40% through caching strategies

Software Engineer — StartupXYZ (2017–2020)
  - Built REST APIs with Django and PostgreSQL
  - Deployed containerised workloads on Kubernetes

EDUCATION
B.S. Computer Science — State University, 2017

CERTIFICATIONS
AWS Certified Solutions Architect – Associate (2022)
""".strip()

MOCK_BEDROCK_RESPONSE = {
    "name": "John Doe",
    "email": "john.doe@email.com",
    "phone": "+1-555-0100",
    "current_role": "Senior Software Engineer",
    "years_experience": 7,
    "location": "San Francisco, CA",
    "education": [{"degree": "B.S. Computer Science", "institution": "State University", "year": 2017}],
    "certifications": ["AWS Certified Solutions Architect – Associate"],
    "work_history": [
        {"company": "Acme Corp", "role": "Senior Software Engineer", "start": "2020", "end": "Present"},
        {"company": "StartupXYZ", "role": "Software Engineer", "start": "2017", "end": "2020"},
    ],
    "summary": "Senior Software Engineer with 7 years of experience.",
}


def _make_bedrock_response(payload: dict) -> dict:
    """Wrap a dict in the Bedrock response envelope."""
    body_bytes = json.dumps({"content": [{"text": json.dumps(payload)}]}).encode()
    mock_body = MagicMock()
    mock_body.read.return_value = body_bytes
    return {"body": mock_body}


class TestAgent1Parser(unittest.TestCase):

    def _invoke(self, event: dict) -> dict:
        """Helper: import lambda and call handler with a mocked Bedrock client."""
        import importlib, sys

        # Ensure a fresh import each time so env-level globals are re-evaluated
        if "agents.agent1_parser.lambda_function" in sys.modules:
            del sys.modules["agents.agent1_parser.lambda_function"]

        with patch("boto3.client") as mock_boto:
            mock_bedrock = MagicMock()
            mock_bedrock.invoke_model.return_value = _make_bedrock_response(MOCK_BEDROCK_RESPONSE)
            mock_boto.return_value = mock_bedrock

            # Import *after* patching so the module-level boto3.client() call is mocked
            import importlib.util, os
            spec = importlib.util.spec_from_file_location(
                "lambda_function",
                os.path.join(os.path.dirname(__file__), "..", "agents", "agent1_parser", "lambda_function.py"),
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module.lambda_handler(event, {})

    # ── Happy-path tests ──────────────────────────────────────────────────────

    def test_returns_all_required_keys(self):
        """Agent 1 must return match_id, candidate_id, parsed_resume, and status."""
        result = self._invoke({"resume_text": SAMPLE_RESUME, "job_description": "Python engineer role"})
        for key in ["match_id", "candidate_id", "parsed_resume", "status", "resume_text", "job_description"]:
            self.assertIn(key, result, f"Missing key: {key}")

    def test_status_is_parsed(self):
        result = self._invoke({"resume_text": SAMPLE_RESUME, "job_description": "Python engineer"})
        self.assertEqual(result["status"], "parsed")

    def test_parsed_resume_contains_name(self):
        result = self._invoke({"resume_text": SAMPLE_RESUME, "job_description": "Python engineer"})
        self.assertEqual(result["parsed_resume"]["name"], "John Doe")

    def test_parsed_resume_contains_email(self):
        result = self._invoke({"resume_text": SAMPLE_RESUME, "job_description": "Python engineer"})
        self.assertEqual(result["parsed_resume"]["email"], "john.doe@email.com")

    def test_years_experience_is_numeric(self):
        result = self._invoke({"resume_text": SAMPLE_RESUME, "job_description": "Python engineer"})
        self.assertIsInstance(result["parsed_resume"]["years_experience"], (int, float))

    def test_job_description_passed_through(self):
        jd = "Looking for a Python backend engineer."
        result = self._invoke({"resume_text": SAMPLE_RESUME, "job_description": jd})
        self.assertEqual(result["job_description"], jd)

    def test_match_id_generated_when_not_provided(self):
        result = self._invoke({"resume_text": SAMPLE_RESUME, "job_description": "Python engineer"})
        self.assertTrue(len(result["match_id"]) > 0)

    def test_custom_match_id_preserved(self):
        result = self._invoke({"resume_text": SAMPLE_RESUME, "job_description": "Python engineer", "match_id": "test-123"})
        self.assertEqual(result["match_id"], "test-123")

    def test_work_history_is_list(self):
        result = self._invoke({"resume_text": SAMPLE_RESUME, "job_description": "Python engineer"})
        self.assertIsInstance(result["parsed_resume"].get("work_history", []), list)

    def test_certifications_is_list(self):
        result = self._invoke({"resume_text": SAMPLE_RESUME, "job_description": "Python engineer"})
        self.assertIsInstance(result["parsed_resume"].get("certifications", []), list)

    # ── Edge-case tests ───────────────────────────────────────────────────────

    def test_empty_resume_text_raises_validation_error(self):
        """Agent 1 should raise ValueError on empty resume_text — empty resumes are invalid input."""
        with self.assertRaises(ValueError) as ctx:
            self._invoke({"resume_text": "", "job_description": "Python engineer"})
        self.assertIn("resume_text", str(ctx.exception).lower())

    def test_missing_job_description_defaults_to_empty(self):
        result = self._invoke({"resume_text": SAMPLE_RESUME})
        self.assertIn("job_description", result)
        self.assertEqual(result["job_description"], "")

    def test_very_long_resume_does_not_crash(self):
        long_resume = SAMPLE_RESUME + ("\nExperience line...\n" * 500)
        try:
            result = self._invoke({"resume_text": long_resume, "job_description": "Engineer"})
            self.assertIn("status", result)
        except Exception as e:
            self.fail(f"Long resume raised an exception: {e}")

    def test_resume_text_preserved_in_output(self):
        result = self._invoke({"resume_text": SAMPLE_RESUME, "job_description": "Python engineer"})
        self.assertEqual(result["resume_text"], SAMPLE_RESUME)


if __name__ == "__main__":
    unittest.main(verbosity=2)