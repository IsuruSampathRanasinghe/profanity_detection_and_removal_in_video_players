"""Audio manager mixin for extraction and pygame audio synchronization."""

import os
import time
from pathlib import Path

import pygame

from config.settings import settings
from processing.audio_extractor import extract_audio
from utils.file_manager import safe_delete


class AudioManagerMixin:
    """Handles preview audio generation and playback restarts."""

    def _extract_audio(self, video_path: str):
        if not self.mixer_ready:
            self.audio_path = None
            self._set_audio_status("Audio: mixer unavailable", self.palette["danger"])
            return

        previous_audio_path = Path(self.audio_path) if self.audio_path else None
        self.audio_path = None

        try:
            try:
                pygame.mixer.music.stop()
                if hasattr(pygame.mixer.music, "unload"):
                    pygame.mixer.music.unload()
            except Exception:
                pass

            settings.audio_dir.mkdir(parents=True, exist_ok=True)
            base_name = Path(video_path).stem
            preview_audio_path = settings.audio_dir / f"preview_{base_name}_{int(time.time() * 1000)}.wav"

            extract_audio(video_path, str(preview_audio_path), sample_rate=44100)
            self.audio_path = str(preview_audio_path)
            self.generated_audio_paths.add(preview_audio_path)
            self._set_audio_status("Audio: ready", self.palette["success"])
        except Exception as exc:
            print(f"Audio extraction failed: {exc}")
            self.audio_path = None
            self._set_audio_status("Audio: extraction failed", self.palette["danger"])
        finally:
            if previous_audio_path and previous_audio_path in self.generated_audio_paths:
                if str(previous_audio_path) != self.audio_path:
                    safe_delete(previous_audio_path)
                    self.generated_audio_paths.discard(previous_audio_path)

    def _restart_audio_at_current_position(self):
        if not self.mixer_ready:
            self._set_audio_status("Audio: mixer unavailable", self.palette["danger"])
            return
        if not self.audio_path or not os.path.exists(self.audio_path):
            self._set_audio_status("Audio: not available", self.palette["warning"])
            return

        try:
            pygame.mixer.music.load(self.audio_path)
            start_sec = self.current_frame / self.fps if self.fps > 0 else 0
            if start_sec > 0:
                try:
                    pygame.mixer.music.play(loops=0, start=start_sec)
                except Exception:
                    pygame.mixer.music.play(loops=0)
            else:
                pygame.mixer.music.play(loops=0)
            pygame.mixer.music.set_volume(self.volume)
            self._set_audio_status("Audio: playing", self.palette["success"])
        except Exception as exc:
            print(f"Audio seek failed: {exc}")
            self._set_audio_status("Audio: playback failed", self.palette["danger"])

    def _set_audio_status(self, text: str, color: str | None = None):
        self.audio_status_text.set(text)
        if color:
            self.audio_status_label.configure(foreground=color)
