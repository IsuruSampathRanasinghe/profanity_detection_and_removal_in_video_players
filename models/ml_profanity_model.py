"""Placeholder for future ML-based profanity detection models."""

from typing import Any


class MLProfanityModel:
    """Future extension point for classifier-based profanity detection."""

    def detect_segments(self, transcription_result: dict[str, Any]) -> list[tuple[float, float]]:
        """Return profanity ranges as (start_seconds, end_seconds).

        This is intentionally a placeholder and currently returns no detections.
        """
        _ = transcription_result
        return []
