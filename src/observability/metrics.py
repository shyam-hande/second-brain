# src/observability/metrics.py
import logfire
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class AgentMetrics:
    """Track metrics for each agent call."""
    total_calls: int = 0
    total_errors: int = 0
    call_times: list[float] = field(default_factory=list)
    confidence_counts: dict = field(default_factory=lambda: {
        "high": 0, "medium": 0, "low": 0
    })

    def record_call(self, duration_seconds: float, confidence: str):
        """Record a completed agent call."""
        self.total_calls += 1
        self.call_times.append(duration_seconds)

        confidence_key = confidence.lower()
        if confidence_key in self.confidence_counts:
            self.confidence_counts[confidence_key] += 1

        # Log to logfire
        logfire.info(
            "agent_call_recorded",
            duration_seconds=round(duration_seconds, 3),
            confidence=confidence,
            total_calls=self.total_calls,
        )

    def record_error(self, error: str):
        """Record a failed agent call."""
        self.total_errors += 1
        logfire.error("agent_call_failed", error=error)

    def summary(self) -> dict:
        """Get a summary of all metrics."""
        avg_time = (
            sum(self.call_times) / len(self.call_times)
            if self.call_times else 0
        )
        return {
            "total_calls": self.total_calls,
            "total_errors": self.total_errors,
            "avg_response_time_seconds": round(avg_time, 3),
            "fastest_seconds": round(min(self.call_times), 3) if self.call_times else 0,
            "slowest_seconds": round(max(self.call_times), 3) if self.call_times else 0,
            "confidence_distribution": self.confidence_counts,
        }


# Global metrics instance
agent_metrics = AgentMetrics()