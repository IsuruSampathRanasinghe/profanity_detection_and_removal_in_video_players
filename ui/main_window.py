"""Main Tkinter controller that composes UI mixins for the video player."""

from pathlib import Path
import tkinter as tk
from tkinter import ttk
import logging

import pygame

from config.settings import settings
from processing.pipeline import ProfanityProcessingPipeline
from utils.file_manager import safe_delete
from ui.audio_manager import AudioManagerMixin
from ui.file_handler import FileHandlerMixin
from ui.layout import LayoutMixin
from ui.playback import PlaybackMixin
from ui.processing_ui import ProcessingUIMixin
from ui.profanity_manager import ProfanityManagerMixin
from ui.theme import ThemeMixin
from ui.video_canvas import VideoCanvasMixin

logger = logging.getLogger(__name__)


class VideoPlayer(
    ThemeMixin,
    LayoutMixin,
    VideoCanvasMixin,
    PlaybackMixin,
    AudioManagerMixin,
    FileHandlerMixin,
    ProfanityManagerMixin,
    ProcessingUIMixin,
):
    """Central controller that delegates responsibilities to focused mixins."""

    style_cls = ttk.Style
    tk = tk

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Profanity Video Player")
        self.root.geometry("1320x900")
        self.root.minsize(1050, 700)
        self.root.resizable(True, True)

        self.pipeline = ProfanityProcessingPipeline(cfg=settings)
        self.dark_mode = tk.BooleanVar(value=True)

        self._setup_theme()

        self.mixer_ready = True
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2)
        except Exception as exc:
            logger.warning("Audio mixer init failed: %s", exc)
            self.mixer_ready = False

        self.cap = None
        self.current_video_path = None
        self.original_video_path = None
        self.clean_video_path = None
        self.audio_path = None
        self.generated_audio_paths: set[Path] = set()
        self.generated_processing_audio_paths: set[Path] = set()
        self.generated_video_paths: set[Path] = set()
        self.filtering_in_progress = False
        self.filter_mode = tk.StringVar(value=settings.filtering_mode)
        self.intelligence_mode = tk.StringVar(value=settings.filtering_mode)
        # Internal code (en/si/ta) and user-facing display name
        self.language_code = tk.StringVar(value="en")
        self.language_display = tk.StringVar(value="English")
        self._display_to_code = {"English": "en", "Sinhala": "si", "Tamil": "ta"}
        self._code_to_display = {v: k for k, v in self._display_to_code.items()}
        self.intelligence_mode_description_text = tk.StringVar(
            value="Strict filtering (removes all offensive words, including masked words)"
        )

        self.is_playing = False
        self.current_frame = 0
        self.total_frames = 0
        self.fps = 25.0
        self.timeline_detections = []
        self.review_detections = []
        self.selected_detection_index = -1
        self._preview_after_id = None

        self.playback_start_time = 0.0
        self.playback_start_frame = 0
        self.volume = 1.0
        self.brightness = 1.0
        # Capture current UI/player state into a dataclass for easier access
        # by non-UI logic and future refactors.
        import importlib

        UIState = None
        try:
            UIState = importlib.import_module('ui.state').UIState
        except Exception:
            try:
                UIState = importlib.import_module('.state', package=__package__).UIState
            except Exception:
                UIState = None

        if UIState is not None:
            self.ui_state = UIState(
            cap=self.cap,
            current_video_path=self.current_video_path,
            original_video_path=self.original_video_path,
            clean_video_path=self.clean_video_path,
            audio_path=self.audio_path,
            generated_audio_paths=set(self.generated_audio_paths),
            generated_processing_audio_paths=set(self.generated_processing_audio_paths),
            generated_video_paths=set(self.generated_video_paths),
            filtering_in_progress=self.filtering_in_progress,
            filter_mode=self.filter_mode.get() if hasattr(self.filter_mode, 'get') else str(self.filter_mode),
            intelligence_mode=self.intelligence_mode.get() if hasattr(self.intelligence_mode, 'get') else str(self.intelligence_mode),
            language_code=self.language_code.get() if hasattr(self.language_code, 'get') else str(self.language_code),
            language_display=self.language_display.get() if hasattr(self.language_display, 'get') else str(self.language_display),
            is_playing=self.is_playing,
            current_frame=self.current_frame,
            total_frames=self.total_frames,
            fps=self.fps,
            timeline_detections=list(self.timeline_detections),
            review_detections=list(self.review_detections),
            selected_detection_index=self.selected_detection_index,
            preview_after_id=self._preview_after_id,
            playback_start_time=self.playback_start_time,
            playback_start_frame=self.playback_start_frame,
            volume=self.volume,
            brightness=self.brightness,
            skip_seconds=self.skip_seconds,
            _updating_progress=self._updating_progress,
            _is_scrubbing=self._is_scrubbing,
            _resume_after_scrub=self._resume_after_scrub,
            processing_progress=self.processing_progress.get() if hasattr(self.processing_progress, 'get') else float(self.processing_progress),
            profanity_words=set(self.profanity_words),
            selected_profanity_word=self.selected_profanity_word.get() if hasattr(self.selected_profanity_word, 'get') else str(self.selected_profanity_word),
            current_video_label_text=self.current_video_label_text.get() if hasattr(self.current_video_label_text, 'get') else str(self.current_video_label_text),
            audio_status_text=self.audio_status_text.get() if hasattr(self.audio_status_text, 'get') else str(self.audio_status_text),
            filter_status_text=self.filter_status_text.get() if hasattr(self.filter_status_text, 'get') else str(self.filter_status_text),
            processing_status_text=self.processing_status_text.get() if hasattr(self.processing_status_text, 'get') else str(self.processing_status_text),
            processing_pct_text=self.processing_pct_text.get() if hasattr(self.processing_pct_text, 'get') else str(self.processing_pct_text),
            detection_review_summary_text=self.detection_review_summary_text.get() if hasattr(self.detection_review_summary_text, 'get') else str(self.detection_review_summary_text),
            volume_value_text=self.volume_value_text.get() if hasattr(self.volume_value_text, 'get') else str(self.volume_value_text),
            brightness_value_text=self.brightness_value_text.get() if hasattr(self.brightness_value_text, 'get') else str(self.brightness_value_text),
        )
        self.skip_seconds = 5
        self._updating_progress = False
        self._is_scrubbing = False
        self._resume_after_scrub = False
        self.processing_progress = tk.DoubleVar(value=0.0)

        self.profanity_words: set[str] = set()
        self.selected_profanity_word = tk.StringVar(value="")
        self.current_video_label_text = tk.StringVar(value="No video loaded")
        self.audio_status_text = tk.StringVar(value="Audio: idle")
        self.filter_status_text = tk.StringVar(value="Filter: idle")
        self.processing_status_text = tk.StringVar(value="Ready")
        self.processing_pct_text = tk.StringVar(value="0%")
        self.detection_review_summary_text = tk.StringVar(value="No detections yet")
        self.volume_value_text = tk.StringVar(value="100%")
        self.brightness_value_text = tk.StringVar(value="100%")
        self.bottom_panel_visible = True
        self.bottom_toggle_text = tk.StringVar(value="Hide Bottom Panel")
        self.is_fullscreen = False

        self._build_ui()
        self._set_clean_video_actions_enabled(False)
        self._apply_theme()
        self._load_profanity_words()
        self._set_review_buttons_enabled(False)
        self.language_code.trace_add("write", self._on_language_changed)
        self.language_display.trace_add("write", self._on_language_display_changed)
        self.intelligence_mode.trace_add("write", self._update_intelligence_mode_description)
        self._update_intelligence_mode_description()
        self.root.bind("<Left>", self._on_skip_backward_key)
        self.root.bind("<Right>", self._on_skip_forward_key)
        self._render_empty_preview()

    def _on_volume_change(self, value):
        self.volume = max(0.0, min(1.0, float(value) / 100.0))
        self.volume_value_text.set(f"{int(self.volume * 100)}%")
        if self.mixer_ready:
            try:
                pygame.mixer.music.set_volume(self.volume)
            except Exception as e:
                logger.debug("Failed to set mixer volume: %s", e)

    def _on_brightness_change(self, value):
        self.brightness = max(0.5, min(1.5, float(value) / 100.0))
        self.brightness_value_text.set(f"{int(self.brightness * 100)}%")
        if self.cap and not self.is_playing:
            self._seek_and_show(self.current_frame)

    def _on_language_display_changed(self, *_args):
        # Map user-facing selection to internal code and trigger existing change handler
        display = self.language_display.get().strip()
        code = self._display_to_code.get(display, "en")
        if self.language_code.get() != code:
            self.language_code.set(code)

    def cleanup(self):
        if self._preview_after_id is not None:
            try:
                self.root.after_cancel(self._preview_after_id)
            except Exception as e:
                logger.debug("Failed to cancel preview after_id: %s", e)
            self._preview_after_id = None

        self.stop_video(reset_frame=False)

        if self.mixer_ready and hasattr(pygame.mixer.music, "unload"):
            try:
                pygame.mixer.music.unload()
            except Exception as e:
                logger.debug("Failed to unload mixer music: %s", e)

        if self.cap:
            self.cap.release()
            self.cap = None

        for path in list(self.generated_audio_paths):
            safe_delete(path)
            self.generated_audio_paths.discard(path)

        for path in list(self.generated_processing_audio_paths):
            safe_delete(path)
            self.generated_processing_audio_paths.discard(path)

        for path in list(self.generated_video_paths):
            safe_delete(path)
            self.generated_video_paths.discard(path)

        # Remove temporary audio files created during processing
        try:
            temp_dir = settings.base_dir / "temp_audio"
            if temp_dir.exists() and temp_dir.is_dir():
                for p in temp_dir.iterdir():
                    if p.is_file():
                        safe_delete(p)
                try:
                    temp_dir.rmdir()
                except Exception:
                    pass
        except Exception as e:
            logger.debug("Failed cleaning temp_audio: %s", e)

        # Remove intermediate audio files in the audio dir (best-effort)
        try:
            for p in settings.audio_dir.glob("*_source.wav"):
                safe_delete(p)
            for p in settings.audio_dir.glob("*_clean.wav"):
                safe_delete(p)
        except Exception as e:
            logger.debug("Failed cleaning audio_dir intermediates: %s", e)

        # Attempt to remove empty audio/outputs directories if left empty
        try:
            if settings.audio_dir.exists() and not any(settings.audio_dir.iterdir()):
                try:
                    settings.audio_dir.rmdir()
                except Exception:
                    pass
        except Exception:
            pass

        try:
            if settings.outputs_dir.exists() and not any(settings.outputs_dir.iterdir()):
                try:
                    settings.outputs_dir.rmdir()
                except Exception:
                    pass
        except Exception:
            pass


def launch_video_player():
    """Run the desktop player UI."""
    root = tk.Tk()
    player = VideoPlayer(root)

    def on_close():
        player.cleanup()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()
