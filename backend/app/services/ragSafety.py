"""
RAG safety utilities: prompt injection detection and PII handling.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_INJECTION_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"ignore\s+(all|previous|earlier)\s+instructions",
        r"system\s+prompt",
        r"developer\s+message",
        r"you\s+are\s+chatgpt",
        r"do\s+not\s+follow",
        r"override\s+instructions",
        r"tool\s+call",
    ]
]

_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_PHONE_RE = re.compile(r"\b(?:\+?\d[\d\-\s]{7,}\d)\b")
_AADHAAR_RE = re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b")


@dataclass
class SafetySignals:
    prompt_injection: bool
    pii_matches: dict[str, int]
    stripped_lines: int = 0


def detect_prompt_injection(text: str) -> bool:
    return any(pattern.search(text) for pattern in _INJECTION_PATTERNS)


def detect_pii(text: str) -> dict[str, int]:
    return {
        "email": len(_EMAIL_RE.findall(text)),
        "phone": len(_PHONE_RE.findall(text)),
        "aadhaar": len(_AADHAAR_RE.findall(text)),
    }


def redact_pii(text: str) -> str:
    text = _EMAIL_RE.sub("[REDACTED_EMAIL]", text)
    text = _AADHAAR_RE.sub("[REDACTED_AADHAAR]", text)
    return _PHONE_RE.sub("[REDACTED_PHONE]", text)


def strip_prompt_injection(text: str) -> tuple[str, int]:
    """Remove lines that match prompt injection patterns."""
    lines = text.splitlines()
    kept_lines = []
    stripped = 0
    for line in lines:
        if any(pattern.search(line) for pattern in _INJECTION_PATTERNS):
            stripped += 1
            continue
        kept_lines.append(line)
    return "\n".join(kept_lines), stripped


def analyze_text(text: str) -> SafetySignals:
    pii_matches = detect_pii(text)
    return SafetySignals(
        prompt_injection=detect_prompt_injection(text),
        pii_matches=pii_matches,
    )
