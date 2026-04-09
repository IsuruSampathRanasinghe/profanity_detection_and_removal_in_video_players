"""Video reconstruction by attaching cleaned audio to source video."""

from moviepy.editor import VideoFileClip, AudioFileClip


def build_clean_video(source_video_path: str, clean_audio_path: str, output_video_path: str) -> None:
    """
    Attach cleaned audio track to the original video and export the final MP4.
    
    Args:
        source_video_path: Path to the original video.
        clean_audio_path: Path to the cleaned audio (wav/mp3).
        output_video_path: Path to save the output video.
    """
    video_clip = None
    clean_audio_clip = None
    final_video = None

    try:
        # Load video and audio
        video_clip = VideoFileClip(source_video_path)
        clean_audio_clip = AudioFileClip(clean_audio_path)

        # Attach audio to video
        final_video = video_clip.set_audio(clean_audio_clip)

        # Write the output video
        final_video.write_videofile(
            output_video_path,
            codec="libx264",
            audio_codec="aac",
            fps=video_clip.fps,
            preset="ultrafast",
            threads=4,
            logger=None
        )

    finally:
        # Safely close all clips
        if final_video:
            final_video.close()
        if clean_audio_clip:
            clean_audio_clip.close()
        if video_clip:
            video_clip.close()