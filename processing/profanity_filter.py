"""Profanity filtering strategies for kids, adult, and custom modes."""

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

from models.ml_profanity_model import MLProfanityModel
from utils.file_manager import read_profanity_words


# A focused strong list for adult mode. Mild words are intentionally excluded.
ADULT_STRONG_WORDS = {
    "fuck",
    "fucking",
    "motherfucker",
    "bitch",
    "asshole",
    "shit",
    "bastard",
    "damn",
}

# Matches masked profanity such as f***, sh!t, b@stard.
MASKED_PROFANITY_RE = re.compile(r"\b[a-zA-Z]+(?:[\*\!\@\#\$\%_]+[a-zA-Z]*)+\b")


@dataclass(frozen=True)
class DetectionResult:
    """Detected profanity occurrence in seconds."""

    start: float
    end: float
    source: str


def filter_profanity(
    segments: list[dict[str, Any]],
    mode: str,
    word_list: set[str],
    use_ml_model: bool = False,
    ml_model: MLProfanityModel | None = None,
) -> tuple[list[DetectionResult], int]:
    """Main filter entry point that routes to a mode-specific strategy."""
    normalized_mode = (mode or "custom").strip().lower()

    if normalized_mode == "kids":
        return kids_filter(
            segments=segments,
            word_list=word_list,
            use_ml_model=use_ml_model,
            ml_model=ml_model,
        )
    if normalized_mode == "adult":
        return adult_filter(segments=segments)
    return custom_filter(segments=segments, word_list=word_list)


def kids_filter(
    segments: list[dict[str, Any]],
    word_list: set[str],
    use_ml_model: bool = False,
    ml_model: MLProfanityModel | None = None,
) -> tuple[list[DetectionResult], int]:
    """Strict mode: list-based + masked detection + optional ML signal."""
    detections: list[DetectionResult] = []
    active_ml_model = ml_model or MLProfanityModel()

    for segment in segments:
        text = str(segment.get("text", "")).strip()
        lowered = text.lower()

        by_list = bool(word_list) and any(word in lowered for word in word_list)
        by_mask = bool(MASKED_PROFANITY_RE.search(text))
        by_model = use_ml_model and active_ml_model.predict_toxicity(text)

        if by_list or by_mask or by_model:
            source = "kids-rule"
            if by_model:
                source = "kids-ml"
            elif by_mask:
                source = "kids-mask"

            detections.append(
                DetectionResult(
                    start=float(segment.get("start", 0)),
                    end=float(segment.get("end", 0)),
                    source=source,
                )
            )

    return detections, len(detections)


def adult_filter(segments: list[dict[str, Any]]) -> tuple[list[DetectionResult], int]:
    """Moderate mode: only strong profanity is filtered."""
    detections: list[DetectionResult] = []

    for segment in segments:
        lowered = str(segment.get("text", "")).lower()
        if any(word in lowered for word in ADULT_STRONG_WORDS):
            detections.append(
                DetectionResult(
                    start=float(segment.get("start", 0)),
                    end=float(segment.get("end", 0)),
                    source="adult-strong",
                )
            )

    return detections, len(detections)


def custom_filter(segments: list[dict[str, Any]], word_list: set[str]) -> tuple[list[DetectionResult], int]:
    """Custom mode: user-provided profanity list only."""
    if not word_list:
        return [], 0

    detections: list[DetectionResult] = []
    for segment in segments:
        lowered = str(segment.get("text", "")).lower()
        if any(word in lowered for word in word_list):
            detections.append(
                DetectionResult(
                    start=float(segment.get("start", 0)),
                    end=float(segment.get("end", 0)),
                    source="custom",
                )
            )

    return detections, len(detections)


class ProfanityFilter:
    """Filter facade used by the pipeline."""

    def __init__(
        self,
        profanity_file: Path,
        profanity_files_by_language: dict[str, Path] | None = None,
        ml_model: MLProfanityModel | None = None,
    ):
        self.profanity_file = profanity_file
        self.profanity_files_by_language = profanity_files_by_language or {}
        self.ml_model = ml_model or MLProfanityModel()

    def _load_words_for_language(self, language: str | None) -> set[str]:
        language_key = (language or "").strip().lower()

        # Auto-detect mode: merge all known lists for broader coverage.
        if not language_key:
            merged = set(read_profanity_words(self.profanity_file))
            for file_path in self.profanity_files_by_language.values():
                merged.update(read_profanity_words(file_path))
            return merged

        target_file = self.profanity_files_by_language.get(language_key)
        if target_file:
            return read_profanity_words(target_file)

        # Fallback if unknown language code is provided.
        return read_profanity_words(self.profanity_file)

    def detect(
        self,
        transcription_result: dict[str, Any],
        mode: str = "custom",
        use_ml_model: bool = False,
        language: str | None = None,
    ) -> tuple[list[DetectionResult], int]:
        words = self._load_words_for_language(language)
        segments = transcription_result.get("segments", [])

        return filter_profanity(
            segments=segments,
            mode=mode,
            word_list=words,
            use_ml_model=use_ml_model,
            ml_model=self.ml_model,
        )
