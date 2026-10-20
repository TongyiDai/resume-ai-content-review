from __future__ import annotations

import re
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_TEXT = (ROOT / "SKILL.md").read_text(encoding="utf-8")
FRONTMATTER = SKILL_TEXT.split("---", 2)[1]


class SkillContractTests(unittest.TestCase):
    def test_frontmatter_name_matches_directory(self):
        self.assertIn("name: resume-ai-content-review", FRONTMATTER)

    def test_description_contains_positive_triggers(self):
        for trigger in ("简历 AI 含量", "AI 写的简历", "ChatGPT 简历", "候选人材料真实性"):
            with self.subTest(trigger=trigger):
                self.assertIn(trigger, FRONTMATTER)

    def test_core_guardrails_are_explicit(self):
        for guardrail in ("不输出伪精确 AI 百分比", "不得自动淘汰候选人", "禁止按“AI 味”给候选人排序"):
            with self.subTest(guardrail=guardrail):
                self.assertIn(guardrail, SKILL_TEXT)

    def test_reference_links_resolve(self):
        refs = re.findall(r"\[[^]]+\]\((references/[^)]+)\)", SKILL_TEXT)
        self.assertGreaterEqual(len(refs), 4)
        for ref in refs:
            with self.subTest(ref=ref):
                self.assertTrue((ROOT / ref).is_file())

    def test_skill_body_stays_concise(self):
        self.assertLessEqual(len(SKILL_TEXT.splitlines()), 500)

    def test_trigger_inventory_is_balanced_and_unique(self):
        inventory = json.loads((ROOT / "tests" / "trigger-cases.json").read_text(encoding="utf-8"))
        self.assertEqual(len(inventory["positive"]), 10)
        self.assertEqual(len(inventory["negative"]), 10)
        all_cases = inventory["positive"] + inventory["negative"]
        self.assertEqual(len(all_cases), len(set(all_cases)))
        self.assertTrue(all(isinstance(item, str) and item.strip() for item in all_cases))


if __name__ == "__main__":
    unittest.main()
