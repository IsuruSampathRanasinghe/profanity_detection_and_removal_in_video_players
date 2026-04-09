"""Processing pipeline UI mixin for filtering, progress, and result messages."""

from pathlib import Path
import threading
from tkinter import messagebox

from config.settings import settings
from utils.file_manager import build_processing_paths


class ProcessingUIMixin:
    """Runs background filtering and updates progress/status widgets."""

    def _set_review_buttons_enabled(self, enabled: bool):
        state = ["!disabled"] if enabled else ["disabled"]
        for button_name in ("review_prev_btn", "review_jump_btn", "review_preview_btn", "review_next_btn"):
            button = getattr(self, button_name, None)
            if button is not None:
                button.state(state)

    def _format_timestamp(self, seconds: float) -> str:
        safe_seconds = max(0.0, float(seconds))
        minutes = int(safe_seconds // 60)
        remaining = safe_seconds % 60
        return f"{minutes:02d}:{remaining:05.2f}"

    def _refresh_detection_review(self, detections):
        self.review_detections = list(detections or [])
        self.selected_detection_index = -1

        if not hasattr(self, "detection_tree"):
            return

        tree = self.detection_tree
        for item_id in tree.get_children():
            tree.delete(item_id)

        for index, detection in enumerate(self.review_detections):
            timestamp = self._format_timestamp(getattr(detection, "start", 0.0))
            word = getattr(detection, "word", "") or "(unknown)"
            confidence_value = float(getattr(detection, "confidence", 0.0))
            confidence = f"{confidence_value * 100:.0f}%"
            tree.insert("", "end", iid=str(index), values=(timestamp, word, confidence))

        total = len(self.review_detections)
        self.detection_review_summary_text.set(f"{total} detections ready for review")
        self._set_review_buttons_enabled(total > 0)

    def _clear_detection_review(self):
        self.review_detections = []
        self.selected_detection_index = -1
        self.detection_review_summary_text.set("No detections yet")

        if hasattr(self, "detection_tree"):
            tree = self.detection_tree
            for item_id in tree.get_children():
                tree.delete(item_id)

        self._set_review_buttons_enabled(False)

    def _on_detection_selected(self, _event=None):
        if not hasattr(self, "detection_tree"):
            return

        selected = self.detection_tree.selection()
        if not selected:
            self.selected_detection_index = -1
            self._set_review_buttons_enabled(bool(self.review_detections))
            return

        try:
            self.selected_detection_index = int(selected[0])
        except ValueError:
            self.selected_detection_index = -1

        self._set_review_buttons_enabled(self.selected_detection_index >= 0)

    def _select_detection_index(self, index: int):
        if not self.review_detections or not hasattr(self, "detection_tree"):
            return

        bounded_index = max(0, min(index, len(self.review_detections) - 1))
        iid = str(bounded_index)
        self.detection_tree.selection_set(iid)
        self.detection_tree.focus(iid)
        self.detection_tree.see(iid)
        self.selected_detection_index = bounded_index
        self._set_review_buttons_enabled(True)

    def _select_previous_detection(self):
        if not self.review_detections:
            return
        if self.selected_detection_index < 0:
            self._select_detection_index(0)
            return
        self._select_detection_index(self.selected_detection_index - 1)

    def _select_next_detection(self):
        if not self.review_detections:
            return
        if self.selected_detection_index < 0:
            self._select_detection_index(0)
            return
        self._select_detection_index(self.selected_detection_index + 1)

    def _jump_to_selected_detection(self):
        if not self.cap or self.selected_detection_index < 0:
            return

        if self.selected_detection_index >= len(self.review_detections):
            return

        detection = self.review_detections[self.selected_detection_index]
        target_frame = int(max(0.0, float(detection.start)) * self.fps)
        self._seek_and_show(target_frame)

    def _preview_selected_detection(self, _event=None):
        if not self.cap or self.selected_detection_index < 0:
            return

        if self.selected_detection_index >= len(self.review_detections):
            return

        detection = self.review_detections[self.selected_detection_index]
        preview_start = max(0.0, float(detection.start) - 0.25)
        preview_end = max(preview_start, float(detection.end) + 0.35)
        preview_duration_ms = int(max(500, min(2500, (preview_end - preview_start) * 1000)))

        if self._preview_after_id is not None:
            try:
                self.root.after_cancel(self._preview_after_id)
            except Exception:
                pass
            self._preview_after_id = None

        target_frame = int(preview_start * self.fps)
        self._seek_and_show(target_frame)
        self.play_video()

        def _stop_preview():
            self.pause_video()
            self._preview_after_id = None

        self._preview_after_id = self.root.after(preview_duration_ms, _stop_preview)

    def filter_profanity(self):
        if not self.original_video_path:
            messagebox.showwarning("Warning", "Load a video first")
            return

        if self.filtering_in_progress:
            return

        self.filtering_in_progress = True
        self._set_processing_progress(0, "Preparing...")

        worker = threading.Thread(target=self._filter_profanity_worker, daemon=True)
        worker.start()

    def _filter_profanity_worker(self):
        try:
            paths = build_processing_paths(self.original_video_path, settings)
            self.generated_processing_audio_paths.update(
                {Path(paths["extracted_audio"]), Path(paths["clean_audio"])}
            )
            self.generated_video_paths.add(Path(paths["output_video"]))

            language = self.language_code.get().strip().lower() if hasattr(self, "language_code") else "auto"
            whisper_language = None if language == "auto" else language
            output_path, count = self.pipeline.process_video(
                video_path=self.original_video_path,
                replacement_mode=self.filter_mode.get(),
                intelligence_mode=self.intelligence_mode.get(),
                language=whisper_language,
                on_progress=self._pipeline_progress_callback,
            )
            self.root.after(0, lambda: self._on_filter_done(output_path, count, self.intelligence_mode.get()))
        except Exception as exc:
            self.root.after(0, lambda e=exc: self._on_filter_error(str(e)))
        finally:
            self.filtering_in_progress = False

    def _pipeline_progress_callback(self, percent: int, message: str):
        self._set_processing_progress(percent, message)

    def _on_filter_done(self, clean_video_path: str, profanities_count: int, mode: str):
        self.clean_video_path = clean_video_path
        detections = getattr(self.pipeline, "last_detections", [])
        self._refresh_timeline_markers(detections)
        self._refresh_detection_review(detections)
        self._set_filter_status(f"✔ {profanities_count} profanities filtered ({mode.capitalize()} mode)", self.palette["success"])
        self.processing_status_text.set("Filtering completed!")
        self.processing_pct_text.set("100%")
        messagebox.showinfo("Success", f"Clean video created:\n{clean_video_path}")

    def _on_filter_error(self, err_text: str):
        self._set_processing_progress(0, "Failed", self.palette["danger"])
        self._set_filter_status("Filter: failed", self.palette["danger"])
        messagebox.showerror("Filtering Error", err_text)

    def _set_filter_status(self, text: str, color: str | None = None):
        def _apply():
            self.filter_status_text.set(text)
            if color:
                self.filter_status_label.configure(foreground=color)

        self.root.after(0, _apply)

    def _set_processing_progress(self, value: int, status_text: str | None = None, status_color: str | None = None):
        progress_value = max(0, min(100, int(value)))

        def _update():
            self.processing_progress.set(progress_value)
            self.processing_pct_text.set(f"{progress_value}%")
            if status_text is not None:
                self.processing_status_text.set(status_text)
            if status_color:
                self.processing_status_label.configure(foreground=status_color)

        self.root.after(0, _update)
