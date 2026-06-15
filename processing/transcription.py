"""
Improved Whisper Transcription Service
- GPU/CPU auto detection
- Lazy model loading + caching
- Sinhala/Tamil accuracy improvements
- Bad output detection + retry with larger model
- Optional subtitle (.srt) generation
"""

import os
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import whisper
import torch
import logging

logger = logging.getLogger(__name__)


class WhisperTranscriber:
    """Handles Whisper model loading, caching, and transcription."""

    def __init__(self, model_name: str = "small"):
        self.model_name = model_name
        self._models: dict[str, Any] = {}

        # 🔥 Detect GPU or CPU
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info("Using device: %s", self.device)

    # =========================
    # ERROR HANDLING
    # =========================
    @staticmethod
    def _is_checksum_error(error: Exception) -> bool:
        """Detect corrupted model download"""
        msg = str(error).lower()
        return "sha256" in msg and "match" in msg

    @staticmethod
    def _model_cache_dir() -> Path:
        """Get Whisper cache directory"""
        return Path(os.path.expanduser("~")) / ".cache" / "whisper"

    def _delete_cached_model_file(self, model_name: str):
        """Delete corrupted model file"""
        model_url = getattr(whisper, "_MODELS", {}).get(model_name)
        if not model_url:
            return

        filename = Path(urlparse(model_url).path).name
        model_file = self._model_cache_dir() / filename

        try:
                if model_file.exists():
                    logger.info("Removing corrupted model: %s", filename)
                    model_file.unlink()
        except Exception as e:
            logger.debug("Failed removing cached model file %s: %s", model_file, e)

    def _load_with_recovery(self, model_name: str):
        """Load model with auto recovery if corrupted"""
        try:
            model = whisper.load_model(model_name)

            # Move model to correct device
            model = model.to(self.device)

            logger.info("Loaded model: %s on %s", model_name, self.device)
            return model

        except Exception as e:
            if self._is_checksum_error(e):
                logger.warning("Model corrupted. Re-downloading...")
                self._delete_cached_model_file(model_name)

                model = whisper.load_model(model_name)
                model = model.to(self.device)
                return model

            raise

    # =========================
    # MODEL MANAGEMENT
    # =========================
    def _preferred_model_name(self, language: str | None) -> str:
        """Use larger model for Sinhala/Tamil"""
        if language in {"si", "ta"}:
            return "medium"
        return self.model_name

    def _get_model(self, language: str | None):
        """Get cached model or load new one"""
        name = self._preferred_model_name(language)

        if name in self._models:
            return self._models[name]

        model = self._load_with_recovery(name)
        self._models[name] = model
        return model

    def _get_or_load_model(self, model_name: str):
        """Force load specific model (used for fallback)"""
        if model_name in self._models:
            return self._models[model_name]

        model = self._load_with_recovery(model_name)
        self._models[model_name] = model
        return model

    # =========================
    # QUALITY CHECK
    # =========================
    def _script_ratio(self, text: str, language: str) -> float:
        """Check if output text matches Sinhala/Tamil script"""
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

    def _has_repeated_chars(self, text: str) -> bool:
        """Detect repeated/garbage output"""
        if len(text) < 10:
            return False

        return len(set(text)) < 5

    def _looks_bad(self, result: dict, language: str) -> bool:
        """Check if transcription quality is poor"""
        text = " ".join(seg.get("text", "") for seg in result.get("segments", []))

        if len(text) < 20:
            return False

        return (
            self._script_ratio(text, language) < 0.3 or
            self._has_repeated_chars(text)
        )

    # =========================
    # AUDIO PREPROCESS (OPTIONAL)
    # =========================
    def preprocess_audio(self, input_path: str, output_path: str):
        """
        Convert audio to:
        - mono channel
        - 16kHz sample rate

        Requires FFmpeg installed
        """
        os.system(f'ffmpeg -i "{input_path}" -ac 1 -ar 16000 "{output_path}"')

    # =========================
    # TRANSCRIPTION
    # =========================
    def transcribe(self, audio_path: str, language: str | None = None) -> dict:
        """Main transcription function"""

        model = self._get_model(language)

        kwargs = {
            "audio": audio_path,
            "task": "transcribe",
            "fp16": self.device == "cuda",
            "word_timestamps": True,

            # 🔥 Improved decoding settings
            "temperature": 0.0,
            "condition_on_previous_text": False,
            "compression_ratio_threshold": 2.4,
            "logprob_threshold": -1.0,
            "no_speech_threshold": 0.6,
        }

        # Sinhala / Tamil optimization
        if language in {"si", "ta"}:
            kwargs.update({
                "language": language,
                "beam_size": 5,
                "best_of": 5,
            })

        logger.info("Transcribing audio: %s", audio_path)
        result = model.transcribe(**kwargs)

        logger.info("Detected language: %s", result.get('language'))

        # Retry with large model if poor quality
        if language in {"si", "ta"} and self._looks_bad(result, language):
            try:
                logger.warning("Retrying with LARGE model...")

                fallback = self._get_or_load_model("large")
                better = fallback.transcribe(**kwargs)

                if not self._looks_bad(better, language):
                    return better

            except Exception as e:
                logger.exception("Retry with large model failed: %s", e)

        return result

    # =========================
    # SUBTITLE GENERATION
    # =========================
    def save_srt(self, result: dict, output_file: str):
        """Save transcription as .srt subtitle file"""

        def format_time(seconds: float):
            h = int(seconds // 3600)
            m = int((seconds % 3600) // 60)
            s = int(seconds % 60)
            ms = int((seconds - int(seconds)) * 1000)
            return f"{h:02}:{m:02}:{s:02},{ms:03}"

        with open(output_file, "w", encoding="utf-8") as f:
            for i, seg in enumerate(result.get("segments", [])):
                start = seg["start"]
                end = seg["end"]
                text = seg["text"].strip()

                f.write(f"{i+1}\n")
                f.write(f"{format_time(start)} --> {format_time(end)}\n")
                f.write(f"{text}\n\n")