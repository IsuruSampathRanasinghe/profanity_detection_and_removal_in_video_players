"""Audio replacement utilities for muting or beeping profane segments."""

import numpy as np
from pydub import AudioSegment
from processing.profanity_filter import DetectionResult


# =========================
# BEEP GENERATOR
# =========================
def generate_beep(
    duration_ms: int,
    frequency: int = 1000,
    sample_rate: int = 44100
) -> AudioSegment:
    """Generate a sine-wave beep tone."""
    
    duration_sec = max(0, duration_ms) / 1000.0
    num_samples = int(sample_rate * duration_sec)

    if num_samples <= 0:
        return AudioSegment.silent(duration=0)

    t = np.linspace(0, duration_sec, num_samples, False)
    wave = np.sin(2 * np.pi * frequency * t) * 32767 * 0.3
    wave = wave.astype(np.int16)

    return AudioSegment(
        wave.tobytes(),
        frame_rate=sample_rate,
        sample_width=2,
        channels=1,
    )


# =========================
# MERGE OVERLAPPING RANGES
# =========================
def merge_ranges(ranges: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Merge overlapping time ranges."""
    
    if not ranges:
        return []

    ranges = sorted(ranges)
    merged = [ranges[0]]

    for current in ranges[1:]:
        prev_start, prev_end = merged[-1]
        curr_start, curr_end = current

        if curr_start <= prev_end:
            merged[-1] = (prev_start, max(prev_end, curr_end))
        else:
            merged.append(current)

    return merged


# =========================
# CLEAN AUDIO (OPTIMIZED)
# =========================
def clean_audio(
    source_audio_path: str,
    detections: list[DetectionResult],
    output_audio_path: str,
    replacement_mode: str = "mute",
) -> int:
    """
    Replace detected ranges with silence or beep.
    Optimized for performance + correct timing.
    """

    audio = AudioSegment.from_wav(source_audio_path)

    # Convert detections → ms ranges
    ranges = [
        (
            max(0, int(d.start * 1000)),
            max(0, int(d.end * 1000)),
        )
        for d in detections
    ]

    # Merge overlaps
    ranges = merge_ranges(ranges)

    # Build output efficiently
    output_audio = AudioSegment.empty()
    last_end = 0

    for start, end in ranges:
        start = max(0, start)
        end = max(start, end)

        # Keep original audio before bad word
        output_audio += audio[last_end:start]

        duration = end - start

        # Insert replacement
        if replacement_mode == "beep":
            replacement = generate_beep(duration)
        else:
            replacement = AudioSegment.silent(duration=duration)

        output_audio += replacement
        last_end = end

    # Add remaining audio
    output_audio += audio[last_end:]

    # Export
    output_audio.export(output_audio_path, format="wav")

    return len(ranges)