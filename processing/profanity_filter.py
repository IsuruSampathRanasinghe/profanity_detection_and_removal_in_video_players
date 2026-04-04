"""Profanity detection strategies (rule-based + ML placeholder)."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from models.ml_profanity_model import MLProfanityModel
from utils.file_manager import read_profanity_words


@dataclass(frozen=True)
class DetectionResult:
    """Detected profanity occurrence in seconds."""

    start: float
    end: float
    source: str


class ProfanityFilter:
    """Provides pluggable profanity detection strategies."""

    def __init__(self, profanity_file: Path, ml_model: MLProfanityModel | None = None):
        self.profanity_file = profanity_file
        self.ml_model = ml_model or MLProfanityModel()

    def detect(
        self,
        transcription_result: dict[str, Any],
        mode: str = "rule-based",
    ) -> list[DetectionResult]:
        if mode == "ai":
            return self._detect_ai(transcription_result)
        return self._detect_rule_based(transcription_result)

    def _detect_rule_based(self, transcription_result: dict[str, Any]) -> list[DetectionResult]:
        words = read_profanity_words(self.profanity_file)
        if not words:
            return []

        detections: list[DetectionResult] = []
        for segment in transcription_result.get("segments", []):
            text = str(segment.get("text", "")).lower()
            if any(word in text for word in words):
                detections.append(
                    DetectionResult(
                        start=float(segment.get("start", 0)),
                        end=float(segment.get("end", 0)),
                        source="rule-based",
                    )
                )
        return detections

    def _detect_ai(self, transcription_result: dict[str, Any]) -> list[DetectionResult]:
        ranges = self.ml_model.detect_segments(transcription_result)
        return [
            DetectionResult(start=float(start), end=float(end), source="ai")
            for start, end in ranges
        ]
