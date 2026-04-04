"""Tkinter UI for video playback and profanity-filter pipeline execution."""

import os
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import cv2
import pygame
from PIL import Image, ImageTk

from config.settings import settings
from processing.audio_extractor import extract_audio
from processing.pipeline import ProfanityProcessingPipeline
from utils.file_manager import read_profanity_words, safe_delete, write_profanity_words


class VideoPlayer:
    """Desktop UI for loading, filtering, and previewing videos."""

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
        self.root.bind("<Left>", self._on_skip_backward_key)
        self.root.bind("<Right>", self._on_skip_forward_key)
        self._render_empty_preview()

    def _setup_theme(self):
        """Configure the app theme and shared widget styles."""
        self.style = ttk.Style()
        self.style.theme_use("clam")

        self.dark_palette = {
            "bg": "#0f172a",
            "panel": "#111827",
            "panel_alt": "#172033",
            "surface": "#1f2937",
            "surface_alt": "#243247",
            "border": "#334155",
            "text": "#f8fafc",
            "muted": "#94a3b8",
            "accent": "#7c3aed",
            "accent_hover": "#8b5cf6",
            "success": "#10b981",
            "success_hover": "#34d399",
            "warning": "#f59e0b",
            "warning_hover": "#fbbf24",
            "danger": "#ef4444",
            "danger_hover": "#f87171",
            "info": "#0ea5e9",
            "info_hover": "#38bdf8",
            "play": "#22c55e",
            "play_hover": "#4ade80",
            "stop": "#dc2626",
            "stop_hover": "#f87171",
            "pause": "#f97316",
            "pause_hover": "#fb923c",
            "video_bg": "#050816",
            "entry_bg": "#0b1220",
            "list_bg": "#0b1220",
            "list_select": "#7c3aed",
        }

        self.light_palette = {
            "bg": "#eef2f7",
            "panel": "#ffffff",
            "panel_alt": "#f8fafc",
            "surface": "#f1f5f9",
            "surface_alt": "#e2e8f0",
            "border": "#cbd5e1",
            "text": "#0f172a",
            "muted": "#475569",
            "accent": "#6d28d9",
            "accent_hover": "#7c3aed",
            "success": "#059669",
            "success_hover": "#10b981",
            "warning": "#d97706",
            "warning_hover": "#f59e0b",
            "danger": "#dc2626",
            "danger_hover": "#ef4444",
            "info": "#0284c7",
            "info_hover": "#0ea5e9",
            "play": "#16a34a",
            "play_hover": "#22c55e",
            "stop": "#b91c1c",
            "stop_hover": "#dc2626",
            "pause": "#ea580c",
            "pause_hover": "#f97316",
            "video_bg": "#0f172a",
            "entry_bg": "#ffffff",
            "list_bg": "#ffffff",
            "list_select": "#6d28d9",
        }

        self._configure_styles()

    def _configure_styles(self):
        """Configure ttk styles using the active palette."""
        self.palette = self.dark_palette if self.dark_mode.get() else self.light_palette
        p = self.palette

        self.root.configure(bg=p["bg"])
        self.style.configure("App.TFrame", background=p["bg"])
        self.style.configure("Panel.TFrame", background=p["panel"])
        self.style.configure("PanelAlt.TFrame", background=p["panel_alt"])
        self.style.configure("Section.TLabelframe", background=p["panel"], borderwidth=1, relief="solid")
        self.style.configure("Section.TLabelframe.Label", background=p["panel"], foreground=p["text"], font=("Segoe UI", 10, "bold"))
        self.style.configure("App.TLabel", background=p["bg"], foreground=p["text"], font=("Segoe UI", 10))
        self.style.configure("Title.TLabel", background=p["bg"], foreground=p["text"], font=("Segoe UI Semibold", 11))
        self.style.configure("Muted.TLabel", background=p["bg"], foreground=p["muted"], font=("Segoe UI", 9))
        self.style.configure("SectionLabel.TLabel", background=p["panel"], foreground=p["muted"], font=("Segoe UI", 9))
        self.style.configure("Status.TLabel", background=p["panel"], foreground=p["text"], font=("Segoe UI Semibold", 9))
        self.style.configure("Small.TLabel", background=p["panel"], foreground=p["muted"], font=("Segoe UI", 8))
        self.style.configure("App.TEntry", padding=6, fieldbackground=p["entry_bg"], foreground=p["text"], insertcolor=p["text"])
        self.style.configure("App.TButton", padding=(10, 6), font=("Segoe UI Semibold", 10), borderwidth=0)
        self.style.configure("Compact.TButton", padding=(8, 4), font=("Segoe UI", 9), borderwidth=0)
        self.style.configure("Primary.TButton", background=p["info"], foreground="white")
        self.style.map("Primary.TButton", background=[("active", p["info_hover"]), ("pressed", p["info"])])
        self.style.configure("Accent.TButton", background=p["accent"], foreground="white")
        self.style.map("Accent.TButton", background=[("active", p["accent_hover"]), ("pressed", p["accent"])])
        self.style.configure("Success.TButton", background=p["play"], foreground="white")
        self.style.map("Success.TButton", background=[("active", p["play_hover"]), ("pressed", p["play"])])
        self.style.configure("Warning.TButton", background=p["pause"], foreground="white")
        self.style.map("Warning.TButton", background=[("active", p["pause_hover"]), ("pressed", p["pause"])])
        self.style.configure("Danger.TButton", background=p["stop"], foreground="white")
        self.style.map("Danger.TButton", background=[("active", p["stop_hover"]), ("pressed", p["stop"])])
        self.style.configure("Neutral.TButton", background=p["surface"], foreground=p["text"])
        self.style.map("Neutral.TButton", background=[("active", p["surface_alt"]), ("pressed", p["surface"])])
        self.style.configure("Toggle.TRadiobutton", background=p["panel"], foreground=p["text"], font=("Segoe UI", 10))
        self.style.map("Toggle.TRadiobutton", foreground=[("selected", p["accent"]), ("active", p["text"])])
        self.style.configure("TCheckbutton", background=p["panel"], foreground=p["text"], font=("Segoe UI", 10))
        self.style.map("TCheckbutton", foreground=[("active", p["text"]), ("selected", p["accent"])])
        self.style.configure("App.Horizontal.TProgressbar", troughcolor=p["surface_alt"], background=p["accent"], bordercolor=p["border"], lightcolor=p["accent"], darkcolor=p["accent"])

    def _apply_theme(self):
        """Apply the active palette to tk widgets and refresh the empty preview."""
        p = self.palette
        self.root.configure(bg=p["bg"])

        for widget in (
            getattr(self, name, None)
            for name in (
                "container",
                "top_frame",
                "status_strip",
                "video_frame",
                "video_shell",
                "playback_section",
                "controls_frame",
                "bottom_frame",
                "settings_section",
                "profanity_card",
                "processing_card",
            )
        ):
            if widget is not None:
                try:
                    widget.configure(style="App.TFrame")
                except Exception:
                    try:
                        widget.configure(bg=p["bg"])
                    except Exception:
                        pass

        for widget in (
            getattr(self, name, None)
            for name in (
                "current_video_label",
                "audio_status_label",
                "filter_status_label",
                "processing_status_label",
                "processing_pct_label",
                "time_label",
                "theme_hint_label",
                "volume_value_label",
                "brightness_value_label",
                "selected_word_label",
                "profanity_count_label",
            )
        ):
            if widget is not None:
                try:
                    widget.configure(background=p["panel"], foreground=p["text"])
                except Exception:
                    try:
                        widget.configure(bg=p["panel"], fg=p["text"])
                    except Exception:
                        pass

        if hasattr(self, "canvas"):
            self.canvas.configure(bg=p["video_bg"], highlightbackground=p["border"], highlightthickness=1)
        if hasattr(self, "profanity_entry"):
            try:
                self.profanity_entry.configure(highlightbackground=p["border"], highlightcolor=p["accent"])
            except Exception:
                pass
        if hasattr(self, "profanity_listbox"):
            self.profanity_listbox.configure(background=p["list_bg"], foreground=p["text"], selectbackground=p["list_select"], selectforeground="white", highlightbackground=p["border"], highlightcolor=p["accent"], relief="flat")
        self._render_empty_preview()

    def _create_button(self, parent, text=None, command=None, style_name="App.TButton", textvariable=None):
        """Create a consistently styled button."""
        kwargs = {"command": command, "style": style_name}
        if textvariable is not None:
            kwargs["textvariable"] = textvariable
        else:
            kwargs["text"] = text
        return ttk.Button(parent, **kwargs)

    def _toggle_fullscreen(self):
        """Toggle fullscreen mode for focused video viewing."""
        self.is_fullscreen = not self.is_fullscreen
        self.root.attributes("-fullscreen", self.is_fullscreen)

    def _toggle_bottom_panel(self):
        """Show or hide the bottom panel to prioritize video area."""
        if self.bottom_panel_visible:
            self.bottom_frame.grid_remove()
            self.container.rowconfigure(3, weight=0)
            self.bottom_toggle_text.set("Show Bottom Panel")
        else:
            self.bottom_frame.grid()
            self.container.rowconfigure(3, weight=2)
            self.bottom_toggle_text.set("Hide Bottom Panel")
        self.bottom_panel_visible = not self.bottom_panel_visible

    def _build_slider_card(self, parent, column, title, command, initial_value, value_text_var):
        card = ttk.Frame(parent, style="Panel.TFrame", padding=(4, 0))
        card.grid(row=0, column=column, sticky="ew", padx=(0 if column == 0 else 12, 0))
        card.columnconfigure(0, weight=1)

        ttk.Label(card, text=title, style="SectionLabel.TLabel").grid(row=0, column=0, sticky="w")
        scale = ttk.Scale(card, from_=0 if title == "Volume" else 50, to=100 if title == "Volume" else 150, orient=tk.HORIZONTAL, command=command)
        scale.grid(row=1, column=0, sticky="ew", pady=(8, 2))
        value_label = ttk.Label(card, textvariable=value_text_var, style="Small.TLabel")
        value_label.grid(row=2, column=0, sticky="w")
        scale.set(initial_value)

        if title == "Volume":
            self.volume_scale = scale
            self.volume_value_label = value_label
        else:
            self.brightness_scale = scale
            self.brightness_value_label = value_label
        return card

    def _on_theme_toggle(self):
        """Switch between light and dark themes."""
        self._configure_styles()
        self._apply_theme()

    def _render_empty_preview(self):
        """Show a centered placeholder when no video is loaded."""
        if not hasattr(self, "canvas"):
            return
        self.canvas.delete("all")
        self.canvas.create_text(
            max(20, self.canvas.winfo_width() // 2),
            max(20, self.canvas.winfo_height() // 2),
            text="No video loaded",
            fill=self.palette["muted"],
            font=("Segoe UI Semibold", 20),
        )

    def _update_current_word_label(self):
        selected = self.selected_profanity_word.get().strip()
        if selected:
            self.selected_word_label.configure(text=f"Selected: {selected}")
        else:
            self.selected_word_label.configure(text="Select a word to remove it")

    def _set_video_status(self, text: str):
        self.current_video_label_text.set(text)

    def _build_ui(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Main container with explicit vertical hierarchy.
        self.container = ttk.Frame(self.root, style="App.TFrame", padding=(14, 12, 14, 12))
        self.container.grid(row=0, column=0, sticky="nsew")
        self.container.columnconfigure(0, weight=1)
        self.container.rowconfigure(0, weight=0)  # top_frame
        self.container.rowconfigure(1, weight=6)  # video_frame (dominant)
        self.container.rowconfigure(2, weight=1)  # controls_frame
        self.container.rowconfigure(3, weight=2)  # bottom_frame

        # 1) Top Bar: minimal controls only.
        self.top_frame = ttk.Frame(self.container, style="App.TFrame")
        self.top_frame.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        self.top_frame.columnconfigure(4, weight=1)
        self.top_frame.columnconfigure(0, weight=0)

        self._create_button(self.top_frame, "Load Video", self.open_video, "Primary.TButton").grid(row=0, column=0, sticky="w", padx=(0, 8))
        self._create_button(self.top_frame, "Filter Profanity", self.filter_profanity, "Accent.TButton").grid(row=0, column=1, sticky="w", padx=(0, 8))
        ttk.Checkbutton(self.top_frame, text="Dark mode", variable=self.dark_mode, command=self._on_theme_toggle, style="TCheckbutton").grid(row=0, column=2, sticky="w", padx=(0, 8))
        self._create_button(self.top_frame, "Fullscreen", self._toggle_fullscreen, "Compact.TButton").grid(row=0, column=3, sticky="w", padx=(0, 8))
        self._create_button(self.top_frame, textvariable=self.bottom_toggle_text, command=self._toggle_bottom_panel, style_name="Compact.TButton").grid(row=0, column=5, sticky="e")

        # Lightweight status strip under the top bar.
        self.status_strip = ttk.Frame(self.top_frame, style="Panel.TFrame", padding=(8, 6, 8, 6))
        self.status_strip.grid(row=1, column=0, columnspan=6, sticky="ew", pady=(8, 0))
        status_row = ttk.Frame(self.status_strip, style="Panel.TFrame")
        status_row.pack(fill=tk.X)
        self.current_video_label = ttk.Label(status_row, textvariable=self.current_video_label_text, style="Status.TLabel")
        self.current_video_label.pack(side=tk.LEFT, padx=(0, 16))
        self.audio_status_label = ttk.Label(status_row, textvariable=self.audio_status_text, style="Status.TLabel")
        self.audio_status_label.pack(side=tk.LEFT, padx=(0, 16))
        self.filter_status_label = ttk.Label(status_row, textvariable=self.filter_status_text, style="Status.TLabel")
        self.filter_status_label.pack(side=tk.LEFT)

        # 2) Main Video Area: dominant, centered, responsive.
        self.video_frame = ttk.Frame(self.container, style="App.TFrame")
        self.video_frame.grid(row=1, column=0, sticky="nsew", pady=(8, 10))
        self.video_frame.columnconfigure(0, weight=1)
        self.video_frame.rowconfigure(0, weight=1)

        self.video_shell = tk.Frame(self.video_frame, bd=0, highlightthickness=1)
        self.video_shell.grid(row=0, column=0, sticky="nsew")
        self.video_shell.rowconfigure(0, weight=1)
        self.video_shell.columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(self.video_shell, highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.canvas.bind("<Configure>", self._on_resize)

        # 3) Playback controls directly under video.
        self.controls_frame = ttk.Frame(self.container, style="App.TFrame")
        self.controls_frame.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        self.controls_frame.columnconfigure(0, weight=1)

        self.playback_section = ttk.Labelframe(self.controls_frame, text="Playback", style="Section.TLabelframe", padding=(12, 10))
        self.playback_section.grid(row=0, column=0, sticky="ew")
        self.playback_section.columnconfigure(0, weight=0)
        self.playback_section.columnconfigure(1, weight=0)
        self.playback_section.columnconfigure(2, weight=0)
        self.playback_section.columnconfigure(3, weight=1)
        self.playback_section.columnconfigure(4, weight=0)
        self.playback_section.columnconfigure(5, weight=0)
        self.playback_section.columnconfigure(6, weight=0)

        self._create_button(self.playback_section, "Play Original", self.play_original_video, "Success.TButton").grid(row=0, column=0, sticky="w", padx=(0, 6))
        self._create_button(self.playback_section, "Play Clean", self.play_clean_video, "Success.TButton").grid(row=0, column=1, sticky="w", padx=(0, 6))
        self._create_button(self.playback_section, "Pause", self.pause_video, "Warning.TButton").grid(row=0, column=2, sticky="w", padx=(0, 10))
        self.progress_scale = ttk.Scale(self.playback_section, from_=0, to=100, orient=tk.HORIZONTAL, command=self._on_seek)
        self.progress_scale.grid(row=0, column=3, sticky="ew", padx=(0, 10))
        self.progress_scale.bind("<ButtonPress-1>", self._on_timeline_press)
        self.progress_scale.bind("<ButtonRelease-1>", self._on_timeline_release)
        self._create_button(self.playback_section, "-5s", self.skip_backward, "Compact.TButton").grid(row=0, column=4, sticky="e", padx=(0, 6))
        self._create_button(self.playback_section, "+5s", self.skip_forward, "Compact.TButton").grid(row=0, column=5, sticky="e", padx=(0, 6))
        self._create_button(self.playback_section, "Stop", self.stop_video, "Danger.TButton").grid(row=0, column=6, sticky="e", padx=(0, 8))
        self.time_label = ttk.Label(self.playback_section, text="00:00 / 00:00", style="Title.TLabel")
        self.time_label.grid(row=0, column=7, sticky="e")

        # 4) Bottom panel: compact stack (settings, profanity, processing).
        self.bottom_frame = ttk.Frame(self.container, style="App.TFrame")
        self.bottom_frame.grid(row=3, column=0, sticky="nsew")
        self.bottom_frame.columnconfigure(0, weight=1)
        self.bottom_frame.rowconfigure(1, weight=1)

        self.settings_section = ttk.Labelframe(self.bottom_frame, text="Settings", style="Section.TLabelframe", padding=(12, 10))
        self.settings_section.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        for column in range(3):
            self.settings_section.columnconfigure(column, weight=1)

        self._build_slider_card(self.settings_section, 0, "Volume", self._on_volume_change, 100, self.volume_value_text)
        self._build_slider_card(self.settings_section, 1, "Brightness", self._on_brightness_change, 100, self.brightness_value_text)

        filter_card = ttk.Frame(self.settings_section, style="Panel.TFrame", padding=(4, 0))
        filter_card.grid(row=0, column=2, sticky="ew", padx=(12, 0))
        filter_card.columnconfigure(0, weight=1)
        ttk.Label(filter_card, text="Filter Mode", style="SectionLabel.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(filter_card, text="Mute", variable=self.filter_mode, value="mute", style="Toggle.TRadiobutton").grid(row=1, column=0, sticky="w", pady=(6, 2))
        ttk.Radiobutton(filter_card, text="Beep", variable=self.filter_mode, value="beep", style="Toggle.TRadiobutton").grid(row=2, column=0, sticky="w")

        self.profanity_card = ttk.Labelframe(self.bottom_frame, text="Profanity Management", style="Section.TLabelframe", padding=(12, 10))
        self.profanity_card.grid(row=1, column=0, sticky="nsew", pady=(0, 8))
        self.profanity_card.columnconfigure(0, weight=1)
        self.profanity_card.rowconfigure(2, weight=1)

        profanity_input_row = ttk.Frame(self.profanity_card, style="Panel.TFrame")
        profanity_input_row.grid(row=0, column=0, sticky="ew")
        profanity_input_row.columnconfigure(0, weight=1)

        self.profanity_entry = ttk.Entry(profanity_input_row, style="App.TEntry")
        self.profanity_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.profanity_entry.bind("<Return>", self._add_profanity_word)
        self._create_button(profanity_input_row, "Add", self._add_profanity_word, "Compact.TButton").grid(row=0, column=1, padx=(0, 6))
        self._create_button(profanity_input_row, "Remove", self._remove_selected_profanity_word, "Compact.TButton").grid(row=0, column=2)

        self.profanity_count_label = ttk.Label(self.profanity_card, text="Profanity list: 0 words", style="Muted.TLabel")
        self.profanity_count_label.grid(row=1, column=0, sticky="w", pady=(6, 6))

        list_frame = ttk.Frame(self.profanity_card, style="Panel.TFrame")
        list_frame.grid(row=2, column=0, sticky="nsew")
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        self.profanity_listbox = tk.Listbox(list_frame, exportselection=False, activestyle="none", selectmode=tk.SINGLE, height=5)
        self.profanity_listbox.grid(row=0, column=0, sticky="nsew")
        self.profanity_listbox.bind("<<ListboxSelect>>", self._on_profanity_select)
        self.profanity_listbox.bind("<Delete>", lambda _event: self._remove_selected_profanity_word())

        list_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.profanity_listbox.yview)
        list_scrollbar.grid(row=0, column=1, sticky="ns")
        self.profanity_listbox.configure(yscrollcommand=list_scrollbar.set)
        self.selected_word_label = ttk.Label(self.profanity_card, text="Select a word to remove it", style="Small.TLabel")
        self.selected_word_label.grid(row=3, column=0, sticky="w", pady=(6, 0))

        self.processing_card = ttk.Labelframe(self.bottom_frame, text="Processing Progress", style="Section.TLabelframe", padding=(12, 10))
        self.processing_card.grid(row=2, column=0, sticky="ew")
        self.processing_card.columnconfigure(0, weight=1)
        self.processing_status_label = ttk.Label(self.processing_card, textvariable=self.processing_status_text, style="Title.TLabel")
        self.processing_status_label.grid(row=0, column=0, sticky="w")

        progress_row = ttk.Frame(self.processing_card, style="Panel.TFrame")
        progress_row.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        progress_row.columnconfigure(0, weight=1)
        self.processing_bar = ttk.Progressbar(progress_row, orient=tk.HORIZONTAL, mode="determinate", maximum=100, variable=self.processing_progress, style="App.Horizontal.TProgressbar")
        self.processing_bar.grid(row=0, column=0, sticky="ew")
        self.processing_pct_label = ttk.Label(progress_row, textvariable=self.processing_pct_text, style="Title.TLabel")
        self.processing_pct_label.grid(row=0, column=1, sticky="e", padx=(12, 0))

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
            result = self.pipeline.process_video(
                video_path=self.original_video_path,
                replacement_mode=self.filter_mode.get(),
                detection_mode=settings.detection_mode,
                on_progress=self._pipeline_progress_callback,
            )
            self.root.after(0, lambda: self._on_filter_done(result.output_video_path, len(result.detections)))
        except Exception as exc:
            self.root.after(0, lambda: self._on_filter_error(str(exc)))
        finally:
            self.filtering_in_progress = False

    def _pipeline_progress_callback(self, percent: int, message: str):
        self._set_processing_progress(percent, message)

    def _on_filter_done(self, clean_video_path: str, muted_count: int):
        self.clean_video_path = clean_video_path
        self._set_filter_status(f"Filter: done ({muted_count} muted)", self.palette["success"])
        self.processing_status_text.set("Completed")
        self.processing_pct_text.set("100%")
        messagebox.showinfo("Success", f"Clean video created:\n{clean_video_path}")

    def _on_filter_error(self, err_text: str):
        self._set_processing_progress(0, "Failed", self.palette["danger"])
        self._set_filter_status("Filter: failed", self.palette["danger"])
        messagebox.showerror("Filtering Error", err_text)

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
        frame = cv2.convertScaleAbs(frame, alpha=self.brightness, beta=0)

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

    def _on_skip_backward_key(self, _event):
        self.skip_backward()

    def _on_skip_forward_key(self, _event):
        self.skip_forward()

    def _on_seek(self, value):
        if not self.cap:
            return
        if self._updating_progress:
            return

        if not self.is_playing:
            self._seek_and_show(int(float(value)))

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

    def _on_resize(self, _event):
        if self.cap:
            self._seek_and_show(self.current_frame)
        else:
            self._render_empty_preview()

    def _update_time_label(self):
        cur = self.current_frame / self.fps if self.fps > 0 else 0
        total = self.total_frames / self.fps if self.fps > 0 else 0
        self.time_label.configure(text=f"{self._fmt_time(cur)} / {self._fmt_time(total)}")

    def _set_audio_status(self, text: str, color: str | None = None):
        self.audio_status_text.set(text)
        if color:
            self.audio_status_label.configure(foreground=color)

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

    def _load_profanity_words(self):
        self.profanity_words = read_profanity_words(settings.profanity_file)
        self._refresh_profanity_ui()

    def _refresh_profanity_ui(self):
        words = sorted(self.profanity_words)
        self.profanity_listbox.delete(0, tk.END)
        for word in words:
            self.profanity_listbox.insert(tk.END, word)

        if words:
            self.profanity_listbox.selection_set(0)
            self.profanity_listbox.see(0)
            self.selected_profanity_word.set(words[0])
        else:
            self.selected_profanity_word.set("")

        self.profanity_count_label.configure(text=f"Profanity list: {len(self.profanity_words)} words")
        self._update_current_word_label()

    def _save_profanity_words(self):
        write_profanity_words(settings.profanity_file, self.profanity_words)

    def _on_profanity_select(self, _event=None):
        selection = self.profanity_listbox.curselection()
        if selection:
            self.selected_profanity_word.set(self.profanity_listbox.get(selection[0]))
        else:
            self.selected_profanity_word.set("")
        self._update_current_word_label()

    def _add_profanity_word(self, _event=None):
        raw_word = self.profanity_entry.get().strip().lower()
        if not raw_word:
            return

        if raw_word in self.profanity_words:
            messagebox.showinfo("Info", f"'{raw_word}' is already in the profanity list")
            return

        self.profanity_words.add(raw_word)
        self._save_profanity_words()
        self._refresh_profanity_ui()
        self.profanity_entry.delete(0, tk.END)
        self._set_filter_status("Filter: word added", self.palette["success"])

    def _remove_selected_profanity_word(self):
        selection = self.profanity_listbox.curselection()
        word = self.profanity_listbox.get(selection[0]).strip().lower() if selection else self.selected_profanity_word.get().strip().lower()
        if not word:
            messagebox.showinfo("Info", "No profanity word available to remove")
            return

        if word not in self.profanity_words:
            self._refresh_profanity_ui()
            return

        self.profanity_words.remove(word)
        self._save_profanity_words()
        self._refresh_profanity_ui()
        self._set_filter_status("Filter: word removed", self.palette["success"])

    @staticmethod
    def _fmt_time(seconds: float) -> str:
        minutes = int(seconds // 60)
        remaining_seconds = int(seconds % 60)
        return f"{minutes:02d}:{remaining_seconds:02d}"

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


if __name__ == "__main__":
    launch_video_player()
