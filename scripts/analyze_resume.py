#!/usr/bin/env python3
"""Extract observable resume-writing features without deciding authorship.

This dependency-free helper locates text for human review. Its output is not an
AI-generated-text probability, an authorship finding, or an employment decision.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

VERSION = "1.0.2"
MIN_REVIEW_CHARS = 120
MIN_REVIEW_BULLETS = 3

BULLET_RE = re.compile(r"^\s*(?:[-*•▪◦]|\d+[.)、])\s+(.+?)\s*$")
NUMBER_RE = re.compile(
    r"(?:\b\d+(?:[.,]\d+)?\s*(?:%|x|倍|万|亿|k|m|人|天|月|年|小时|次|条|项)"
    r"|[$¥￥€£]\s*\d+(?:[.,]\d+)?|\d+(?:[.,]\d+)?%)",
    re.IGNORECASE,
)

TEMPLATE_PHRASES: Sequence[Tuple[str, str]] = (
    ("负责并推动", r"负责并推动"),
    ("深度参与", r"深度参与"),
    ("显著提升", r"显著(?:提升|改善|优化)"),
    ("赋能业务", r"赋能(?:业务|团队|组织)"),
    ("从0到1", r"从\s*0\s*到\s*1"),
    ("end-to-end", r"\bend[- ]to[- ]end\b"),
    ("results-driven", r"\bresults?[- ]driven\b"),
    ("proven track record", r"\bproven track record\b"),
    ("leveraged", r"\bleverag(?:e|ed|ing)\b"),
)

VAGUE_CLAIMS: Sequence[Tuple[str, str]] = (
    ("显著/大幅但无口径", r"(?:显著|大幅|极大)(?:提升|提高|降低|减少|优化|改善)"),
    ("行业领先/世界级", r"(?:行业领先|业界领先|世界级|顶尖)"),
    ("many/various without scope", r"\b(?:many|various|numerous|significant)\b"),
    ("best-in-class/world-class", r"\b(?:best[- ]in[- ]class|world[- ]class|industry[- ]leading)\b"),
)

ACTION_OPENERS = (
    "负责", "主导", "推动", "搭建", "建立", "设计", "开发", "实现",
    "优化", "完成", "管理", "协调", "分析", "制定", "交付", "组织",
    "led", "managed", "built", "designed", "developed", "implemented",
    "optimized", "created", "drove", "delivered", "owned", "analyzed",
)


def read_text(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(f"Input file not found: {source}")
    if source.suffix.lower() not in {".txt", ".md", ".markdown"}:
        raise ValueError(
            "Unsupported input type. Extract PDF/DOCX/image content to UTF-8 text or Markdown first."
        )
    return source.read_text(encoding="utf-8")


def normalize(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n").strip()


def extract_bullets(text: str) -> List[Dict[str, object]]:
    bullets: List[Dict[str, object]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        match = BULLET_RE.match(line)
        if match:
            bullets.append({"line": line_number, "text": match.group(1).strip()})
    return bullets


def clip(text: str, limit: int = 100) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    return compact if len(compact) <= limit else compact[: limit - 1] + "…"


def first_token(text: str) -> str:
    cleaned = re.sub(r"^[^\w\u4e00-\u9fff]+", "", text).strip().lower()
    english = re.match(r"[a-z]+", cleaned)
    if english:
        return english.group(0)
    for opener in ACTION_OPENERS:
        if cleaned.startswith(opener.lower()):
            return opener.lower()
    chinese = re.match(r"[\u4e00-\u9fff]{1,4}", cleaned)
    return chinese.group(0)[:2] if chinese else cleaned[:12]


def phrase_hits(
    bullets: Sequence[Dict[str, object]], patterns: Sequence[Tuple[str, str]]
) -> List[Dict[str, object]]:
    hits: List[Dict[str, object]] = []
    for bullet in bullets:
        value = str(bullet["text"])
        for label, pattern in patterns:
            if re.search(pattern, value, flags=re.IGNORECASE):
                hits.append(
                    {"line": bullet["line"], "label": label, "excerpt": clip(value)}
                )
    return hits


def safe_ratio(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 3) if denominator else 0.0


def coefficient_of_variation(values: Iterable[int]) -> float:
    materialized = list(values)
    if len(materialized) < 2 or statistics.mean(materialized) == 0:
        return 0.0
    return round(statistics.pstdev(materialized) / statistics.mean(materialized), 3)


def analyze(text: str) -> Dict[str, object]:
    clean = normalize(text)
    bullets = extract_bullets(clean)
    bullet_texts = [str(item["text"]) for item in bullets]
    quantified = [item for item in bullets if NUMBER_RE.search(str(item["text"]))]
    template_hits = phrase_hits(bullets, TEMPLATE_PHRASES)
    vague_hits = phrase_hits(bullets, VAGUE_CLAIMS)

    openers = [first_token(value) for value in bullet_texts if first_token(value)]
    opener_counts = Counter(openers)
    dominant_opener, dominant_count = ("", 0)
    if opener_counts:
        dominant_opener, dominant_count = opener_counts.most_common(1)[0]

    duplicates = []
    exact_counts = Counter(re.sub(r"\s+", " ", value).strip().lower() for value in bullet_texts)
    for value, count in exact_counts.items():
        if count > 1:
            duplicates.append({"count": count, "excerpt": clip(value)})

    enough_text = len(clean) >= MIN_REVIEW_CHARS and len(bullets) >= MIN_REVIEW_BULLETS
    cautions = [
        "These measurements do not identify the author or prove AI use.",
        "Template phrases, uniform structure, and polished language have ordinary human explanations.",
        "Do not use this output as the sole basis for an employment decision.",
    ]
    if not enough_text:
        cautions.insert(0, "The sample is too short for an overall signal judgment.")

    return {
        "schema_version": "1.0",
        "tool_version": VERSION,
        "reviewability": {
            "enough_text_for_review": enough_text,
            "minimum_characters": MIN_REVIEW_CHARS,
            "minimum_bullets": MIN_REVIEW_BULLETS,
        },
        "counts": {
            "characters": len(clean),
            "nonempty_lines": sum(1 for line in clean.splitlines() if line.strip()),
            "bullets": len(bullets),
            "quantified_bullets": len(quantified),
            "template_phrase_hits": len(template_hits),
            "vague_claim_hits": len(vague_hits),
        },
        "measurements": {
            "quantified_bullet_ratio": safe_ratio(len(quantified), len(bullets)),
            "bullet_length_cv": coefficient_of_variation(len(value) for value in bullet_texts),
            "dominant_opener": dominant_opener,
            "dominant_opener_ratio": safe_ratio(dominant_count, len(openers)),
            "exact_duplicate_groups": duplicates,
        },
        "observations": {
            "template_phrases": template_hits,
            "vague_claims": vague_hits,
            "quantified_examples": [
                {"line": item["line"], "excerpt": clip(str(item["text"]))}
                for item in quantified[:8]
            ],
        },
        "cautions": cautions,
    }


def format_markdown(result: Dict[str, object]) -> str:
    counts = result["counts"]
    measurements = result["measurements"]
    observations = result["observations"]
    reviewability = result["reviewability"]
    lines = [
        "# Resume text feature report",
        "",
        f"- Reviewable sample: **{'yes' if reviewability['enough_text_for_review'] else 'no'}**",
        f"- Characters / bullets: **{counts['characters']} / {counts['bullets']}**",
        f"- Quantified bullets: **{counts['quantified_bullets']}** ({measurements['quantified_bullet_ratio']:.1%})",
        f"- Bullet-length variation (CV): **{measurements['bullet_length_cv']}**",
        f"- Dominant opener: **{measurements['dominant_opener'] or 'n/a'}** ({measurements['dominant_opener_ratio']:.1%})",
        f"- Template-phrase hits: **{counts['template_phrase_hits']}**",
        f"- Vague-claim hits: **{counts['vague_claim_hits']}**",
        "",
        "## Located observations",
        "",
    ]
    located = list(observations["template_phrases"]) + list(observations["vague_claims"])
    if not located:
        lines.append("- No configured phrase patterns were located.")
    else:
        for item in located:
            lines.append(f"- Line {item['line']} · {item['label']}: “{item['excerpt']}”")
    lines.extend(["", "## Cautions", ""] )
    lines.extend(f"- {item}" for item in result["cautions"])
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract observable resume-writing features without claiming AI authorship."
    )
    parser.add_argument("input", help="UTF-8 .txt/.md path, or - for standard input")
    parser.add_argument(
        "--format", choices=("json", "markdown"), default="markdown", help="Output format"
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        text = read_text(args.input)
        result = analyze(text)
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_markdown(result), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
