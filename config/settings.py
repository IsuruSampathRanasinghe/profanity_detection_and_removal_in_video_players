"""Central configuration for profanity filtering and video processing."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    """Application-level settings used by UI and processing modules."""

    base_dir: Path = Path(__file__).resolve().parent.parent
    audio_dir: Path = base_dir / "audio"
    outputs_dir: Path = base_dir / "outputs"
    uploads_dir: Path = base_dir / "uploads"
    videos_dir: Path = base_dir / "videos"
    profanity_file: Path = base_dir / "profanity.txt"

    whisper_model_name: str = "base"
    filter_mode: str = "mute"  # mute | beep
    detection_mode: str = "rule-based"  # rule-based | ai


settings = Settings()
