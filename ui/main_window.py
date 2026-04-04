"""Main Tkinter controller that composes UI mixins for the video player."""

from pathlib import Path
import tkinter as tk
from tkinter import ttk

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
            print(f"Audio mixer init failed: {exc}")
            self.mixer_ready = False

        self.cap = None
        self.current_video_path = None
        self.original_video_path = None
        self.clean_video_path = None
        self.audio_path = None
        self.generated_audio_paths: set[Path] = set()
        self.filtering_in_progress = False
        self.filter_mode = tk.StringVar(value=settings.filter_mode)
        self.intelligence_mode = tk.StringVar(value=settings.filtering_mode)
        self.language_code = tk.StringVar(value="auto")
        self.intelligence_mode_description_text = tk.StringVar(
            value="Strict filtering (removes all offensive words, including masked words)"
        )

        self.is_playing = False
        self.current_frame = 0
        self.total_frames = 0
        self.fps = 25.0

        self.playback_start_time = 0.0
        self.playback_start_frame = 0
        self.volume = 1.0
        self.brightness = 1.0
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
        self.volume_value_text = tk.StringVar(value="100%")
        self.brightness_value_text = tk.StringVar(value="100%")
        self.bottom_panel_visible = True
        self.bottom_toggle_text = tk.StringVar(value="Hide Bottom Panel")
        self.is_fullscreen = False

        self._build_ui()
        self._apply_theme()
        self._load_profanity_words()
        self.language_code.trace_add("write", self._on_language_changed)
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
            except Exception:
                pass

    def _on_brightness_change(self, value):
        self.brightness = max(0.5, min(1.5, float(value) / 100.0))
        self.brightness_value_text.set(f"{int(self.brightness * 100)}%")
        if self.cap and not self.is_playing:
            self._seek_and_show(self.current_frame)

    def cleanup(self):
        self.stop_video(reset_frame=False)

        if self.mixer_ready and hasattr(pygame.mixer.music, "unload"):
            try:
                pygame.mixer.music.unload()
            except Exception:
                pass

        if self.cap:
            self.cap.release()
            self.cap = None

        for path in list(self.generated_audio_paths):
            safe_delete(path)
            self.generated_audio_paths.discard(path)


def launch_video_player():
    """Run the desktop player UI."""
    root = tk.Tk()
    player = VideoPlayer(root)

    def on_close():
        player.cleanup()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()
