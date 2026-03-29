import os
import time
import tkinter as tk
from tkinter import filedialog, messagebox

import cv2
import pygame
from PIL import Image, ImageTk

try:
    from moviepy.editor import VideoFileClip
except ImportError:
    from moviepy import VideoFileClip


class VideoPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Player")
        self.root.geometry("960x640")
        self.root.resizable(True, True)

        self.mixer_ready = True
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2)
        except Exception as exc:
            print(f"Audio mixer init failed: {exc}")
            self.mixer_ready = False

        self.cap = None
        self.video_path = None
        self.audio_path = None

        self.is_playing = False
        self.current_frame = 0
        self.total_frames = 0
        self.fps = 25.0

        self.playback_start_time = 0.0
        self.playback_start_frame = 0

        self._build_ui()

    def _build_ui(self):
        controls = tk.Frame(self.root)
        controls.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        tk.Button(
            controls,
            text="Open Video",
            command=self.open_video,
            bg="#2e7d32",
            fg="white",
            padx=12,
            pady=6,
        ).pack(side=tk.LEFT, padx=4)

        tk.Button(
            controls,
            text="Play",
            command=self.play_video,
            bg="#1565c0",
            fg="white",
            padx=12,
            pady=6,
        ).pack(side=tk.LEFT, padx=4)

        tk.Button(
            controls,
            text="Pause",
            command=self.pause_video,
            bg="#ef6c00",
            fg="white",
            padx=12,
            pady=6,
        ).pack(side=tk.LEFT, padx=4)

        tk.Button(
            controls,
            text="Stop",
            command=self.stop_video,
            bg="#c62828",
            fg="white",
            padx=12,
            pady=6,
        ).pack(side=tk.LEFT, padx=4)

        self.video_label = tk.Label(controls, text="No video loaded", fg="#666")
        self.video_label.pack(side=tk.LEFT, padx=16)

        self.audio_status_label = tk.Label(controls, text="Audio: idle", fg="#666")
        self.audio_status_label.pack(side=tk.RIGHT, padx=8)

        self.canvas = tk.Canvas(self.root, bg="black")
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.canvas.bind("<Configure>", self._on_resize)

        progress_wrap = tk.Frame(self.root)
        progress_wrap.pack(fill=tk.X, padx=10, pady=6)

        self.progress_scale = tk.Scale(
            progress_wrap,
            from_=0,
            to=100,
            orient=tk.HORIZONTAL,
            command=self._on_seek,
            showvalue=False,
        )
        self.progress_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.time_label = tk.Label(progress_wrap, text="00:00 / 00:00", width=16)
        self.time_label.pack(side=tk.RIGHT, padx=8)

    def open_video(self):
        file_path = filedialog.askopenfilename(
            title="Select a video file",
            filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv *.flv"), ("All files", "*.*")],
            initialdir="videos",
        )
        if not file_path:
            return

        self.stop_video(reset_frame=False)

        if self.cap:
            self.cap.release()
            self.cap = None

        self.cap = cv2.VideoCapture(file_path)
        if not self.cap.isOpened():
            messagebox.showerror("Error", "Cannot open video file")
            return

        self.video_path = file_path
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        detected_fps = float(self.cap.get(cv2.CAP_PROP_FPS) or 0)
        self.fps = detected_fps if detected_fps > 1 else 25.0
        self.current_frame = 0

        self.video_label.config(text=f"Loaded: {os.path.basename(file_path)}")
        self.progress_scale.config(to=max(1, self.total_frames - 1))

        self._extract_audio(file_path)
        self._seek_and_show(0)

    def _extract_audio(self, video_path):
        self.audio_path = None
        if not self.mixer_ready:
            self._set_audio_status("Audio: mixer unavailable", "#c62828")
            return

        clip = None
        try:
            if os.path.exists("temp_audio.wav"):
                os.remove("temp_audio.wav")

            clip = VideoFileClip(video_path)
            if clip.audio is None:
                self._set_audio_status("Audio: no audio track", "#ef6c00")
                return

            clip.audio.write_audiofile(
                "temp_audio.wav",
                codec="pcm_s16le",
                fps=44100,
                logger=None,
            )
            self.audio_path = "temp_audio.wav"
            self._set_audio_status("Audio: ready", "#2e7d32")
        except Exception as exc:
            print(f"Audio extraction failed: {exc}")
            self.audio_path = None
            self._set_audio_status("Audio: extraction failed", "#c62828")
        finally:
            if clip is not None:
                clip.close()

    def _seek_and_show(self, frame_index):
        if not self.cap:
            return

        frame_index = max(0, min(frame_index, max(0, self.total_frames - 1)))
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ok, frame = self.cap.read()
        if not ok:
            return

        self.current_frame = frame_index
        self._render_frame(frame)
        self.progress_scale.set(self.current_frame)
        self._update_time_label()

    def _render_frame(self, frame):
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        if canvas_w <= 1 or canvas_h <= 1:
            return

        h, w = frame.shape[:2]
        aspect = w / h

        if canvas_w / canvas_h > aspect:
            new_h = canvas_h
            new_w = int(new_h * aspect)
        else:
            new_w = canvas_w
            new_h = int(new_w / aspect)

        frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        image = Image.fromarray(frame)
        photo = ImageTk.PhotoImage(image=image)

        self.canvas.delete("all")
        self.canvas.create_image(canvas_w // 2, canvas_h // 2, image=photo)
        self.canvas.image = photo

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
                        # WAV seeking is not always supported; fallback keeps audio working.
                        pygame.mixer.music.play(loops=0)
                else:
                    pygame.mixer.music.play(loops=0)
                pygame.mixer.music.set_volume(1.0)
                self._set_audio_status("Audio: playing", "#2e7d32")
            except Exception as exc:
                print(f"Audio playback failed: {exc}")
                self._set_audio_status("Audio: playback failed", "#c62828")
        elif not self.mixer_ready:
            self._set_audio_status("Audio: mixer unavailable", "#c62828")
        else:
            self._set_audio_status("Audio: not available", "#ef6c00")

        self._playback_tick()

    def _playback_tick(self):
        if not self.is_playing or not self.cap:
            return

        elapsed = time.perf_counter() - self.playback_start_time
        target_frame = self.playback_start_frame + int(elapsed * self.fps)

        if target_frame >= self.total_frames:
            self.stop_video()
            return

        if target_frame != self.current_frame:
            self._seek_and_show(target_frame)

        self.root.after(10, self._playback_tick)

    def pause_video(self):
        if not self.is_playing:
            return

        self.is_playing = False
        if self.mixer_ready and pygame.mixer.music.get_busy():
            pygame.mixer.music.pause()
            self._set_audio_status("Audio: paused", "#666")

    def stop_video(self, reset_frame=True):
        self.is_playing = False
        if self.mixer_ready:
            pygame.mixer.music.stop()
            self._set_audio_status("Audio: stopped", "#666")

        if self.cap and reset_frame:
            self._seek_and_show(0)

    def _on_seek(self, value):
        if self.is_playing:
            return
        if not self.cap:
            return

        self._seek_and_show(int(float(value)))

    def _on_resize(self, _event):
        if self.cap:
            self._seek_and_show(self.current_frame)

    def _update_time_label(self):
        cur = self.current_frame / self.fps if self.fps > 0 else 0
        total = self.total_frames / self.fps if self.fps > 0 else 0
        self.time_label.config(text=f"{self._fmt_time(cur)} / {self._fmt_time(total)}")

    def _set_audio_status(self, text, color="#666"):
        self.audio_status_label.config(text=text, fg=color)

    @staticmethod
    def _fmt_time(seconds):
        m = int(seconds // 60)
        s = int(seconds % 60)
        return f"{m:02d}:{s:02d}"

    def cleanup(self):
        self.stop_video(reset_frame=False)
        if self.cap:
            self.cap.release()
            self.cap = None


if __name__ == "__main__":
    root = tk.Tk()
    player = VideoPlayer(root)

    def on_close():
        player.cleanup()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()
