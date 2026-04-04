"""File and path helpers used across the project."""

from pathlib import Path
from typing import Iterable, Set

from config.settings import Settings


def ensure_directories(paths: Iterable[Path]) -> None:
    """Create directories if they do not already exist."""
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)


def build_processing_paths(video_path: str, cfg: Settings) -> dict[str, Path]:
    """Build deterministic file paths for intermediate and output artifacts."""
    source = Path(video_path)
    stem = source.stem
    return {
        "source_video": source,
        "extracted_audio": cfg.audio_dir / f"{stem}_source.wav",
        "clean_audio": cfg.audio_dir / f"{stem}_clean.wav",
        "output_video": cfg.outputs_dir / f"{stem}_clean.mp4",
    }


def read_profanity_words(file_path: Path) -> Set[str]:
    """Load profanity words from file while ignoring comments and empty lines."""
    if not file_path.exists():
        file_path.touch()
        return set()

    words = set()
    for raw_line in file_path.read_text(encoding="utf-8").splitlines():
        word = raw_line.strip().lower()
        if not word or word.startswith("#"):
            continue
        words.add(word)
    return words


def write_profanity_words(file_path: Path, words: Set[str]) -> None:
    """Persist profanity words as a sorted text file."""
    sorted_words = sorted({word.strip().lower() for word in words if word.strip()})
    content = "\n".join(sorted_words)
    if content:
        content += "\n"
    file_path.write_text(content, encoding="utf-8")


def safe_delete(path: Path) -> None:
    """Best-effort file deletion."""
    try:
        if path.exists():
            path.unlink()
    except OSError:
        pass
