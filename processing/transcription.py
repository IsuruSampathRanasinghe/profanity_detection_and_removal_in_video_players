"""Whisper transcription service with lazy model loading."""

from typing import Any

import whisper


class WhisperTranscriber:
    """Wraps Whisper model lifecycle and transcription calls."""

    def __init__(self, model_name: str = "base"):
        self.model_name = model_name
        self._model = None

    def _get_model(self):
        if self._model is None:
            self._model = whisper.load_model(self.model_name)
        return self._model

    def transcribe(self, audio_path: str, language: str | None = None) -> dict[str, Any]:
        model = self._get_model()
        kwargs = {"audio": audio_path}
        if language:
            kwargs["language"] = language
        return model.transcribe(**kwargs)
