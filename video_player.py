import os
import time
import threading
import tkinter as tk
from tkinter import filedialog, messagebox

import cv2
import pygame
import whisper
from PIL import Image, ImageTk
from pydub import AudioSegment

from moviepy import AudioFileClip, VideoFileClip


class VideoPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Player")
        self.root.geometry("960x640")
        self.root.resizable(True, True)

        self.mixer_ready = True
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2)
        except Exception as exc:
            print(f"Audio mixer init failed: {exc}")
            self.mixer_ready = False

        self.cap = None
        self.current_video_path = None
        self.original_video_path = None
        self.clean_video_path = None
        self.audio_path = None
        self.generated_audio_paths = set()
        self.filtering_in_progress = False
        self.whisper_model = None
        self.profanity_words = set()

        self.is_playing = False
        self.current_frame = 0
        self.total_frames = 0
        self.fps = 25.0

        self.playback_start_time = 0.0
        self.playback_start_frame = 0
        self.volume = 1.0

        self._build_ui()

    def _build_ui(self):
        controls = tk.Frame(self.root)
        controls.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        tk.Button(
            controls,
            text="Load Video",
            command=self.open_video,
            bg="#2e7d32",
            fg="white",
            padx=12,
            pady=6,
        ).pack(side=tk.LEFT, padx=4)

        tk.Button(
            controls,
            text="Filter Profanity",
            command=self.filter_profanity,
            bg="#6a1b9a",
            fg="white",
            padx=12,
            pady=6,
        ).pack(side=tk.LEFT, padx=4)

        tk.Button(
            controls,
            text="Play Original",
            command=self.play_original_video,
            bg="#1565c0",
            fg="white",
            padx=12,
            pady=6,
        ).pack(side=tk.LEFT, padx=4)

        tk.Button(
            controls,
            text="Play Clean",
            command=self.play_clean_video,
            bg="#00838f",
            fg="white",
            padx=12,
            pady=6,
        ).pack(side=tk.LEFT, padx=4)

        tk.Button(
            controls,
            text="Pause",
            command=self.pause_video,
            bg="#ef6c00",
            fg="white",
            padx=12,
            pady=6,
        ).pack(side=tk.LEFT, padx=4)

        tk.Button(
            controls,
            text="Stop",
            command=self.stop_video,
            bg="#c62828",
            fg="white",
            padx=12,
            pady=6,
        ).pack(side=tk.LEFT, padx=4)

        self.video_label = tk.Label(controls, text="No video loaded", fg="#666")
        self.video_label.pack(side=tk.LEFT, padx=16)

        self.filter_status_label = tk.Label(controls, text="Filter: idle", fg="#666")
        self.filter_status_label.pack(side=tk.LEFT, padx=8)

        self.volume_label = tk.Label(controls, text="Volume")
        self.volume_label.pack(side=tk.RIGHT, padx=(12, 4))

        self.volume_scale = tk.Scale(
            controls,
            from_=0,
            to=100,
            orient=tk.HORIZONTAL,
            command=self._on_volume_change,
            showvalue=True,
            length=120,
        )
        self.volume_scale.set(100)
        self.volume_scale.pack(side=tk.RIGHT, padx=4)

        self.audio_status_label = tk.Label(controls, text="Audio: idle", fg="#666")
        self.audio_status_label.pack(side=tk.RIGHT, padx=8)

        self.canvas = tk.Canvas(self.root, bg="black")
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.canvas.bind("<Configure>", self._on_resize)

        progress_wrap = tk.Frame(self.root)
        progress_wrap.pack(fill=tk.X, padx=10, pady=6)

        self.progress_scale = tk.Scale(
            progress_wrap,
            from_=0,
            to=100,
            orient=tk.HORIZONTAL,
            command=self._on_seek,
            showvalue=False,
        )
        self.progress_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.time_label = tk.Label(progress_wrap, text="00:00 / 00:00", width=16)
        self.time_label.pack(side=tk.RIGHT, padx=8)

        profanity_wrap = tk.Frame(self.root)
        profanity_wrap.pack(fill=tk.X, padx=10, pady=(0, 8))

        tk.Label(profanity_wrap, text="Add Profanity Word:").pack(side=tk.LEFT, padx=(0, 6))

        self.profanity_entry = tk.Entry(profanity_wrap, width=24)
        self.profanity_entry.pack(side=tk.LEFT, padx=4)
        self.profanity_entry.bind("<Return>", self._add_profanity_word)

        tk.Button(
            profanity_wrap,
            text="Add",
            command=self._add_profanity_word,
            bg="#5d4037",
            fg="white",
            padx=10,
            pady=3,
        ).pack(side=tk.LEFT, padx=4)

        self.selected_profanity_word = tk.StringVar(value="")
        self.profanity_dropdown = tk.OptionMenu(profanity_wrap, self.selected_profanity_word, "")
        self.profanity_dropdown.config(width=18)
        self.profanity_dropdown.pack(side=tk.LEFT, padx=4)

        tk.Button(
            profanity_wrap,
            text="Remove",
            command=self._remove_selected_profanity_word,
            bg="#8e24aa",
            fg="white",
            padx=10,
            pady=3,
        ).pack(side=tk.LEFT, padx=4)

        self.profanity_count_label = tk.Label(profanity_wrap, text="Profanity list: 0 words", fg="#666")
        self.profanity_count_label.pack(side=tk.LEFT, padx=10)

        self._load_profanity_words()

    def open_video(self):
        file_path = filedialog.askopenfilename(
            title="Select a video file",
            filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv *.flv"), ("All files", "*.*")],
            initialdir="videos",
        )
        if not file_path:
            return

        self.original_video_path = file_path
        self.clean_video_path = None
        self._set_filter_status("Filter: ready", "#2e7d32")
        self._load_video_source(file_path, source_name="Original")

    def _load_video_source(self, file_path, source_name="Video"):
        self.stop_video(reset_frame=False)

        if self.cap:
            self.cap.release()
            self.cap = None

        self.cap = cv2.VideoCapture(file_path)
        if not self.cap.isOpened():
            messagebox.showerror("Error", "Cannot open video file")
            self.cap = None
            return False

        self.current_video_path = file_path
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        detected_fps = float(self.cap.get(cv2.CAP_PROP_FPS) or 0)
        self.fps = detected_fps if detected_fps > 1 else 25.0
        self.current_frame = 0

        self.video_label.config(text=f"{source_name}: {os.path.basename(file_path)}")
        self.progress_scale.config(to=max(1, self.total_frames - 1))

        self._extract_audio(file_path)
        self._seek_and_show(0)
        return True

    def filter_profanity(self):
        if not self.original_video_path:
            messagebox.showwarning("Warning", "Load a video first")
            return

        if self.filtering_in_progress:
            return

        self.filtering_in_progress = True
        self._set_filter_status("Filter: processing...", "#ef6c00")

        worker = threading.Thread(target=self._filter_profanity_worker, daemon=True)
        worker.start()

    def _filter_profanity_worker(self):
        input_video = self.original_video_path
        base_name = os.path.splitext(os.path.basename(input_video))[0]

        os.makedirs("audio", exist_ok=True)
        os.makedirs("outputs", exist_ok=True)

        extracted_audio_path = os.path.join("audio", f"{base_name}_source.wav")
        clean_audio_path = os.path.join("audio", f"{base_name}_clean.wav")
        clean_video_path = os.path.join("outputs", f"{base_name}_clean.mp4")

        video_clip = None
        clean_audio_clip = None
        try:
            self._set_filter_status("Filter: extracting audio...", "#ef6c00")
            video_clip = VideoFileClip(input_video)
            if video_clip.audio is None:
                raise ValueError("Selected video has no audio track")

            video_clip.audio.write_audiofile(
                extracted_audio_path,
                codec="pcm_s16le",
                fps=16000,
                logger=None,
            )

            self._set_filter_status("Filter: transcribing...", "#ef6c00")
            if self.whisper_model is None:
                self.whisper_model = whisper.load_model("base")

            result = self.whisper_model.transcribe(extracted_audio_path)

            with open("profanity.txt", "r", encoding="utf-8") as f:
                bad_words = [line.strip().lower() for line in f if line.strip()]

            bad_word_times = []
            for segment in result.get("segments", []):
                segment_text = segment.get("text", "").lower()
                start = float(segment.get("start", 0))
                end = float(segment.get("end", 0))
                if any(word in segment_text for word in bad_words):
                    bad_word_times.append((start, end))

            self._set_filter_status("Filter: muting segments...", "#ef6c00")
            audio = AudioSegment.from_wav(extracted_audio_path)

            for start, end in bad_word_times:
                start_ms = int(start * 1000)
                end_ms = int(end * 1000)
                silence = AudioSegment.silent(duration=max(0, end_ms - start_ms))
                audio = audio[:start_ms] + silence + audio[end_ms:]

            audio.export(clean_audio_path, format="wav")

            self._set_filter_status("Filter: rebuilding video...", "#ef6c00")
            clean_audio_clip = AudioFileClip(clean_audio_path)
            if hasattr(video_clip, "with_audio"):
                final_video = video_clip.with_audio(clean_audio_clip)
            else:
                final_video = video_clip.set_audio(clean_audio_clip)
            final_video.write_videofile(
                clean_video_path,
                codec="libx264",
                audio_codec="aac",
                fps=video_clip.fps,
                logger=None,
            )
            final_video.close()

            self.root.after(0, lambda: self._on_filter_done(clean_video_path, len(bad_word_times)))
        except Exception as exc:
            self.root.after(0, lambda: self._on_filter_error(str(exc)))
        finally:
            if clean_audio_clip is not None:
                clean_audio_clip.close()
            if video_clip is not None:
                video_clip.close()
            self.filtering_in_progress = False

    def _on_filter_done(self, clean_video_path, muted_count):
        self.clean_video_path = clean_video_path
        self._set_filter_status(f"Filter: done ({muted_count} muted)", "#2e7d32")
        messagebox.showinfo("Success", f"Clean video created:\n{clean_video_path}")

    def _on_filter_error(self, err_text):
        self._set_filter_status("Filter: failed", "#c62828")
        messagebox.showerror("Filtering Error", err_text)

    def play_original_video(self):
        if not self.original_video_path:
            messagebox.showwarning("Warning", "Load a video first")
            return

        if self.current_video_path != self.original_video_path:
            loaded = self._load_video_source(self.original_video_path, source_name="Original")
            if not loaded:
                return

        self.play_video()

    def play_clean_video(self):
        if not self.clean_video_path or not os.path.exists(self.clean_video_path):
            messagebox.showwarning("Warning", "Filter profanity first to create the clean video")
            return

        if self.current_video_path != self.clean_video_path:
            loaded = self._load_video_source(self.clean_video_path, source_name="Clean")
            if not loaded:
                return

        self.play_video()

    def _extract_audio(self, video_path):
        if not self.mixer_ready:
            self.audio_path = None
            self._set_audio_status("Audio: mixer unavailable", "#c62828")
            return

        clip = None
        previous_audio_path = self.audio_path
        self.audio_path = None
        try:
            # Release any file handle held by pygame before writing new preview audio.
            try:
                pygame.mixer.music.stop()
                if hasattr(pygame.mixer.music, "unload"):
                    pygame.mixer.music.unload()
            except Exception:
                pass

            os.makedirs("audio", exist_ok=True)
            base_name = os.path.splitext(os.path.basename(video_path))[0]
            preview_audio_path = os.path.join("audio", f"preview_{base_name}_{int(time.time() * 1000)}.wav")

            clip = VideoFileClip(video_path)
            if clip.audio is None:
                self._set_audio_status("Audio: no audio track", "#ef6c00")
                return

            clip.audio.write_audiofile(
                preview_audio_path,
                codec="pcm_s16le",
                fps=44100,
                logger=None,
            )
            self.audio_path = preview_audio_path
            self.generated_audio_paths.add(preview_audio_path)
            self._set_audio_status("Audio: ready", "#2e7d32")
        except Exception as exc:
            print(f"Audio extraction failed: {exc}")
            self.audio_path = None
            self._set_audio_status("Audio: extraction failed", "#c62828")
        finally:
            if clip is not None:
                clip.close()

            # Best-effort cleanup of the previous preview audio after switching source.
            if previous_audio_path and previous_audio_path in self.generated_audio_paths:
                if previous_audio_path != self.audio_path:
                    self._safe_delete_file(previous_audio_path)
                    self.generated_audio_paths.discard(previous_audio_path)

    def _seek_and_show(self, frame_index):
        if not self.cap:
            return

        frame_index = max(0, min(frame_index, max(0, self.total_frames - 1)))
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ok, frame = self.cap.read()
        if not ok:
            return

        self.current_frame = frame_index
        self._render_frame(frame)
        self.progress_scale.set(self.current_frame)
        self._update_time_label()

    def _render_frame(self, frame):
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        if canvas_w <= 1 or canvas_h <= 1:
            return

        h, w = frame.shape[:2]
        aspect = w / h

        if canvas_w / canvas_h > aspect:
            new_h = canvas_h
            new_w = int(new_h * aspect)
        else:
            new_w = canvas_w
            new_h = int(new_w / aspect)

        frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        image = Image.fromarray(frame)
        photo = ImageTk.PhotoImage(image=image)

        self.canvas.delete("all")
        self.canvas.create_image(canvas_w // 2, canvas_h // 2, image=photo)
        self.canvas.image = photo

    def play_video(self):
        if not self.cap or not self.cap.isOpened():
            messagebox.showwarning("Warning", "Open a video first")
            return
        if self.is_playing:
            return

        self.is_playing = True
        self.playback_start_time = time.perf_counter()
        self.playback_start_frame = self.current_frame

        if self.mixer_ready and self.audio_path and os.path.exists(self.audio_path):
            try:
                pygame.mixer.music.load(self.audio_path)
                start_sec = self.current_frame / self.fps
                if start_sec > 0:
                    try:
                        pygame.mixer.music.play(loops=0, start=start_sec)
                    except Exception:
                        # WAV seeking is not always supported; fallback keeps audio working.
                        pygame.mixer.music.play(loops=0)
                else:
                    pygame.mixer.music.play(loops=0)
                pygame.mixer.music.set_volume(self.volume)
                self._set_audio_status("Audio: playing", "#2e7d32")
            except Exception as exc:
                print(f"Audio playback failed: {exc}")
                self._set_audio_status("Audio: playback failed", "#c62828")
        elif not self.mixer_ready:
            self._set_audio_status("Audio: mixer unavailable", "#c62828")
        else:
            self._set_audio_status("Audio: not available", "#ef6c00")

        self._playback_tick()

    def _playback_tick(self):
        if not self.is_playing or not self.cap:
            return

        elapsed = time.perf_counter() - self.playback_start_time
        target_frame = self.playback_start_frame + int(elapsed * self.fps)

        if target_frame >= self.total_frames:
            self.stop_video()
            return

        if target_frame != self.current_frame:
            self._seek_and_show(target_frame)

        self.root.after(10, self._playback_tick)

    def pause_video(self):
        if not self.is_playing:
            return

        self.is_playing = False
        if self.mixer_ready and pygame.mixer.music.get_busy():
            pygame.mixer.music.pause()
            self._set_audio_status("Audio: paused", "#666")

    def stop_video(self, reset_frame=True):
        self.is_playing = False
        if self.mixer_ready:
            pygame.mixer.music.stop()
            self._set_audio_status("Audio: stopped", "#666")

        if self.cap and reset_frame:
            self._seek_and_show(0)

    def _on_seek(self, value):
        if self.is_playing:
            return
        if not self.cap:
            return

        self._seek_and_show(int(float(value)))

    def _on_volume_change(self, value):
        self.volume = max(0.0, min(1.0, float(value) / 100.0))
        if self.mixer_ready:
            try:
                pygame.mixer.music.set_volume(self.volume)
            except Exception:
                pass

    def _on_resize(self, _event):
        if self.cap:
            self._seek_and_show(self.current_frame)

    def _update_time_label(self):
        cur = self.current_frame / self.fps if self.fps > 0 else 0
        total = self.total_frames / self.fps if self.fps > 0 else 0
        self.time_label.config(text=f"{self._fmt_time(cur)} / {self._fmt_time(total)}")

    def _set_audio_status(self, text, color="#666"):
        self.audio_status_label.config(text=text, fg=color)

    def _set_filter_status(self, text, color="#666"):
        self.root.after(0, lambda: self.filter_status_label.config(text=text, fg=color))

    def _load_profanity_words(self):
        if not os.path.exists("profanity.txt"):
            open("profanity.txt", "a", encoding="utf-8").close()

        with open("profanity.txt", "r", encoding="utf-8") as f:
            self.profanity_words = {line.strip().lower() for line in f if line.strip()}

        self._refresh_profanity_ui()

    def _refresh_profanity_ui(self):
        words = sorted(self.profanity_words)
        menu = self.profanity_dropdown["menu"]
        menu.delete(0, "end")

        if words:
            for word in words:
                menu.add_command(label=word, command=lambda w=word: self.selected_profanity_word.set(w))
            self.selected_profanity_word.set(words[0])
        else:
            self.selected_profanity_word.set("")

        self.profanity_count_label.config(text=f"Profanity list: {len(self.profanity_words)} words")

    def _save_profanity_words(self):
        words = sorted(self.profanity_words)
        with open("profanity.txt", "w", encoding="utf-8") as f:
            if words:
                f.write("\n".join(words) + "\n")

    def _add_profanity_word(self, _event=None):
        raw_word = self.profanity_entry.get().strip().lower()
        if not raw_word:
            return

        if raw_word in self.profanity_words:
            messagebox.showinfo("Info", f"'{raw_word}' is already in the profanity list")
            return

        self.profanity_words.add(raw_word)
        self._save_profanity_words()
        self._refresh_profanity_ui()
        self.profanity_entry.delete(0, tk.END)
        self._set_filter_status("Filter: word added", "#2e7d32")

    def _remove_selected_profanity_word(self):
        word = self.selected_profanity_word.get().strip().lower()
        if not word:
            messagebox.showinfo("Info", "No profanity word available to remove")
            return

        if word not in self.profanity_words:
            self._refresh_profanity_ui()
            return

        self.profanity_words.remove(word)
        self._save_profanity_words()
        self._refresh_profanity_ui()
        self._set_filter_status("Filter: word removed", "#2e7d32")

    @staticmethod
    def _safe_delete_file(path):
        try:
            if path and os.path.exists(path):
                os.remove(path)
        except Exception:
            pass

    @staticmethod
    def _fmt_time(seconds):
        m = int(seconds // 60)
        s = int(seconds % 60)
        return f"{m:02d}:{s:02d}"

    def cleanup(self):
        self.stop_video(reset_frame=False)

        if self.mixer_ready and hasattr(pygame.mixer.music, "unload"):
            try:
                pygame.mixer.music.unload()
            except Exception:
                pass

        if self.cap:
            self.cap.release()
            self.cap = None

        for path in list(self.generated_audio_paths):
            self._safe_delete_file(path)
            self.generated_audio_paths.discard(path)


if __name__ == "__main__":
    root = tk.Tk()
    player = VideoPlayer(root)

    def on_close():
        player.cleanup()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()
