"""
Lightweight text extraction utilities for HTML/text sources.
"""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

_WHITESPACE_RE = re.compile(r"\s+")


def extract_text_from_html(html: str) -> str:
    """Extract readable text from HTML while stripping scripts/styles."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = soup.get_text(separator=" ")
    return normalize_whitespace(text)


def normalize_whitespace(text: str) -> str:
    """Normalize whitespace to single spaces and trim."""
    return _WHITESPACE_RE.sub(" ", text).strip()
