import re
from collections.abc import Sequence
from typing import Any


DEFAULT_BANNED_TERMS = [
    "guaranteed results",
    "100% risk-free",
    "cure all diseases",
]

DEFAULT_APPROVED_FACTS = [
    "BrandLens helps teams review marketing content.",
    "BrandLens provides explainable brand-rule findings.",
]

CLAIM_PATTERN = re.compile(
    r"(?<!\w)(?:\d[\d,]*(?:-\d[\d,]*)?(?:\.\d+)?\s?(?:%|percent|days?|weeks?|months?|years?|hours?)?"
    r"|best|first|leading|proven|number\s+one)(?!\w)",
    re.IGNORECASE,
)


def _policy_items(
    items: Sequence[dict[str, str] | str],
    id_key: str,
    text_key: str,
) -> list[tuple[str, str]]:
    normalized = []
    for index, item in enumerate(items, start=1):
        if isinstance(item, str):
            normalized.append((f"{id_key}-{index:03d}", item))
        else:
            normalized.append((item[id_key], item[text_key]))
    return normalized


def review_content(
    content: str,
    banned_terms: Sequence[dict[str, str] | str] = DEFAULT_BANNED_TERMS,
    approved_facts: Sequence[dict[str, str] | str] = DEFAULT_APPROVED_FACTS,
) -> dict[str, Any]:
    """Return deterministic, evidence-cited findings against the active brand policy."""
    if not content or not content.strip():
        return {
            "status": "error",
            "message": "Please provide marketing content to review.",
            "findings": [],
            "total_issues": 0,
        }

    rules = _policy_items(banned_terms, "rule_id", "term")
    facts = _policy_items(approved_facts, "fact_id", "text")
    findings: list[dict[str, str]] = []
    covered_spans: list[tuple[int, int]] = []

    for rule_id, term in rules:
        for match in re.finditer(re.escape(term), content, flags=re.IGNORECASE):
            covered_spans.append(match.span())
            findings.append(
                {
                    "rule_id": rule_id,
                    "category": "Banned term",
                    "severity": "high",
                    "confidence": "high",
                    "matched_text": match.group(),
                    "source_id": rule_id,
                    "source_text": f"Do not use “{term}” in published content.",
                    "reason": f"“{term}” is on the active banned-terms list.",
                    "suggestion": "Remove this phrase or replace it with a verified, compliant statement.",
                }
            )

    for sentence_match in re.finditer(r"[^.!?\n]+(?:[.!?]+|$)", content):
        sentence = sentence_match.group()
        sentence_start = sentence_match.start()
        trimmed = sentence.strip()
        if not trimmed:
            continue

        for claim in CLAIM_PATTERN.finditer(sentence):
            start = sentence_start + claim.start()
            end = sentence_start + claim.end()
            supported_by_fact = any(
                re.search(
                    rf"(?<!\w){re.escape(claim.group())}(?!\w)",
                    fact,
                    flags=re.IGNORECASE,
                )
                for _, fact in facts
            )
            if supported_by_fact:
                continue
            if any(start < covered_end and end > covered_start for covered_start, covered_end in covered_spans):
                continue
            findings.append(
                {
                    "rule_id": "BL-CLAIM-001",
                    "category": "Claim needs verification",
                    "severity": "medium",
                    "confidence": "medium",
                    "matched_text": claim.group(),
                    "source_id": "F-REGISTER",
                    "source_text": "No exact matching approved fact was found in the fact register.",
                    "reason": "This numeric or absolute claim is not supported by an exact approved fact.",
                    "suggestion": "Add an approved supporting fact or ask a reviewer to verify this claim.",
                }
            )

    findings.sort(
        key=lambda finding: content.casefold().find(finding["matched_text"].casefold())
    )
    return {
        "status": "success",
        "findings": findings,
        "total_issues": len(findings),
        "review_note": "Automated checks are suggestions. A human reviewer makes the final decision.",
    }
