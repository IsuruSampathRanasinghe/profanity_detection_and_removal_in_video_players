"""Project entry point for CLI processing and desktop UI launch."""

import argparse

from processing.pipeline import ProfanityProcessingPipeline
from ui.video_player import launch_video_player


def run_cli(args: argparse.Namespace) -> None:
    """Process a video from command line using the modular pipeline."""
    pipeline = ProfanityProcessingPipeline()

    def progress(percent: int, message: str):
        print(f"[{percent:>3}%] {message}")

    result = pipeline.process_video(
        video_path=args.input,
        replacement_mode=args.replacement_mode,
        detection_mode=args.detection_mode,
        language=args.language,
        on_progress=progress,
    )

    print("\nProcessing complete")
    print(f"Output video : {result.output_video_path}")
    print(f"Clean audio  : {result.clean_audio_path}")
    print(f"Detections   : {len(result.detections)}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Profanity detection and removal for videos")
    parser.add_argument("--gui", action="store_true", help="Launch Tkinter video player")
    parser.add_argument("--input", type=str, help="Input video path for CLI processing")
    parser.add_argument(
        "--replacement-mode",
        choices=["mute", "beep"],
        default="mute",
        help="Audio replacement mode for detected profanity",
    )
    parser.add_argument(
        "--detection-mode",
        choices=["rule-based", "ai"],
        default="rule-based",
        help="Profanity detection strategy",
    )
    parser.add_argument(
        "--language",
        type=str,
        default=None,
        help="Whisper language code (e.g. en, si, ta). Leave empty for auto-detect.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.gui or not args.input:
        launch_video_player()
        return

    run_cli(args)


if __name__ == "__main__":
    main()
