"""End-to-end profanity removal pipeline orchestrator."""

from dataclasses import dataclass
from typing import Callable

from config.settings import Settings, settings
from processing.audio_cleaner import clean_audio
from processing.audio_extractor import extract_audio
from processing.profanity_filter import DetectionResult, ProfanityFilter
from processing.transcription import WhisperTranscriber
from processing.video_builder import build_clean_video
from utils.file_manager import build_processing_paths, ensure_directories

ProgressCallback = Callable[[int, str], None]


@dataclass(frozen=True)
class PipelineResult:
    """Result data returned by the processing pipeline."""

    output_video_path: str
    clean_audio_path: str
    extracted_audio_path: str
    detections: list[DetectionResult]


class ProfanityProcessingPipeline:
    """Coordinates extract -> transcribe -> detect -> clean -> rebuild."""

    def __init__(self, cfg: Settings = settings):
        self.cfg = cfg
        self.transcriber = WhisperTranscriber(model_name=cfg.whisper_model_name)
        self.filter = ProfanityFilter(profanity_file=cfg.profanity_file)

    def process_video(
        self,
        video_path: str,
        replacement_mode: str | None = None,
        intelligence_mode: str | None = None,
        detection_mode: str | None = None,
        language: str | None = None,
        on_progress: ProgressCallback | None = None,
    ) -> tuple[str, int]:
        ensure_directories([self.cfg.audio_dir, self.cfg.outputs_dir])

        audio_mode = replacement_mode or self.cfg.filter_mode
        detector_mode = intelligence_mode or detection_mode or self.cfg.filtering_mode

        paths = build_processing_paths(video_path, self.cfg)

        self._progress(on_progress, 10, "Extracting audio...")
        extract_audio(str(paths["source_video"]), str(paths["extracted_audio"]), sample_rate=16000)

        self._progress(on_progress, 35, "Transcribing audio...")
        transcription_result = self.transcriber.transcribe(str(paths["extracted_audio"]), language=language)

        self._progress(on_progress, 55, f"Detecting profanity ({detector_mode})...")
        detections, count = self.filter.detect(
            transcription_result,
            mode=detector_mode,
            use_ml_model=self.cfg.use_ml_model,
        )

        status = "Applying mute filter..." if audio_mode == "mute" else "Applying beep filter..."
        self._progress(on_progress, 70, status)
        clean_audio(
            source_audio_path=str(paths["extracted_audio"]),
            detections=detections,
            output_audio_path=str(paths["clean_audio"]),
            replacement_mode=audio_mode,
        )

        self._progress(on_progress, 85, "Rebuilding clean video...")
        build_clean_video(
            source_video_path=str(paths["source_video"]),
            clean_audio_path=str(paths["clean_audio"]),
            output_video_path=str(paths["output_video"]),
        )

        self._progress(on_progress, 100, "Completed")
        return str(paths["output_video"]), count

    @staticmethod
    def _progress(cb: ProgressCallback | None, percent: int, message: str) -> None:
        if cb:
            cb(percent, message)
