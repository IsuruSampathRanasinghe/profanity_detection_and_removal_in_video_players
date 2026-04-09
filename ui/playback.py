"""Playback controls mixin for timeline, play/pause/seek and skip actions."""

import os
import time
from tkinter import messagebox

import pygame


class PlaybackMixin:
    """Playback state machine and user playback actions."""

    def _refresh_timeline_markers(self, detections):
        self.timeline_detections = sorted(detections, key=lambda item: float(item.start)) if detections else []
        self._redraw_timeline_markers()

    def _clear_timeline_markers(self):
        self.timeline_detections = []
        self._redraw_timeline_markers()

    def _redraw_timeline_markers(self, _event=None):
        if not hasattr(self, "timeline_marker_canvas"):
            return

        canvas = self.timeline_marker_canvas
        canvas.delete("all")

        width = max(1, canvas.winfo_width())
        height = max(1, canvas.winfo_height())

        # Visual baseline that aligns markers with the seek bar track.
        canvas.create_line(0, height // 2, width, height // 2, fill=self.palette["border"], width=1)

        if self.total_frames <= 1 or self.fps <= 0 or not getattr(self, "timeline_detections", None):
            return

        total_duration = self.total_frames / self.fps
        if total_duration <= 0:
            return

        for detection in self.timeline_detections:
            ratio = max(0.0, min(1.0, float(detection.start) / total_duration))
            x_pos = int(ratio * (width - 1))

            marker_color = self.palette["accent"]
            source = str(getattr(detection, "source", ""))
            if "adult" in source:
                marker_color = self.palette["warning"]
            elif "ml" in source:
                marker_color = self.palette["danger"]

            canvas.create_line(x_pos, 1, x_pos, height - 1, fill=marker_color, width=2)

    def _on_marker_click(self, event):
        if not self.cap or not self.timeline_detections or self.total_frames <= 1 or self.fps <= 0:
            return

        canvas = self.timeline_marker_canvas
        width = max(1, canvas.winfo_width())
        click_ratio = max(0.0, min(1.0, event.x / width))
        click_time = click_ratio * (self.total_frames / self.fps)

        nearest = min(self.timeline_detections, key=lambda item: abs(float(item.start) - click_time))
        nearest_ratio = max(0.0, min(1.0, float(nearest.start) / (self.total_frames / self.fps)))
        nearest_x = int(nearest_ratio * (width - 1))
        if abs(event.x - nearest_x) > 8:
            return

        target_frame = int(float(nearest.start) * self.fps)

        was_playing = self.is_playing
        self._seek_and_show(target_frame)

        if was_playing:
            self.playback_start_time = time.perf_counter()
            self.playback_start_frame = self.current_frame
            self._restart_audio_at_current_position()

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
