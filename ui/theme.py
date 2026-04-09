"""Theme and styling mixin for the Tkinter video player."""


class ThemeMixin:
    """Adds dark/light palette setup and ttk styling methods."""

    def _setup_theme(self):
        self.style = self.style_cls()
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
        self.style.configure(
            "Review.Treeview",
            background=p["list_bg"],
            fieldbackground=p["list_bg"],
            foreground=p["text"],
            bordercolor=p["border"],
            rowheight=22,
            font=("Segoe UI", 9),
        )
        self.style.configure(
            "Review.Treeview.Heading",
            background=p["surface"],
            foreground=p["text"],
            relief="flat",
            font=("Segoe UI Semibold", 9),
        )
        self.style.map("Review.Treeview", background=[("selected", p["list_select"])], foreground=[("selected", "white")])

    def _apply_theme(self):
        p = self.palette
        self.root.configure(bg=p["bg"])

        for widget in (
            getattr(self, name, None)
            for name in (
                "container",
                "top_frame",
                "status_strip",
                "video_frame",
                "playback_section",
                "controls_frame",
                "bottom_frame",
                "settings_section",
                "profanity_card",
                "review_card",
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
                "review_summary_label",
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
        if hasattr(self, "video_frame"):
            self.video_frame.configure(bg=p["video_bg"])
        if hasattr(self, "profanity_entry"):
            try:
                self.profanity_entry.configure(highlightbackground=p["border"], highlightcolor=p["accent"])
            except Exception:
                pass
        if hasattr(self, "profanity_listbox"):
            self.profanity_listbox.configure(
                background=p["list_bg"],
                foreground=p["text"],
                selectbackground=p["list_select"],
                selectforeground="white",
                highlightbackground=p["border"],
                highlightcolor=p["accent"],
                relief="flat",
            )
        if hasattr(self, "timeline_marker_canvas"):
            self.timeline_marker_canvas.configure(bg=p["panel"])
            self._redraw_timeline_markers()
        self._render_empty_preview()

    def _on_theme_toggle(self):
        self._configure_styles()
        self._apply_theme()
