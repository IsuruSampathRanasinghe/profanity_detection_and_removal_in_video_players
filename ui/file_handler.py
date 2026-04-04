"""File and source switching mixin for opening/loading videos."""

import os
import cv2
from tkinter import filedialog, messagebox

from config.settings import settings


class FileHandlerMixin:
    """Handles selecting source files and swapping preview source."""

    def open_video(self):
        file_path = filedialog.askopenfilename(
            title="Select a video file",
            filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv *.flv"), ("All files", "*.*")],
            initialdir=str(settings.videos_dir),
        )
        if not file_path:
            return

        self.original_video_path = file_path
        self.clean_video_path = None
        self._set_filter_status("Filter: ready", self.palette["success"])
        self._load_video_source(file_path, source_name="Original")

    def _load_video_source(self, file_path: str, source_name: str = "Video") -> bool:
        self.stop_video(reset_frame=False)

        if self.cap:
            self.cap.release()
            self.cap = None

        self.cap = cv2.VideoCapture(file_path)
        if not self.cap.isOpened():
            messagebox.showerror("Error", "Cannot open video file")
            self.cap = None
            return False

        self.current_video_path = file_path
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        detected_fps = float(self.cap.get(cv2.CAP_PROP_FPS) or 0)
        self.fps = detected_fps if detected_fps > 1 else 25.0
        self.current_frame = 0

        self._set_video_status(f"{source_name}: {os.path.basename(file_path)}")
        self.progress_scale.config(to=max(1, self.total_frames - 1))

        self._extract_audio(file_path)
        self._seek_and_show(0)
        return True

    def play_original_video(self):
        if not self.original_video_path:
            messagebox.showwarning("Warning", "Load a video first")
            return

        if self.current_video_path != self.original_video_path:
            loaded = self._load_video_source(self.original_video_path, source_name="Original")
            if not loaded:
                return

        self.play_video()

    def play_clean_video(self):
        if not self.clean_video_path or not os.path.exists(self.clean_video_path):
            messagebox.showwarning("Warning", "Filter profanity first to create the clean video")
            return

        if self.current_video_path != self.clean_video_path:
            loaded = self._load_video_source(self.clean_video_path, source_name="Clean")
            if not loaded:
                return

        self.play_video()

    def _set_video_status(self, text: str):
        self.current_video_label_text.set(text)
