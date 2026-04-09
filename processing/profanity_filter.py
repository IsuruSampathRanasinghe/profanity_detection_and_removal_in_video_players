"""Optimized profanity filtering module."""

from dataclasses import dataclass
from pathlib import Path
import re
import unicodedata
from typing import Any

from models.ml_profanity_model import MLProfanityModel
from utils.file_manager import read_profanity_words


# =========================
# CONSTANTS
# =========================
ADULT_STRONG_WORDS = {
    "fuck", "fucking", "motherfucker", "bitch",
    "asshole", "shit", "bastard", "damn",
    "fuckoff", "fuck off"
}

MASKED_PROFANITY_RE = re.compile(r"\b[a-zA-Z]+(?:[\*\!\@\#\$\%_]+[a-zA-Z]*)+\b")

ZERO_WIDTH_CHARS = {"\u200b", "\u200c", "\u200d", "\ufeff"}

SINHALA_SUFFIXES = (
    "ගේ", "ගෙන්", "ටම", "ට", "කට", "ක්", "කි",
    "යි", "යන්", "යෝ", "යා", "ය", "ව", "ත්", "ද",
)


# =========================
# HELPERS
# =========================
def normalize(text: str) -> str:
    if not text:
        return ""
    text = unicodedata.normalize("NFC", text).lower()
    text = "".join(c for c in text if c not in ZERO_WIDTH_CHARS)
    return re.sub(r"\s+", " ", text).strip()


def contains_sinhala(text: str) -> bool:
    return any("\u0d80" <= ch <= "\u0dff" for ch in text)


def tokenize(text: str) -> list[str]:
    tokens = []
    current = []

    for ch in text:
        if ch.isalnum():
            current.append(ch)
        else:
            if current:
                tokens.append("".join(current))
                current.clear()

    if current:
        tokens.append("".join(current))

    return tokens


def sinhala_forms(word: str) -> set[str]:
    word = normalize(word)
    if not contains_sinhala(word):
        return {word}

    forms = {word}
    current = word

    for _ in range(2):
        for suf in SINHALA_SUFFIXES:
            if current.endswith(suf) and len(current) > len(suf) + 1:
                current = current[:-len(suf)]
                forms.add(current)
                break

    return forms


# =========================
# DATA CLASS
# =========================
@dataclass(frozen=True)
class DetectionResult:
    start: float
    end: float
    source: str
    word: str = ""
    confidence: float = 0.0


# =========================
# DETECTION CORE
# =========================
def detect_word(segment, word_list: set[str], source: str, confidence: float):
    detections = []

    words = segment.get("words", [])
    if not words:
        return detections

    for w in words:
        raw = str(w.get("word", ""))
        norm = normalize(raw)

        if not norm:
            continue

        for bad in word_list:
            if norm == bad or bad in norm:
                start = float(w.get("start", segment["start"]))
                end = float(w.get("end", start + 0.15))

                detections.append(
                    DetectionResult(start, end, source, bad, confidence)
                )
                break

    return detections


# =========================
# FILTER MODES
# =========================
def kids_filter(segments, word_list, use_ml_model, ml_model):
    detections = []

    if use_ml_model and ml_model is None:
        ml_model = MLProfanityModel()

    for seg in segments:
        # Rule-based first
        matches = detect_word(seg, word_list, "kids-rule", 0.98)
        if matches:
            detections.extend(matches)
            continue

        text = seg.get("text", "")

        # Masked profanity
        if MASKED_PROFANITY_RE.search(text):
            detections.append(
                DetectionResult(seg["start"], seg["end"], "mask", "[masked]", 0.9)
            )
            continue

        # ML fallback
        if use_ml_model and ml_model and ml_model.predict_toxicity(text):
            detections.append(
                DetectionResult(seg["start"], seg["end"], "ml", "[ML]", 0.7)
            )

    return detections, len(detections)


def adult_filter(segments):
    detections = []

    for seg in segments:
        matches = detect_word(seg, ADULT_STRONG_WORDS, "adult", 0.95)
        detections.extend(matches)

    return detections, len(detections)


def custom_filter(segments, word_list):
    detections = []

    for seg in segments:
        matches = detect_word(seg, word_list, "custom", 0.97)
        detections.extend(matches)

    return detections, len(detections)


# =========================
# MAIN FILTER
# =========================
def filter_profanity(
    segments,
    mode,
    word_list,
    use_ml_model=False,
    ml_model=None,
):
    if not segments:
        return [], 0

    mode = (mode or "custom").lower()

    if mode in {"kids", "ai"}:
        return kids_filter(segments, word_list, use_ml_model, ml_model)

    if mode == "adult":
        return adult_filter(segments)

    return custom_filter(segments, word_list)


# =========================
# MAIN CLASS
# =========================
class ProfanityFilter:

    def __init__(
        self,
        profanity_file: Path,
        profanity_files_by_language: dict[str, Path] | None = None,
        ml_model: MLProfanityModel | None = None,
    ):
        self.profanity_file = profanity_file
        self.files_by_lang = profanity_files_by_language or {}
        self.ml_model = ml_model  # ✅ lazy load

    def _load_words(self, language):
        if not language:
            words = set(read_profanity_words(self.profanity_file))
            for f in self.files_by_lang.values():
                words.update(read_profanity_words(f))
            return {normalize(w) for w in words if w}

        file = self.files_by_lang.get(language)
        if file:
            return {normalize(w) for w in read_profanity_words(file)}

        return {normalize(w) for w in read_profanity_words(self.profanity_file)}

    def detect(self, transcription_result, mode="ai", use_ml_model=True, language=None):
        segments = transcription_result.get("segments", [])
        if not segments:
            return [], 0

        words = self._load_words(language)

        detections, count = filter_profanity(
            segments,
            mode,
            words,
            use_ml_model,
            self.ml_model,
        )

        return detections, count