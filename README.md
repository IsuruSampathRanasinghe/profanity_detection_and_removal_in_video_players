# Profanity Detection & Removal in Video Players

A web-based application that automatically detects and removes profanity from videos.

## Features

- 🎬 **Video Upload**: Upload video files (MP4, AVI, MOV, MKV, FLV)
- 🔍 **Profanity Detection**: Uses OpenAI's Whisper for speech-to-text transcription
- 🔇 **Auto-Muting**: Automatically mutes profane words in the audio
- 🎥 **Video Playback**: Built-in player to preview videos
- 📊 **Real-time Progress**: Monitor processing status with live progress updates
- 💾 **Video Management**: View uploaded and processed videos

## Requirements

- Python 3.8 or higher
- FFmpeg (required by moviepy)
- 500MB+ free disk space for processing videos

## Installation

### 1. Install FFmpeg

**Windows (using Chocolatey):**
```bash
choco install ffmpeg
```

**Windows (manual):**
Download from https://ffmpeg.org/download.html and add to PATH

**macOS:**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install ffmpeg
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Option 1: Run with Web UI (Recommended)

Start the Flask application:

```bash
python app.py
```

Then open your browser to: **http://localhost:5000**

Features:
- Select or upload a video
- Click "Start Processing" to remove profanity
- Watch real-time progress
- Download the cleaned video

### Option 2: Custom Built-in Video Player (NEW!)

Run the advanced custom video player:

```bash
python custom_video_player.py
```

**Features:**
- ✨ Native video playback within the application
- ▶️ Full playback controls (play, pause, stop)
- ⏱️ Seek/timeline with frame-precise control
- 🎬 Real-time video display with frame updating
- ⚡ Adjustable playback speed (0.25x - 2.0x)
- 📊 Video information display (resolution, FPS, duration)
- 🎨 Modern dark-themed UI
- 📁 Support for MP4, AVI, MOV, MKV, FLV, WMV, WebM formats

**Technology:**
- Uses OpenCV for fast video processing (primary)
- Falls back to MoviePy if OpenCV unavailable
- Pillow for image display in GUI

### Option 3: GUI Video Player (Legacy)

Run the legacy video player:

```bash
python video_player_gui.py
```

Features:
- Open video files with file browser
- Support for MP4, AVI, MOV, MKV, FLV, WMV formats
- Two modes: System player or integrated (with moviepy/Pillow)

### Option 4: Run Core Script Directly

For command-line processing:

```bash
python main.py
```

This requires editing `main.py` to specify the video path.

## Project Structure

```
.
├── app.py                      # Flask web application
├── main.py                     # Core processing script
├── video_player_gui.py         # GUI video player
├── profanity.txt              # List of bad words
├── requirements.txt           # Python dependencies
├── frontend/
│   ├── templates/
│   │   └── index.html         # Web interface
│   └── static/
│       ├── style.css          # Styling
│       └── script.js          # Client-side logic
├── videos/                    # Input video storage
├── uploads/                   # User uploaded videos
├── outputs/                   # Processed videos
└── audio/                     # Temporary audio files
```

## How It Works

1. **Audio Extraction**: Extracts audio from the selected video
2. **Speech Recognition**: Converts speech to text using Whisper
3. **Bad Word Detection**: Scans transcribed text for profanity
4. **Audio Muting**: Replaces profane segments with silence
5. **Video Reconstruction**: Creates new video with cleaned audio

## Configuration

Edit `profanity.txt` to customize the list of words to detect. One word per line.

## Troubleshooting

### FFmpeg Not Found
- Ensure FFmpeg is installed and added to your system PATH
- Restart your terminal after installation

### Processing Slow
- Initial Whisper model download takes time
- Adjust `preset` in `app.py` (fast, medium, slow) for quality vs speed tradeoff
- Use smaller videos for testing

### Audio Sync Issues
- Ensure original video has intact audio stream
- Try with different video formats

## Technical Details

- **Speech Recognition**: OpenAI Whisper (base model)
- **Video Processing**: MoviePy with libx264 codec
- **Audio Processing**: pydub
- **Web Framework**: Flask
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **GUI Framework**: Tkinter (uses system video player)
- **File Upload**: Max 500MB

## License

This project is open source and available under the MIT License.