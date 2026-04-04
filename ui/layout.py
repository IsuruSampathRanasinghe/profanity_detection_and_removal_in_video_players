"""Layout builder mixin for constructing the Tkinter player interface."""

from tkinter import ttk

from ui.tooltip import Tooltip


class LayoutMixin:
    """Builds top bar, video canvas area, playback controls, and side panel."""

    def _create_button(self, parent, text=None, command=None, style_name="App.TButton", textvariable=None):
        kwargs = {"command": command, "style": style_name}
        if textvariable is not None:
            kwargs["textvariable"] = textvariable
        else:
            kwargs["text"] = text
        return ttk.Button(parent, **kwargs)

    def _toggle_fullscreen(self):
        self.is_fullscreen = not self.is_fullscreen
        self.root.attributes("-fullscreen", self.is_fullscreen)

    def _toggle_bottom_panel(self):
        if self.bottom_panel_visible:
            self.bottom_frame.grid_remove()
            self.container.columnconfigure(1, weight=0)
            self.bottom_toggle_text.set("Show Side Panel")
        else:
            self.bottom_frame.grid()
            self.container.columnconfigure(1, weight=2)
            self.bottom_toggle_text.set("Hide Side Panel")
        self.bottom_panel_visible = not self.bottom_panel_visible

    def _build_slider_card(self, parent, column, title, command, initial_value, value_text_var):
        card = ttk.Frame(parent, style="Panel.TFrame", padding=(4, 0))
        card.grid(row=0, column=column, sticky="ew", padx=(0 if column == 0 else 12, 0))
        card.columnconfigure(0, weight=1)

        ttk.Label(card, text=title, style="SectionLabel.TLabel").grid(row=0, column=0, sticky="w")
        scale = ttk.Scale(card, from_=0 if title == "Volume" else 50, to=100 if title == "Volume" else 150, orient=self.tk.HORIZONTAL, command=command)
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

    def _build_ui(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        self.container = ttk.Frame(self.root, style="App.TFrame", padding=(14, 12, 14, 12))
        self.container.grid(row=0, column=0, sticky="nsew")
        self.container.columnconfigure(0, weight=4)
        self.container.columnconfigure(1, weight=2)
        self.container.rowconfigure(0, weight=0)
        self.container.rowconfigure(1, weight=4)
        self.container.rowconfigure(2, weight=1)

        self.top_frame = ttk.Frame(self.container, style="App.TFrame")
        self.top_frame.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        self.top_frame.columnconfigure(4, weight=1)
        self.top_frame.columnconfigure(0, weight=0)

        self._create_button(self.top_frame, "Load Video", self.open_video, "Primary.TButton").grid(row=0, column=0, sticky="w", padx=(0, 8))
        self._create_button(self.top_frame, "Filter Profanity", self.filter_profanity, "Accent.TButton").grid(row=0, column=1, sticky="w", padx=(0, 8))
        ttk.Checkbutton(self.top_frame, text="Dark mode", variable=self.dark_mode, command=self._on_theme_toggle, style="TCheckbutton").grid(row=0, column=2, sticky="w", padx=(0, 8))
        self._create_button(self.top_frame, "Fullscreen", self._toggle_fullscreen, "Compact.TButton").grid(row=0, column=3, sticky="w", padx=(0, 8))

        language_row = ttk.Frame(self.top_frame, style="Panel.TFrame")
        language_row.grid(row=0, column=4, sticky="e", padx=(0, 8))
        ttk.Label(language_row, text="Language", style="SectionLabel.TLabel").pack(side=self.tk.LEFT, padx=(0, 6))
        self.language_combo = ttk.Combobox(
            language_row,
            textvariable=self.language_code,
            values=("auto", "en", "si", "ta"),
            width=7,
            state="readonly",
        )
        self.language_combo.pack(side=self.tk.LEFT)

        self._create_button(self.top_frame, textvariable=self.bottom_toggle_text, command=self._toggle_bottom_panel, style_name="Compact.TButton").grid(row=0, column=5, sticky="e")
        self.bottom_toggle_text.set("Hide Side Panel")

        self.status_strip = ttk.Frame(self.top_frame, style="Panel.TFrame", padding=(8, 6, 8, 6))
        self.status_strip.grid(row=1, column=0, columnspan=6, sticky="ew", pady=(8, 0))
        status_row = ttk.Frame(self.status_strip, style="Panel.TFrame")
        status_row.pack(fill=self.tk.X)
        self.current_video_label = ttk.Label(status_row, textvariable=self.current_video_label_text, style="Status.TLabel")
        self.current_video_label.pack(side=self.tk.LEFT, padx=(0, 16))
        self.audio_status_label = ttk.Label(status_row, textvariable=self.audio_status_text, style="Status.TLabel")
        self.audio_status_label.pack(side=self.tk.LEFT, padx=(0, 16))
        self.filter_status_label = ttk.Label(status_row, textvariable=self.filter_status_text, style="Status.TLabel")
        self.filter_status_label.pack(side=self.tk.LEFT)

        self.video_frame = self.tk.Frame(self.container, bg="black", bd=0, highlightthickness=0)
        self.video_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        self.canvas = self.tk.Canvas(self.video_frame, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self._on_resize)

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
        self.progress_scale = ttk.Scale(self.playback_section, from_=0, to=100, orient=self.tk.HORIZONTAL, command=self._on_seek)
        self.progress_scale.grid(row=0, column=3, sticky="ew", padx=(0, 10))
        self.progress_scale.bind("<ButtonPress-1>", self._on_timeline_press)
        self.progress_scale.bind("<ButtonRelease-1>", self._on_timeline_release)
        self._create_button(self.playback_section, "-5s", self.skip_backward, "Compact.TButton").grid(row=0, column=4, sticky="e", padx=(0, 6))
        self._create_button(self.playback_section, "+5s", self.skip_forward, "Compact.TButton").grid(row=0, column=5, sticky="e", padx=(0, 6))
        self._create_button(self.playback_section, "Stop", self.stop_video, "Danger.TButton").grid(row=0, column=6, sticky="e", padx=(0, 8))
        self.time_label = ttk.Label(self.playback_section, text="00:00 / 00:00", style="Title.TLabel")
        self.time_label.grid(row=0, column=7, sticky="e")

        self.bottom_frame = ttk.Frame(self.container, style="App.TFrame")
        self.bottom_frame.grid(row=1, column=1, rowspan=2, sticky="nsew", padx=(10, 0))
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
        ttk.Label(filter_card, text="Replacement", style="SectionLabel.TLabel").grid(row=0, column=0, sticky="w")

        mute_radio = ttk.Radiobutton(filter_card, text="Mute", variable=self.filter_mode, value="mute", style="Toggle.TRadiobutton")
        mute_radio.grid(row=1, column=0, sticky="w", pady=(6, 2))
        Tooltip(mute_radio, "Silent replacement: Detected profanity segments are muted (silent).")

        beep_radio = ttk.Radiobutton(filter_card, text="Beep", variable=self.filter_mode, value="beep", style="Toggle.TRadiobutton")
        beep_radio.grid(row=2, column=0, sticky="w")
        Tooltip(beep_radio, "Beep replacement: Detected profanity segments are replaced with a beep sound.")

        ttk.Separator(filter_card, orient=self.tk.HORIZONTAL).grid(row=3, column=0, sticky="ew", pady=(8, 8))
        ttk.Label(filter_card, text="Intelligence Mode", style="SectionLabel.TLabel").grid(row=4, column=0, sticky="w")

        kids_radio = ttk.Radiobutton(filter_card, text="Kids (strict)", variable=self.intelligence_mode, value="kids", style="Toggle.TRadiobutton")
        kids_radio.grid(row=5, column=0, sticky="w", pady=(6, 2))
        Tooltip(kids_radio, "Strict mode: Filters all profanity words, masked patterns (f***, sh!t), and optional AI detection. Best for children.")

        adult_radio = ttk.Radiobutton(filter_card, text="Adult (moderate)", variable=self.intelligence_mode, value="adult", style="Toggle.TRadiobutton")
        adult_radio.grid(row=6, column=0, sticky="w", pady=(0, 2))
        Tooltip(adult_radio, "Moderate mode: Filters only strong profanity words. Allows mild language. Suitable for general audiences.")

        custom_radio = ttk.Radiobutton(filter_card, text="Custom (word list)", variable=self.intelligence_mode, value="custom", style="Toggle.TRadiobutton")
        custom_radio.grid(row=7, column=0, sticky="w")
        Tooltip(custom_radio, "Custom mode: Filters only words in your custom profanity list below. Full user control.")

        self.intelligence_mode_description_label = ttk.Label(
            filter_card,
            textvariable=self.intelligence_mode_description_text,
            style="Small.TLabel",
            wraplength=220,
            justify=self.tk.LEFT,
        )
        self.intelligence_mode_description_label.grid(row=8, column=0, sticky="w", pady=(8, 0))

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

        self.profanity_listbox = self.tk.Listbox(list_frame, exportselection=False, activestyle="none", selectmode=self.tk.SINGLE, height=5)
        self.profanity_listbox.grid(row=0, column=0, sticky="nsew")
        self.profanity_listbox.bind("<<ListboxSelect>>", self._on_profanity_select)
        self.profanity_listbox.bind("<Delete>", lambda _event: self._remove_selected_profanity_word())

        list_scrollbar = ttk.Scrollbar(list_frame, orient=self.tk.VERTICAL, command=self.profanity_listbox.yview)
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
        self.processing_bar = ttk.Progressbar(progress_row, orient=self.tk.HORIZONTAL, mode="determinate", maximum=100, variable=self.processing_progress, style="App.Horizontal.TProgressbar")
        self.processing_bar.grid(row=0, column=0, sticky="ew")
        self.processing_pct_label = ttk.Label(progress_row, textvariable=self.processing_pct_text, style="Title.TLabel")
        self.processing_pct_label.grid(row=0, column=1, sticky="e", padx=(12, 0))
