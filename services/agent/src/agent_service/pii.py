"""Pluggable PII/content-policy hook on the answer path (Section 9.2, ADR-0005).

The basic filter catches obvious identifier shapes; real deployments plug a
proper classifier into the same seam.
"""

import re


class NoopPiiFilter:
    def filter(self, text: str) -> tuple[str, int]:
        return text, 0


class BasicPiiFilter:
    _PATTERNS = [
        (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[REDACTED-SSN]"),
        (re.compile(r"\b\d{13,16}\b"), "[REDACTED-CARD]"),
    ]

    def filter(self, text: str) -> tuple[str, int]:
        redactions = 0
        for pattern, replacement in self._PATTERNS:
            text, count = pattern.subn(replacement, text)
            redactions += count
        return text, redactions


def build_pii_filter(mode: str):
    return NoopPiiFilter() if mode == "off" else BasicPiiFilter()
