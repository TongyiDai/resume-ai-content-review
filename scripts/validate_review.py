#!/usr/bin/env python3
"""Validate a machine-readable resume AI content review report.

The validator checks the public output contract and high-risk hiring guardrails.
It does not decide whether the underlying analysis is factually correct.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Set


AI_ATTRIBUTIONS = {
    "insufficient_evidence",
    "assistance_compatible_signals",
    "provenance_confirmed",
}
VERIFICATION_NEEDS = {
    "normal",
    "targeted",
    "enhanced",
    "insufficient_information",
}
EVIDENCE_LEVELS = {"E1", "E2", "E3"}
IMPLICATIONS = {"style_only", "verify_claim", "provenance"}
PROVENANCE_BASES = {
    "explicit_disclosure",
    "documented_edit_history",
    "verifiable_watermark_or_metadata",
}
NEXT_STEPS = {
    "standard_process",
    "structured_verification",
    "manual_review_due_to_insufficient_text",
}
FAIRNESS_FLAGS = {
    "no_automatic_rejection",
    "no_candidate_ranking",
    "no_protected_attribute_inference",
    "language_background_considered",
    "template_and_editor_alternatives_considered",
    "pii_minimized",
}
FORBIDDEN_KEYS = {
    "score",
    "risk_score",
    "ai_score",
    "ai_percentage",
    "probability",
    "ranking",
    "rank",
}
PERCENT_RE = re.compile(r"(?:AI|人工智能|机器).{0,12}\b\d{1,3}(?:\.\d+)?\s*%", re.I)
CERTAINTY_RE = re.compile(
    r"(?:definitely|certainly|proved?|confirmed)\s+(?:ai|machine)[ -](?:written|generated)|"
    r"(?:确定|肯定|实锤|证明).{0,8}(?:AI|人工智能|机器)(?:写|生成)",
    re.I,
)
PROHIBITED_ACTION_RE = re.compile(
    r"(?:建议|应当|应该|直接|自动).{0,8}(?:淘汰|拒绝|刷掉)|"
    r"(?:rank|reject|eliminate|disqualify).{0,20}(?:candidate|applicant).{0,20}(?:ai|machine)|"
    r"(?:candidate|applicant).{0,20}(?:rank|reject|eliminate|disqualify).{0,20}(?:ai|machine)",
    re.I,
)


def _is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _forbidden_key_paths(value: Any, path: str = "$") -> List[str]:
    hits: List[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = "{}.{}".format(path, key)
            if str(key).lower() in FORBIDDEN_KEYS:
                hits.append(child_path)
            hits.extend(_forbidden_key_paths(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            hits.extend(_forbidden_key_paths(child, "{}[{}]".format(path, index)))
    return hits


def _string_paths(value: Any, path: str = "$") -> List[tuple]:
    values: List[tuple] = []
    if isinstance(value, dict):
        for key, child in value.items():
            values.extend(_string_paths(child, "{}.{}".format(path, key)))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            values.extend(_string_paths(child, "{}[{}]".format(path, index)))
    elif isinstance(value, str):
        values.append((path, value))
    return values


def validate(report: Any) -> List[str]:
    errors: List[str] = []
    if not isinstance(report, dict):
        return ["report root must be a JSON object"]

    required = {
        "schema_version",
        "subject",
        "conclusion",
        "signals",
        "counter_evidence",
        "verification_plan",
        "fairness_checks",
        "hiring_action",
    }
    missing = sorted(required - set(report))
    if missing:
        errors.append("missing top-level fields: {}".format(", ".join(missing)))

    forbidden_paths = _forbidden_key_paths(report)
    if forbidden_paths:
        errors.append("forbidden scoring or ranking fields: {}".format(", ".join(forbidden_paths)))
    prohibited_actions = [
        path for path, value in _string_paths(report) if PROHIBITED_ACTION_RE.search(value)
    ]
    if prohibited_actions:
        errors.append("prohibited automatic hiring action in: {}".format(", ".join(prohibited_actions)))

    if report.get("schema_version") != "1.0":
        errors.append("schema_version must be '1.0'")

    subject = report.get("subject")
    if not isinstance(subject, dict):
        errors.append("subject must be an object")
    else:
        if not _is_nonempty_string(subject.get("anonymous_id")):
            errors.append("subject.anonymous_id must be a non-empty string")
        if not isinstance(subject.get("sections_reviewed"), list):
            errors.append("subject.sections_reviewed must be an array")
        if not isinstance(subject.get("job_context_provided"), bool):
            errors.append("subject.job_context_provided must be boolean")
        if not isinstance(subject.get("text_limitations"), list):
            errors.append("subject.text_limitations must be an array")

    conclusion = report.get("conclusion")
    attribution = None
    if not isinstance(conclusion, dict):
        errors.append("conclusion must be an object")
    else:
        attribution = conclusion.get("ai_attribution")
        if attribution not in AI_ATTRIBUTIONS:
            errors.append("conclusion.ai_attribution has an unsupported value")
        if conclusion.get("verification_need") not in VERIFICATION_NEEDS:
            errors.append("conclusion.verification_need has an unsupported value")
        summary = conclusion.get("summary")
        if not _is_nonempty_string(summary):
            errors.append("conclusion.summary must be a non-empty string")
        elif PERCENT_RE.search(summary) or CERTAINTY_RE.search(summary):
            errors.append("conclusion.summary overstates AI attribution or uses an AI percentage")

    signals = report.get("signals")
    signal_ids: Set[str] = set()
    e2_ids: Set[str] = set()
    e3_count = 0
    if not isinstance(signals, list):
        errors.append("signals must be an array")
        signals = []
    for index, signal in enumerate(signals):
        prefix = "signals[{}]".format(index)
        if not isinstance(signal, dict):
            errors.append("{} must be an object".format(prefix))
            continue
        signal_id = signal.get("id")
        if not _is_nonempty_string(signal_id):
            errors.append("{}.id must be a non-empty string".format(prefix))
        elif signal_id in signal_ids:
            errors.append("duplicate signal id: {}".format(signal_id))
        else:
            signal_ids.add(signal_id)
        level = signal.get("evidence_level")
        if level not in EVIDENCE_LEVELS:
            errors.append("{}.evidence_level must be E1, E2, or E3".format(prefix))
        if level == "E2" and _is_nonempty_string(signal_id):
            e2_ids.add(signal_id)
        if level == "E3":
            e3_count += 1
            if signal.get("provenance_basis") not in PROVENANCE_BASES:
                errors.append("{}.provenance_basis is required for E3".format(prefix))
        for key in ("excerpt", "observation", "why_relevant"):
            if not _is_nonempty_string(signal.get(key)):
                errors.append("{}.{} must be a non-empty string".format(prefix, key))
        alternatives = signal.get("alternative_explanations")
        if not isinstance(alternatives, list) or not alternatives or not all(
            _is_nonempty_string(item) for item in alternatives
        ):
            errors.append("{}.alternative_explanations must contain at least one explanation".format(prefix))
        implication = signal.get("implication")
        if implication not in IMPLICATIONS:
            errors.append("{}.implication has an unsupported value".format(prefix))
        expected = {"E1": "style_only", "E2": "verify_claim", "E3": "provenance"}
        if level in expected and implication != expected[level]:
            errors.append("{}.implication does not match its evidence level".format(prefix))

    if attribution == "provenance_confirmed" and e3_count == 0:
        errors.append("provenance_confirmed requires at least one E3 signal")
    if attribution != "provenance_confirmed" and e3_count:
        errors.append("E3 evidence requires conclusion.ai_attribution=provenance_confirmed")

    counter_evidence = report.get("counter_evidence")
    if not isinstance(counter_evidence, list):
        errors.append("counter_evidence must be an array")
    else:
        for index, item in enumerate(counter_evidence):
            prefix = "counter_evidence[{}]".format(index)
            if not isinstance(item, dict):
                errors.append("{} must be an object".format(prefix))
                continue
            for key in ("excerpt", "observation", "why_it_matters"):
                if not _is_nonempty_string(item.get(key)):
                    errors.append("{}.{} must be a non-empty string".format(prefix, key))

    verification_plan = report.get("verification_plan")
    covered_ids: Set[str] = set()
    if not isinstance(verification_plan, list):
        errors.append("verification_plan must be an array")
        verification_plan = []
    for index, item in enumerate(verification_plan):
        prefix = "verification_plan[{}]".format(index)
        if not isinstance(item, dict):
            errors.append("{} must be an object".format(prefix))
            continue
        targets = item.get("target_signal_ids")
        if not isinstance(targets, list) or not all(isinstance(target, str) for target in targets):
            errors.append("{}.target_signal_ids must be an array of strings".format(prefix))
        else:
            unknown = set(targets) - signal_ids
            if unknown:
                errors.append("{} references unknown signals: {}".format(prefix, ", ".join(sorted(unknown))))
            covered_ids.update(targets)
        for key in ("primary_question", "follow_up", "good_evidence"):
            if not _is_nonempty_string(item.get(key)):
                errors.append("{}.{} must be a non-empty string".format(prefix, key))
    uncovered_e2 = sorted(e2_ids - covered_ids)
    if uncovered_e2:
        errors.append("E2 signals without verification questions: {}".format(", ".join(uncovered_e2)))

    fairness = report.get("fairness_checks")
    if not isinstance(fairness, dict):
        errors.append("fairness_checks must be an object")
    else:
        for flag in sorted(FAIRNESS_FLAGS):
            if fairness.get(flag) is not True:
                errors.append("fairness_checks.{} must be true".format(flag))

    action = report.get("hiring_action")
    if not isinstance(action, dict):
        errors.append("hiring_action must be an object")
    else:
        if action.get("next_step") not in NEXT_STEPS:
            errors.append("hiring_action.next_step has an unsupported value")
        if action.get("prohibited_use_acknowledged") is not True:
            errors.append("hiring_action.prohibited_use_acknowledged must be true")
        if not _is_nonempty_string(action.get("note")):
            errors.append("hiring_action.note must be a non-empty string")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path, help="Path to a JSON review report")
    parser.add_argument("--compact", action="store_true", help="Emit compact JSON")
    args = parser.parse_args()

    try:
        report = json.loads(args.report.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        result: Dict[str, Any] = {"ok": False, "errors": [str(exc)]}
        print(json.dumps(result, ensure_ascii=False, indent=None if args.compact else 2))
        return 2

    errors = validate(report)
    result = {"ok": not errors, "errors": errors}
    print(json.dumps(result, ensure_ascii=False, indent=None if args.compact else 2))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
