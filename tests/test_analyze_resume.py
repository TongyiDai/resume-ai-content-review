from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "analyze_resume.py"
FIXTURE = ROOT / "tests" / "fixtures" / "synthetic_resume.md"
SPEC = importlib.util.spec_from_file_location("analyze_resume", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class AnalyzeResumeTests(unittest.TestCase):
    def test_synthetic_resume_extracts_observations(self) -> None:
        result = MODULE.analyze(FIXTURE.read_text(encoding="utf-8"))
        self.assertTrue(result["reviewability"]["enough_text_for_review"])
        self.assertEqual(result["counts"]["bullets"], 5)
        self.assertGreaterEqual(result["counts"]["quantified_bullets"], 4)
        self.assertGreaterEqual(result["counts"]["template_phrase_hits"], 4)
        self.assertGreaterEqual(result["counts"]["vague_claim_hits"], 1)
        self.assertEqual(result["measurements"]["dominant_opener"], "主导")

    def test_short_text_stops_overall_review(self) -> None:
        result = MODULE.analyze("- 负责产品工作。")
        self.assertFalse(result["reviewability"]["enough_text_for_review"])
        self.assertIn("too short", result["cautions"][0])

    def test_cli_json_is_machine_readable(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), str(FIXTURE), "--format", "json"],
            check=True, capture_output=True, text=True,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["schema_version"], "1.0")
        self.assertIn("do not identify the author", payload["cautions"][0].lower())

    def test_cli_rejects_unknown_file_type(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            source = Path(tmp_dir) / "resume.pdf"
            source.write_bytes(b"not a pdf")
            completed = subprocess.run(
                [sys.executable, str(SCRIPT), str(source)],
                check=False, capture_output=True, text=True,
            )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("Extract PDF/DOCX/image content", completed.stderr)

    def test_markdown_output_keeps_cautions(self) -> None:
        report = MODULE.format_markdown(MODULE.analyze(FIXTURE.read_text(encoding="utf-8")))
        self.assertIn("## Cautions", report)
        self.assertIn("sole basis for an employment decision", report)


if __name__ == "__main__":
    unittest.main()
