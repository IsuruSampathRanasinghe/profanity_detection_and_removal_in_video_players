"""Audio replacement utilities for muting or beeping profane segments."""

import numpy as np
from pydub import AudioSegment

from processing.profanity_filter import DetectionResult


def generate_beep(duration_ms: int, frequency: int = 1000, sample_rate: int = 44100) -> AudioSegment:
    """Generate a sine-wave beep tone for censorship."""
    duration_sec = max(0, duration_ms) / 1000.0
    num_samples = int(sample_rate * duration_sec)
    if num_samples <= 0:
        return AudioSegment.silent(duration=0)

    t = np.linspace(0, duration_sec, num_samples, False)
    amplitude = 0.3
    wave = np.sin(2 * np.pi * frequency * t) * (32767 * amplitude)
    wave = wave.astype(np.int16)

    return AudioSegment(
        wave.tobytes(),
        frame_rate=sample_rate,
        sample_width=2,
        channels=1,
    )


def clean_audio(
    source_audio_path: str,
    detections: list[DetectionResult],
    output_audio_path: str,
    replacement_mode: str = "mute",
) -> int:
    """Replace detected ranges with silence or beeps and export cleaned audio."""
    audio = AudioSegment.from_wav(source_audio_path)

    for detection in detections:
        start_ms = max(0, int(detection.start * 1000))
        end_ms = max(start_ms, int(detection.end * 1000))
        duration_ms = end_ms - start_ms

        if replacement_mode == "beep":
            replacement = generate_beep(duration_ms)
        else:
            replacement = AudioSegment.silent(duration=duration_ms)

        audio = audio[:start_ms] + replacement + audio[end_ms:]

    audio.export(output_audio_path, format="wav")
    return len(detections)
