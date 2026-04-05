# Profanity Detection and Removal in Video Players

This project is a local Python application for detecting profanity in video audio and producing a cleaned version of the video. It uses Whisper for transcription, a word-list-based profanity filter by default, pydub for audio replacement, and MoviePy for rebuilding the final video.

## What It Does

- Loads a video file from disk
- Extracts the audio track
- Transcribes speech with Whisper
- Detects profanity with a configurable rule-based or future ML strategy
- Replaces profane segments with silence or a beep tone
- Rebuilds a cleaned output video
- Lets you preview original and cleaned videos in a Tkinter UI

## Current Architecture

The project is split into small modules with clear responsibilities:

- [main.py](main.py) is the entry point for CLI processing or launching the GUI
- [ui/main_window.py](ui/main_window.py) contains the Tkinter controller for the modular interface
- [processing/pipeline.py](processing/pipeline.py) coordinates the full workflow
- [processing/audio_extractor.py](processing/audio_extractor.py) handles audio extraction
- [processing/transcription.py](processing/transcription.py) wraps Whisper transcription
- [processing/profanity_filter.py](processing/profanity_filter.py) performs rule-based or AI-based profanity detection
- [processing/audio_cleaner.py](processing/audio_cleaner.py) mutates audio by mute or beep replacement
- [processing/video_builder.py](processing/video_builder.py) rebuilds the final video
- [utils/file_manager.py](utils/file_manager.py) handles file, path, and profanity-list helpers
- [config/settings.py](config/settings.py) stores shared configuration
- [models/ml_profanity_model.py](models/ml_profanity_model.py) is a placeholder for future ML-based detection

## Folder Structure

```text
.
├── config/
│   ├── __init__.py
│   └── settings.py
├── data/
│   └── profanity/
│       ├── en.txt              # English profanity words
│       ├── si.txt              # Sinhala profanity words
│       ├── ta.txt              # Tamil profanity words
│       └── fallback.txt         # Merged fallback list (auto-detect mode)
├── models/
│   ├── __init__.py
│   └── ml_profanity_model.py
├── processing/
│   ├── __init__.py
│   ├── audio_cleaner.py
│   ├── audio_extractor.py
│   ├── pipeline.py
│   ├── profanity_filter.py
│   ├── transcription.py
│   └── video_builder.py
├── ui/
│   ├── __init__.py
│   ├── main_window.py
│   ├── layout.py
│   ├── playback.py
│   ├── video_canvas.py
│   ├── audio_manager.py
│   ├── file_handler.py
│   ├── profanity_manager.py
│   ├── processing_ui.py
│   ├── theme.py
│   └── tooltip.py
├── utils/
│   ├── __init__.py
│   └── file_manager.py
├── audio/                       # Extracted audio files (runtime)
├── outputs/                     # Processed video output
├── inputs/                      # Input video storage
├── main.py
├── video_player.py              # Backward-compatible shim
├── requirements.txt
└── README.md
```

## Requirements

- Python 3.8 or higher
- FFmpeg installed and available on PATH
- Enough disk space for temporary audio and output video files

## Installation

Install FFmpeg first if it is not already available.

Windows with Chocolatey:

```bash
choco install ffmpeg
```

macOS:

```bash
brew install ffmpeg
```

Ubuntu or Debian:

```bash
sudo apt-get install ffmpeg
```

Install Python dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Launch the GUI

Run the Tkinter player and filtering UI:

```bash
python main.py --gui
```

You can also launch the same UI through the compatibility entry point:

```bash
python video_player.py
```

### Process a Video from the CLI

Run the pipeline directly on one file:

```bash
python main.py --input inputs/movie.mp4
```

Optional flags:

- `--replacement-mode mute|beep` controls how profane audio is replaced
- `--detection-mode rule-based|ai` selects the detection strategy
- `--language en|si|ta|...` passes a Whisper language code, or omit it for auto-detect

Example:

```bash
python main.py --input inputs/movie.mp4 --replacement-mode beep --language en
```

## How the Pipeline Works

1. `audio_extractor.py` extracts audio from the input video
2. `transcription.py` uses Whisper to generate transcript segments
3. `profanity_filter.py` scans the transcript for profanity matches
4. `audio_cleaner.py` replaces those ranges with silence or beep audio
5. `video_builder.py` attaches the cleaned audio to the source video
6. `pipeline.py` coordinates the full workflow and reports progress

## Configuration

Shared settings live in [config/settings.py](config/settings.py).

Key options include:

- Whisper model name
- Default filter mode: mute or beep
- Default detection mode: rule-based or ai
- Paths for audio, outputs, inputs, and language-specific profanity word lists

The profanity lists are stored in [data/profanity/](data/profanity/):
- `en.txt` for English
- `si.txt` for Sinhala
- `ta.txt` for Tamil
- `fallback.txt` for auto-detect mode (merged list)

Blank lines and lines starting with `#` are ignored.

## Extensibility

The project is structured so you can extend it without touching the UI:

- Replace or extend the rule-based detector in [processing/profanity_filter.py](processing/profanity_filter.py)
- Implement ML logic in [models/ml_profanity_model.py](models/ml_profanity_model.py)
- Add new audio replacement strategies in [processing/audio_cleaner.py](processing/audio_cleaner.py)
- Add new pipeline steps in [processing/pipeline.py](processing/pipeline.py)

## Technical Stack

- Whisper for speech-to-text transcription
- MoviePy for video/audio reading and rebuilding
- pydub for segment-level audio editing
- OpenCV for frame decoding and playback in the UI
- pygame for audio preview playback
- Pillow for rendering frames in Tkinter
- Tkinter for the desktop interface

## Notes

- The project is now organized as a local desktop application plus processing pipeline, not a Flask web app
- Temporary audio files are written under [audio](audio)
- Clean videos are written under [outputs](outputs)

## License

This project is open source and available under the MIT License.