"""Video canvas rendering mixin for centered, aspect-ratio-preserving preview."""

import cv2
from PIL import Image, ImageTk


class VideoCanvasMixin:
    """Owns canvas placeholder and frame rendering behavior."""

    def _render_empty_preview(self):
        if not hasattr(self, "canvas"):
            return
        self.canvas.delete("all")
        canvas_w = max(1, self.canvas.winfo_width())
        canvas_h = max(1, self.canvas.winfo_height())
        self.canvas.create_text(
            canvas_w // 2,
            canvas_h // 2,
            text="No video loaded",
            fill="white",
            font=("Segoe UI", 16),
        )

    def _render_frame(self, frame):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        if canvas_w <= 1 or canvas_h <= 1:
            return

        h, w = frame.shape[:2]
        scale = min(canvas_w / w, canvas_h / h)
        new_w = max(1, int(w * scale))
        new_h = max(1, int(h * scale))

        frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
        frame = cv2.convertScaleAbs(frame, alpha=self.brightness, beta=0)

        image = Image.fromarray(frame)
        photo = ImageTk.PhotoImage(image=image)
        x_offset = (canvas_w - new_w) // 2
        y_offset = (canvas_h - new_h) // 2

        self.canvas.delete("all")
        self.canvas.create_image(x_offset, y_offset, anchor="nw", image=photo)
        self.canvas.image = photo

    def _seek_and_show(self, frame_index: int):
        if not self.cap:
            return

        frame_index = max(0, min(frame_index, max(0, self.total_frames - 1)))
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ok, frame = self.cap.read()
        if not ok:
            return

        self.current_frame = frame_index
        self._render_frame(frame)
        self._updating_progress = True
        try:
            self.progress_scale.set(self.current_frame)
        finally:
            self._updating_progress = False
        self._update_time_label()

    def _on_resize(self, _event):
        if self.cap:
            self._seek_and_show(self.current_frame)
        else:
            self._render_empty_preview()
