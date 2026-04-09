"""Central configuration for profanity filtering and video processing."""

from dataclasses import dataclass, field
from pathlib import Path


# =========================
# DEFAULT MODES
# =========================
DEFAULT_FILTERING_MODE = "kids"   # kids | adult | custom
DEFAULT_REPLACEMENT_MODE = "mute" # mute | beep
DEFAULT_DETECTION_MODE = "ai"     # rule-based | ai
DEFAULT_USE_ML = True


# =========================
# SETTINGS CLASS
# =========================
@dataclass(frozen=True)
class Settings:
    """Application-level settings used by UI and processing modules."""

    # Base directory
    base_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent)

    # Directories
    audio_dir: Path = field(init=False)
    outputs_dir: Path = field(init=False)
    inputs_dir: Path = field(init=False)
    data_dir: Path = field(init=False)
    profanity_dir: Path = field(init=False)

    # Profanity files
    profanity_file: Path = field(init=False)
    profanity_en_file: Path = field(init=False)
    profanity_si_file: Path = field(init=False)
    profanity_ta_file: Path = field(init=False)

    # Model & processing settings
    whisper_model_name: str = "small"
    replacement_mode: str = DEFAULT_REPLACEMENT_MODE
    filtering_mode: str = DEFAULT_FILTERING_MODE
    detection_mode: str = DEFAULT_DETECTION_MODE
    use_ml_model: bool = DEFAULT_USE_ML

    def __post_init__(self):
        base = self.base_dir

        object.__setattr__(self, "audio_dir", base / "audio")
        object.__setattr__(self, "outputs_dir", base / "outputs")
        object.__setattr__(self, "inputs_dir", base / "inputs")
        object.__setattr__(self, "data_dir", base / "data")
        object.__setattr__(self, "profanity_dir", base / "data" / "profanity")

        object.__setattr__(self, "profanity_file", base / "data" / "profanity" / "fallback.txt")
        object.__setattr__(self, "profanity_en_file", base / "data" / "profanity" / "en.txt")
        object.__setattr__(self, "profanity_si_file", base / "data" / "profanity" / "si.txt")
        object.__setattr__(self, "profanity_ta_file", base / "data" / "profanity" / "ta.txt")

        self._validate()

    # =========================
    # VALIDATION
    # =========================
    def _validate(self):
        valid_filter_modes = {"kids", "adult", "custom"}
        valid_replacement_modes = {"mute", "beep"}
        valid_detection_modes = {"rule-based", "ai"}

        if self.filtering_mode not in valid_filter_modes:
            raise ValueError(f"Invalid filtering_mode: {self.filtering_mode}")

        if self.replacement_mode not in valid_replacement_modes:
            raise ValueError(f"Invalid replacement_mode: {self.replacement_mode}")

        if self.detection_mode not in valid_detection_modes:
            raise ValueError(f"Invalid detection_mode: {self.detection_mode}")


# Singleton instance
settings = Settings()