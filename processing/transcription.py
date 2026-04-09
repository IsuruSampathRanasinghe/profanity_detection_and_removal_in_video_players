"""Whisper transcription service with lazy model loading (CPU-only)."""

import os
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import whisper


class WhisperTranscriber:
    """Handles Whisper model loading, caching, and transcription."""

    def __init__(self, model_name: str = "small"):
        self.model_name = model_name
        self._models: dict[str, Any] = {}

    # =========================
    # ERROR HANDLING
    # =========================
    @staticmethod
    def _is_checksum_error(error: Exception) -> bool:
        msg = str(error).lower()
        return "sha256" in msg and "match" in msg

    @staticmethod
    def _model_cache_dir() -> Path:
        return Path(os.path.expanduser("~")) / ".cache" / "whisper"

    def _delete_cached_model_file(self, model_name: str):
        model_url = getattr(whisper, "_MODELS", {}).get(model_name)
        if not model_url:
            return

        filename = Path(urlparse(model_url).path).name
        model_file = self._model_cache_dir() / filename

        try:
            if model_file.exists():
                model_file.unlink()
        except Exception:
            pass

    def _load_with_recovery(self, model_name: str):
        try:
            return whisper.load_model(model_name)  # CPU only
        except Exception as e:
            if not self._is_checksum_error(e):
                raise

            # Retry if corrupted download
            self._delete_cached_model_file(model_name)
            return whisper.load_model(model_name)

    # =========================
    # MODEL MANAGEMENT
    # =========================
    def _preferred_model_name(self, language: str | None) -> str:
        # Improve Sinhala/Tamil accuracy
        if language in {"si", "ta"} and self.model_name in {"tiny", "base"}:
            return "small"
        return self.model_name

    def _get_model(self, language: str | None):
        name = self._preferred_model_name(language)

        if name in self._models:
            return self._models[name]

        model = self._load_with_recovery(name)
        self._models[name] = model
        return model

    def _get_or_load_model(self, model_name: str):
        if model_name in self._models:
            return self._models[model_name]

        model = self._load_with_recovery(model_name)
        self._models[model_name] = model
        return model

    # =========================
    # QUALITY CHECK
    # =========================
    def _script_ratio(self, text: str, language: str) -> float:
        letters = [c for c in text if c.isalpha()]
        if not letters:
            return 0.0

        if language == "si":
            valid = [c for c in letters if "\u0d80" <= c <= "\u0dff"]
        elif language == "ta":
            valid = [c for c in letters if "\u0b80" <= c <= "\u0bff"]
        else:
            return 1.0

        return len(valid) / len(letters)

    def _looks_bad(self, result: dict, language: str) -> bool:
        text = " ".join(seg.get("text", "") for seg in result.get("segments", []))

        if len(text) < 20:
            return False

        return self._script_ratio(text, language) < 0.3

    # =========================
    # TRANSCRIBE
    # =========================
    def transcribe(self, audio_path: str, language: str | None = None) -> dict:
        model = self._get_model(language)

        kwargs = {
            "audio": audio_path,
            "task": "transcribe",
            "fp16": False,  # ✅ always CPU-safe
            "word_timestamps": True,
            "temperature": 0.0,
        }

        if language:
            kwargs["language"] = language

            # Better for Sinhala/Tamil
            if language in {"si", "ta"}:
                kwargs.update({
                    "beam_size": 5,
                    "best_of": 5,
                })

        result = model.transcribe(**kwargs)

        # Retry with bigger model if poor quality
        if language in {"si", "ta"} and self._looks_bad(result, language):
            try:
                fallback = self._get_or_load_model("medium")
                better = fallback.transcribe(**kwargs)

                if not self._looks_bad(better, language):
                    return better
            except Exception:
                pass

        return result