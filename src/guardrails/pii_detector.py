# src/guardrails/pii_detector.py
import re
from dataclasses import dataclass
import logfire


@dataclass
class PIIMatch:
    """Represents a detected PII item."""
    pii_type: str
    original: str
    replacement: str
    start: int
    end: int


# ── Regex patterns for common PII ─────────────────────────────────────────────
PII_PATTERNS = {
    "SSN": (
        r"\b\d{3}-\d{2}-\d{4}\b",
        "[SSN_REDACTED]",
    ),
    "EMAIL": (
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "[EMAIL_REDACTED]",
    ),
    "PHONE_US": (
        r"\b(\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
        "[PHONE_REDACTED]",
    ),
    "CREDIT_CARD": (
        r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
        "[CARD_REDACTED]",
    ),
    "IP_ADDRESS": (
        r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
        "[IP_REDACTED]",
    ),
    "API_KEY": (
        r"\b(sk-|pk-|api-|key-)[A-Za-z0-9]{16,}\b",
        "[API_KEY_REDACTED]",
    ),
    "PASSWORD": (
        r"(?i)(password|passwd|pwd)\s*[:=]\s*\S+",
        "[PASSWORD_REDACTED]",
    ),
}


def detect_pii(text: str) -> list[PIIMatch]:
    """
    Detect all PII in a text string.
    Returns list of PIIMatch objects with location info.
    """
    matches = []

    for pii_type, (pattern, replacement) in PII_PATTERNS.items():
        for match in re.finditer(pattern, text):
            matches.append(PIIMatch(
                pii_type=pii_type,
                original=match.group(),
                replacement=replacement,
                start=match.start(),
                end=match.end(),
            ))

    # Sort by position in text
    matches.sort(key=lambda x: x.start)

    if matches:
        logfire.warning(
            "pii_detected",
            count=len(matches),
            types=[m.pii_type for m in matches],
        )

    return matches


def redact_pii(text: str) -> tuple[str, list[PIIMatch]]:
    """
    Remove all PII from text by replacing with placeholders.

    Returns:
        tuple of (redacted_text, list of what was found)

    Example:
        text = "Email me at john@gmail.com or call 555-123-4567"
        redacted = "Email me at [EMAIL_REDACTED] or call [PHONE_REDACTED]"
    """
    matches = detect_pii(text)

    if not matches:
        return text, []

    # Replace from end to start so positions stay valid
    redacted = text
    for match in reversed(matches):
        redacted = (
            redacted[:match.start]
            + match.replacement
            + redacted[match.end:]
        )

    logfire.info(
        "pii_redacted",
        original_length=len(text),
        redacted_length=len(redacted),
        items_redacted=len(matches),
    )

    return redacted, matches


def has_pii(text: str) -> bool:
    """Quick check if text contains any PII."""
    return len(detect_pii(text)) > 0


def get_pii_report(text: str) -> dict:
    """
    Get a detailed report of PII found in text.
    Useful for logging and auditing.
    """
    matches = detect_pii(text)

    report = {
        "has_pii": len(matches) > 0,
        "total_found": len(matches),
        "types_found": list(set(m.pii_type for m in matches)),
        "details": [
            {
                "type": m.pii_type,
                "replacement": m.replacement,
                # Never log the original! Just show length
                "original_length": len(m.original),
            }
            for m in matches
        ],
    }

    return report