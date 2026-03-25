# from moviepy.video.io.VideoFileClip import VideoFileClip
import whisper
import re
from pydub import AudioSegment
# from moviepy.editor import VideoFileClip, AudioFileClip
from moviepy import VideoFileClip, AudioFileClip

# STEP 1 - Extract audio
video = VideoFileClip("videos/movie.mp4")
audio = video.audio
audio.write_audiofile("audio/audio.wav")


print("✅ Audio extracted successfully!")

# STEP 2 - Load Whisper model
model = whisper.load_model("base")

print("⏳ Converting speech to text...")

# STEP 3 - Convert speech to text
result = model.transcribe("audio/audio.wav")

print("✅ Speech converted to text")
print("\n--- TRANSCRIBED TEXT ---\n")
print(result["text"])


# STEP 4 - Detect bad words

# Load bad words
with open("profanity.txt", "r") as f:
    bad_words = [word.strip().lower() for word in f.readlines()]

# Get text
text = result["text"].lower()

# Find bad words
found_words = []

for word in bad_words:
    if word in text:
        found_words.append(word)

print("\n🚫 BAD WORDS DETECTED:")
print(found_words)


# STEP 5 - Detect bad words with timestamps
print("\n⏱️ BAD WORD TIMESTAMPS:")

bad_word_times = []

for segment in result["segments"]:
    segment_text = segment["text"].lower()
    start = segment["start"]
    end = segment["end"]

    for bad_word in bad_words:
        if bad_word in segment_text:
            bad_word_times.append((bad_word, start, end))
            print(f"{bad_word} → {start:.2f}s to {end:.2f}s")



# STEP 6 - Load audio
audio = AudioSegment.from_wav("audio/audio.wav")

# STEP 7 - Mute bad word segments
for word, start, end in bad_word_times:
    start_ms = int(start * 1000)
    end_ms = int(end * 1000)

    # Create silence for that segment
    silence = AudioSegment.silent(duration=(end_ms - start_ms))

    # Replace segment with silence
    audio = audio[:start_ms] + silence + audio[end_ms:]

print("🔇 Bad words muted")

# STEP 8 - Save clean audio
audio.export("audio/clean_audio.wav", format="wav")

print("✅ Clean audio saved")

print("✅ Clean audio saved as clean_audio.wav")

# Load original video (only once!)
video = VideoFileClip("videos/movie.mp4")

# Load the cleaned WAV as MoviePy AudioFileClip
clean_audio_clip = AudioFileClip("audio/clean_audio.wav")

# Attach clean audio → returns a NEW clip
final_video = video.with_audio(clean_audio_clip)

# Optional: make sure durations match (good safety)
if clean_audio_clip.duration < video.duration:
    print("Warning: clean audio is shorter than video → looping last frame or padding silence if needed")
    # You can add .with_duration(video.duration) or fx(vfx.loop) etc. if wanted

# Write the result
final_video.write_videofile(
    "videos/output_clean.mp4",
    codec="libx264",          # common safe choice
    audio_codec="aac",        # good for mp4
    fps=video.fps,            # keep original fps
    preset="medium",          # balance speed/quality
    threads=4                 # speed up if you have cores
)

print("🎬 Clean video created!")