"""Central configuration for profanity filtering and video processing."""

from dataclasses import dataclass
from pathlib import Path


# Intelligence mode defaults.
FILTER_MODE = "kids"  # kids | adult | custom
USE_ML_MODEL = False


@dataclass(frozen=True)
class Settings:
    """Application-level settings used by UI and processing modules."""

    base_dir: Path = Path(__file__).resolve().parent.parent
    audio_dir: Path = base_dir / "audio"
    outputs_dir: Path = base_dir / "outputs"
    uploads_dir: Path = base_dir / "uploads"
    videos_dir: Path = base_dir / "videos"
    profanity_file: Path = base_dir / "profanity.txt"
    profanity_en_file: Path = base_dir / "profanity_en.txt"
    profanity_si_file: Path = base_dir / "profanity_si.txt"
    profanity_ta_file: Path = base_dir / "profanity_ta.txt"

    whisper_model_name: str = "base"
    filter_mode: str = "mute"  # mute | beep (audio replacement)
    filtering_mode: str = FILTER_MODE  # kids | adult | custom
    use_ml_model: bool = USE_ML_MODEL
    detection_mode: str = "rule-based"  # rule-based | ai


settings = Settings()
