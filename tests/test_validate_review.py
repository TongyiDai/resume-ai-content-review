from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "validate_review", ROOT / "scripts" / "validate_review.py"
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ValidateReviewTests(unittest.TestCase):
    def load_fixture(self, name: str):
        return json.loads((ROOT / "tests" / "fixtures" / name).read_text(encoding="utf-8"))

    def test_valid_review_passes(self):
        self.assertEqual(MODULE.validate(self.load_fixture("valid-review.json")), [])

    def test_ai_percentage_and_automatic_rejection_fail(self):
        errors = MODULE.validate(self.load_fixture("invalid-scored-review.json"))
        joined = "\n".join(errors)
        self.assertIn("forbidden scoring or ranking fields", joined)
        self.assertIn("prohibited automatic hiring action", joined)
        self.assertIn("uses an AI percentage", joined)
        self.assertIn("no_automatic_rejection must be true", joined)
        self.assertIn("prohibited_use_acknowledged must be true", joined)

    def test_e2_requires_verification_question(self):
        report = self.load_fixture("valid-review.json")
        report["verification_plan"] = []
        errors = MODULE.validate(report)
        self.assertTrue(any("E2 signals without verification questions" in item for item in errors))

    def test_provenance_requires_e3(self):
        report = self.load_fixture("valid-review.json")
        report["conclusion"]["ai_attribution"] = "provenance_confirmed"
        errors = MODULE.validate(report)
        self.assertIn("provenance_confirmed requires at least one E3 signal", errors)

    def test_alternative_explanation_is_required(self):
        report = self.load_fixture("valid-review.json")
        report["signals"][0]["alternative_explanations"] = []
        errors = MODULE.validate(report)
        self.assertTrue(any("alternative_explanations" in item for item in errors))

    def test_prohibited_action_text_fails_even_when_flags_claim_safety(self):
        report = self.load_fixture("valid-review.json")
        report["conclusion"]["summary"] = "建议直接淘汰这名候选人"
        errors = MODULE.validate(report)
        self.assertTrue(any("prohibited automatic hiring action" in item for item in errors))


if __name__ == "__main__":
    unittest.main()
