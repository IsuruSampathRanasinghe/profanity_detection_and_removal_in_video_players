"""Audio extraction helpers for full processing and preview playback."""

from moviepy.video.io.VideoFileClip import VideoFileClip


def extract_audio(video_path: str, output_audio_path: str, sample_rate: int = 16000) -> None:
    """Extract mono WAV audio from a video file."""
    clip = None
    try:
        clip = VideoFileClip(video_path)
        if clip.audio is None:
            raise ValueError("Selected video has no audio track")
        clip.audio.write_audiofile(
            output_audio_path,
            codec="pcm_s16le",
            fps=sample_rate,
            logger=None,
        )
    finally:
        if clip is not None:
            clip.close()
