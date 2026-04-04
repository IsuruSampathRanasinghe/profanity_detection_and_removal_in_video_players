"""Processing pipeline UI mixin for filtering, progress, and result messages."""

import threading
from tkinter import messagebox


class ProcessingUIMixin:
    """Runs background filtering and updates progress/status widgets."""

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
            self.root.after(0, lambda: self._on_filter_error(str(exc)))
        finally:
            self.filtering_in_progress = False

    def _pipeline_progress_callback(self, percent: int, message: str):
        self._set_processing_progress(percent, message)

    def _on_filter_done(self, clean_video_path: str, profanities_count: int, mode: str):
        self.clean_video_path = clean_video_path
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
