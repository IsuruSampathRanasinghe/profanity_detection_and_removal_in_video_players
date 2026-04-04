"""Video reconstruction by attaching cleaned audio to source video."""

from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.io.VideoFileClip import VideoFileClip


def build_clean_video(source_video_path: str, clean_audio_path: str, output_video_path: str) -> None:
    """Attach cleaned audio track and write final MP4 video."""
    video_clip = None
    clean_audio_clip = None
    final_video = None
    try:
        video_clip = VideoFileClip(source_video_path)
        clean_audio_clip = AudioFileClip(clean_audio_path)

        if hasattr(video_clip, "with_audio"):
            final_video = video_clip.with_audio(clean_audio_clip)
        else:
            final_video = video_clip.set_audio(clean_audio_clip)

        final_video.write_videofile(
            output_video_path,
            codec="libx264",
            audio_codec="aac",
            fps=video_clip.fps,
            logger=None,
        )
    finally:
        if final_video is not None:
            final_video.close()
        if clean_audio_clip is not None:
            clean_audio_clip.close()
        if video_clip is not None:
            video_clip.close()
