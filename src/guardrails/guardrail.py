# src/guardrails/guardrail.py
"""
Guardrail layer that wraps around all inputs and outputs.

Flow:
    User message
        ↓
    [PII Check on input]
        ↓
    Agent/Memory/RAG
        ↓
    [PII Check on output]
        ↓
    Safe response to user
"""
import logfire
from src.guardrails.pii_detector import redact_pii, has_pii, get_pii_report


class PIIGuardrail:
    """
    Guardrail that removes PII from messages and memory.

    Use this as a wrapper around any text before:
    - Storing in memory
    - Storing in conversation history logs
    - Sending to external services
    """

    def __init__(self, strict_mode: bool = False):
        """
        strict_mode: if True, block messages with PII entirely
                     if False, redact and continue (default)
        """
        self.strict_mode = strict_mode
        self.total_redacted = 0
        self.total_checked = 0

    def process_input(self, text: str) -> tuple[str, bool]:
        """
        Process user input through PII guardrail.

        Returns:
            (processed_text, was_modified)
        """
        self.total_checked += 1

        if not has_pii(text):
            return text, False

        # PII found!
        report = get_pii_report(text)
        logfire.warning(
            "guardrail_pii_in_input",
            types_found=report["types_found"],
            count=report["total_found"],
        )

        if self.strict_mode:
            # Block the message entirely
            blocked_msg = (
                f"⚠️ Your message contained {report['total_found']} "
                f"PII item(s) ({', '.join(report['types_found'])}). "
                f"Please remove sensitive information before sending."
            )
            return blocked_msg, True

        # Redact and continue
        redacted, matches = redact_pii(text)
        self.total_redacted += len(matches)

        print(
            f"⚠️  PII detected and redacted: "
            f"{[m.pii_type for m in matches]}"
        )

        return redacted, True

    def process_for_storage(self, text: str) -> str:
        """
        Clean text before storing in memory or logs.
        Always redacts (never blocks) for storage.

        Use this before:
        - saving to memory store
        - saving conversation summaries
        - logging
        """
        redacted, matches = redact_pii(text)

        if matches:
            logfire.info(
                "guardrail_storage_redaction",
                items_redacted=len(matches),
                types=[m.pii_type for m in matches],
            )

        return redacted

    def process_memory_content(self, content: str) -> str:
        """
        Specifically for cleaning memory content before storage.
        """
        return self.process_for_storage(content)

    def get_stats(self) -> dict:
        """Get guardrail statistics."""
        return {
            "total_checked": self.total_checked,
            "total_pii_items_redacted": self.total_redacted,
            "strict_mode": self.strict_mode,
        }


# Global guardrail instance
pii_guardrail = PIIGuardrail(strict_mode=False)