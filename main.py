"""Project entry point for CLI processing and desktop UI launch."""

import argparse

from processing.pipeline import ProfanityProcessingPipeline
from ui.main_window import launch_video_player


def run_cli(args: argparse.Namespace) -> None:
    """Process a video from command line using the modular pipeline."""
    
    pipeline = ProfanityProcessingPipeline()

    def progress(percent: int, message: str):
        print(f"[{percent:>3}%] {message}")

    # Handle language
    selected_language = None if args.language == "auto" else args.language

    try:
        output_path, count = pipeline.process_video(
            video_path=args.input,
            replacement_mode=args.replacement_mode,
            intelligence_mode=args.detection_mode,
            language=selected_language,
            on_progress=progress,
        )

        print("\n✅ Processing complete")
        print(f"🎬 Output video : {output_path}")
        print(f"🚨 Detections   : {count}")

    except Exception as e:
        print("\n❌ Error occurred during processing")
        print(str(e))


def build_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser."""
    
    parser = argparse.ArgumentParser(
        description="AI-based profanity detection and removal for videos"
    )

    parser.add_argument(
        "--gui",
        action="store_true",
        help="Launch Tkinter video player UI",
    )

    parser.add_argument(
        "--input",
        type=str,
        help="Path to input video file",
    )

    parser.add_argument(
        "--replacement-mode",
        choices=["mute", "beep"],
        default="mute",
        help="Replace profanity with silence or beep",
    )

    parser.add_argument(
        "--detection-mode",
        choices=["rule-based", "ai"],
        default="rule-based",
        help="Detection strategy (rule-based or AI)",
    )

    parser.add_argument(
        "--language",
        choices=["auto", "en", "si", "ta"],
        default="auto",
        help="Speech recognition language",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # If GUI requested OR no input → launch UI
    if args.gui or not args.input:
        launch_video_player()
        return

    # CLI mode
    run_cli(args)


if __name__ == "__main__":
    main()