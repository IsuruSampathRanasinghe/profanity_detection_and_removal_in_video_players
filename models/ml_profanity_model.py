"""Placeholder for future ML-based profanity detection models."""

from typing import Any


def predict_toxicity(text: str) -> bool:
    """Return whether text is toxic/profane.

    Placeholder for future model inference.
    """
    _ = text
    return False


class MLProfanityModel:
    """Future extension point for classifier-based profanity detection."""

    def predict_toxicity(self, text: str) -> bool:
        """Class wrapper around the placeholder toxicity prediction function."""
        return predict_toxicity(text)

    def detect_segments(self, transcription_result: dict[str, Any]) -> list[tuple[float, float]]:
        """Return profanity ranges as (start_seconds, end_seconds).

        This is intentionally a placeholder and currently returns no detections.
        """
        _ = transcription_result
        return []
