"""
tests/test_agent2.py — Unit tests for Agent 2: Skills Extractor
Run: python -m pytest tests/test_agent2.py -v
"""

import json
import unittest
from unittest.mock import patch, MagicMock

PARSED_RESUME = {
    "name": "John Doe",
    "email": "john.doe@email.com",
    "current_role": "Senior Software Engineer",
    "years_experience": 7,
    "work_history": [
        {"company": "Acme Corp", "role": "Senior Software Engineer", "start": "2020", "end": "Present"},
        {"company": "StartupXYZ", "role": "Software Engineer", "start": "2017", "end": "2020"},
    ],
    "certifications": ["AWS Certified Solutions Architect – Associate"],
}

SAMPLE_RESUME_TEXT = "Senior Software Engineer with Python, AWS, Docker, React experience."

MOCK_SKILLS_RESPONSE = {
    "skills": [
        {"name": "Python", "level": "senior", "years": 7, "category": "programming_language", "context": "Backend APIs", "is_primary": True},
        {"name": "AWS", "level": "senior", "years": 5, "category": "cloud", "context": "Lambda, S3, DynamoDB", "is_primary": True},
        {"name": "Docker", "level": "mid", "years": 4, "category": "devops", "context": "Containerisation", "is_primary": False},
        {"name": "React", "level": "junior", "years": 2, "category": "frontend", "context": "Side projects", "is_primary": False},
        {"name": "Django", "level": "mid", "years": 3, "category": "framework", "context": "REST APIs at StartupXYZ", "is_primary": False},
    ],
    "primary_stack": ["Python", "AWS"],
    "total_skills_count": 5,
}


def _make_bedrock_response(payload: dict) -> dict:
    body_bytes = json.dumps({"content": [{"text": json.dumps(payload)}]}).encode()
    mock_body = MagicMock()
    mock_body.read.return_value = body_bytes
    return {"body": mock_body}


class TestAgent2SkillsExtractor(unittest.TestCase):

    def _invoke(self, event: dict) -> dict:
        import sys, os, importlib.util

        if "agents.agent2_skills.lambda_function" in sys.modules:
            del sys.modules["agents.agent2_skills.lambda_function"]

        with patch("boto3.client") as mock_boto:
            mock_bedrock = MagicMock()
            mock_bedrock.invoke_model.return_value = _make_bedrock_response(MOCK_SKILLS_RESPONSE)
            mock_boto.return_value = mock_bedrock

            spec = importlib.util.spec_from_file_location(
                "lambda_function",
                os.path.join(os.path.dirname(__file__), "..", "agents", "agent2_skills", "lambda_function.py"),
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module.lambda_handler(event, {})

    def _default_event(self):
        return {
            "resume_text": SAMPLE_RESUME_TEXT,
            "parsed_resume": PARSED_RESUME,
            "match_id": "test-match-001",
            "candidate_id": "test-match-001",
            "job_description": "Python backend engineer",
            "job_id": "job-001",
        }

    # ── Happy-path tests ──────────────────────────────────────────────────────

    def test_returns_extracted_skills_key(self):
        result = self._invoke(self._default_event())
        self.assertIn("extracted_skills", result)

    def test_status_is_skills_extracted(self):
        result = self._invoke(self._default_event())
        self.assertEqual(result["status"], "skills_extracted")

    def test_skills_is_a_list(self):
        result = self._invoke(self._default_event())
        skills = result["extracted_skills"].get("skills", [])
        self.assertIsInstance(skills, list)

    def test_skills_list_not_empty(self):
        result = self._invoke(self._default_event())
        skills = result["extracted_skills"].get("skills", [])
        self.assertGreater(len(skills), 0)

    def test_each_skill_has_required_fields(self):
        result = self._invoke(self._default_event())
        for skill in result["extracted_skills"].get("skills", []):
            for field in ["name", "level", "years", "category"]:
                self.assertIn(field, skill, f"Skill missing field: {field}")

    def test_skill_level_is_valid_enum(self):
        valid_levels = {"junior", "mid", "senior", "expert"}
        result = self._invoke(self._default_event())
        for skill in result["extracted_skills"].get("skills", []):
            self.assertIn(skill["level"], valid_levels, f"Invalid level: {skill['level']}")

    def test_primary_stack_is_list(self):
        result = self._invoke(self._default_event())
        self.assertIsInstance(result["extracted_skills"].get("primary_stack", []), list)

    def test_total_skills_count_matches_skills_length(self):
        result = self._invoke(self._default_event())
        skills = result["extracted_skills"].get("skills", [])
        count = result["extracted_skills"].get("total_skills_count", 0)
        self.assertEqual(count, len(skills))

    def test_upstream_event_keys_passed_through(self):
        """All keys from the incoming event must be forwarded downstream."""
        event = self._default_event()
        result = self._invoke(event)
        for key in ["match_id", "candidate_id", "job_description", "job_id", "resume_text", "parsed_resume"]:
            self.assertIn(key, result, f"Key not passed through: {key}")

    def test_python_skill_identified_as_primary(self):
        result = self._invoke(self._default_event())
        primary_stack = result["extracted_skills"].get("primary_stack", [])
        self.assertIn("Python", primary_stack)

    # ── Edge-case tests ───────────────────────────────────────────────────────

    def test_empty_resume_text_raises_validation_error(self):
        """Agent 2 should raise ValueError on empty resume_text — skills cannot be extracted without a resume."""
        event = self._default_event()
        event["resume_text"] = ""
        with self.assertRaises(ValueError) as ctx:
            self._invoke(event)
        self.assertIn("resume_text", str(ctx.exception).lower())

    def test_missing_work_history_does_not_crash(self):
        event = self._default_event()
        event["parsed_resume"] = {**PARSED_RESUME, "work_history": []}
        try:
            result = self._invoke(event)
            self.assertIn("status", result)
        except Exception as e:
            self.fail(f"Missing work_history raised: {e}")

    def test_missing_parsed_resume_does_not_crash(self):
        event = self._default_event()
        event.pop("parsed_resume", None)
        try:
            result = self._invoke(event)
            self.assertIn("status", result)
        except Exception as e:
            self.fail(f"Missing parsed_resume raised: {e}")

    def test_years_experience_is_non_negative_for_each_skill(self):
        result = self._invoke(self._default_event())
        for skill in result["extracted_skills"].get("skills", []):
            self.assertGreaterEqual(skill.get("years", 0), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)