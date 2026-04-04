"""Playback controls mixin for timeline, play/pause/seek and skip actions."""

import os
import time
from tkinter import messagebox

import pygame


class PlaybackMixin:
    """Playback state machine and user playback actions."""

    def play_video(self):
        if not self.cap or not self.cap.isOpened():
            messagebox.showwarning("Warning", "Open a video first")
            return
        if self.is_playing:
            return

        self.is_playing = True
        self.playback_start_time = time.perf_counter()
        self.playback_start_frame = self.current_frame

        if self.mixer_ready and self.audio_path and os.path.exists(self.audio_path):
            try:
                pygame.mixer.music.load(self.audio_path)
                start_sec = self.current_frame / self.fps
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
                print(f"Audio playback failed: {exc}")
                self._set_audio_status("Audio: playback failed", self.palette["danger"])
        elif not self.mixer_ready:
            self._set_audio_status("Audio: mixer unavailable", self.palette["danger"])
        else:
            self._set_audio_status("Audio: not available", self.palette["warning"])

        self._playback_tick()

    def _playback_tick(self):
        if not self.is_playing or not self.cap:
            return

        if self._is_scrubbing:
            self.root.after(10, self._playback_tick)
            return

        elapsed = time.perf_counter() - self.playback_start_time
        target_frame = self.playback_start_frame + int(elapsed * self.fps)

        if target_frame >= self.total_frames:
            self.stop_video()
            return

        if target_frame != self.current_frame:
            self._seek_and_show(target_frame)

        self.root.after(10, self._playback_tick)

    def _on_timeline_press(self, _event):
        if not self.cap:
            return

        self._is_scrubbing = True
        self._resume_after_scrub = self.is_playing

        if self._resume_after_scrub:
            self.is_playing = False
            if self.mixer_ready and pygame.mixer.music.get_busy():
                try:
                    pygame.mixer.music.pause()
                except Exception:
                    pass

    def _on_timeline_release(self, _event):
        if not self.cap:
            return

        was_playing = self._resume_after_scrub or self.is_playing
        self._seek_and_show(int(self.progress_scale.get()))

        self._is_scrubbing = False
        self._resume_after_scrub = False

        if was_playing:
            self.is_playing = True
            self.playback_start_time = time.perf_counter()
            self.playback_start_frame = self.current_frame
            self._restart_audio_at_current_position()
            self._playback_tick()

    def _on_seek(self, value):
        if not self.cap or self._updating_progress:
            return
        if not self.is_playing:
            self._seek_and_show(int(float(value)))

    def pause_video(self):
        if not self.is_playing:
            return

        self.is_playing = False
        if self.mixer_ready and pygame.mixer.music.get_busy():
            pygame.mixer.music.pause()
            self._set_audio_status("Audio: paused", self.palette["muted"])

    def stop_video(self, reset_frame: bool = True):
        self.is_playing = False
        if self.mixer_ready:
            pygame.mixer.music.stop()
            self._set_audio_status("Audio: stopped", self.palette["muted"])

        if self.cap and reset_frame:
            self._seek_and_show(0)
        elif not self.cap:
            self._render_empty_preview()

    def skip_backward(self):
        self._skip_seconds(-self.skip_seconds)

    def skip_forward(self):
        self._skip_seconds(self.skip_seconds)

    def _skip_seconds(self, delta_seconds: int):
        if not self.cap:
            return

        was_playing = self.is_playing
        delta_frames = int(delta_seconds * self.fps)
        target_frame = self.current_frame + delta_frames
        self._seek_and_show(target_frame)

        if was_playing:
            self.playback_start_time = time.perf_counter()
            self.playback_start_frame = self.current_frame
            self._restart_audio_at_current_position()

    def _on_skip_backward_key(self, _event):
        self.skip_backward()

    def _on_skip_forward_key(self, _event):
        self.skip_forward()

    def _update_time_label(self):
        cur = self.current_frame / self.fps if self.fps > 0 else 0
        total = self.total_frames / self.fps if self.fps > 0 else 0
        self.time_label.configure(text=f"{self._fmt_time(cur)} / {self._fmt_time(total)}")

    @staticmethod
    def _fmt_time(seconds: float) -> str:
        minutes = int(seconds // 60)
        remaining_seconds = int(seconds % 60)
        return f"{minutes:02d}:{remaining_seconds:02d}"
