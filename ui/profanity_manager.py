"""Profanity list editor mixin for add/remove/select and persistence."""

from tkinter import messagebox

from config.settings import settings
from utils.file_manager import read_profanity_words, write_profanity_words


class ProfanityManagerMixin:
    """Owns profanity list data and listbox synchronization."""

    def _load_profanity_words(self):
        self.profanity_words = read_profanity_words(settings.profanity_file)
        self._refresh_profanity_ui()

    def _refresh_profanity_ui(self):
        words = sorted(self.profanity_words)
        self.profanity_listbox.delete(0, self.tk.END)
        for word in words:
            self.profanity_listbox.insert(self.tk.END, word)

        if words:
            self.profanity_listbox.selection_set(0)
            self.profanity_listbox.see(0)
            self.selected_profanity_word.set(words[0])
        else:
            self.selected_profanity_word.set("")

        self.profanity_count_label.configure(text=f"Profanity list: {len(self.profanity_words)} words")
        self._update_current_word_label()

    def _save_profanity_words(self):
        write_profanity_words(settings.profanity_file, self.profanity_words)

    def _on_profanity_select(self, _event=None):
        selection = self.profanity_listbox.curselection()
        if selection:
            self.selected_profanity_word.set(self.profanity_listbox.get(selection[0]))
        else:
            self.selected_profanity_word.set("")
        self._update_current_word_label()

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
        self.profanity_entry.delete(0, self.tk.END)
        self._set_filter_status("Filter: word added", self.palette["success"])

    def _remove_selected_profanity_word(self):
        selection = self.profanity_listbox.curselection()
        word = self.profanity_listbox.get(selection[0]).strip().lower() if selection else self.selected_profanity_word.get().strip().lower()
        if not word:
            messagebox.showinfo("Info", "No profanity word available to remove")
            return

        if word not in self.profanity_words:
            self._refresh_profanity_ui()
            return

        self.profanity_words.remove(word)
        self._save_profanity_words()
        self._refresh_profanity_ui()
        self._set_filter_status("Filter: word removed", self.palette["success"])

    def _update_current_word_label(self):
        selected = self.selected_profanity_word.get().strip()
        if selected:
            self.selected_word_label.configure(text=f"Selected: {selected}")
        else:
            self.selected_word_label.configure(text="Select a word to remove it")

    def _update_intelligence_mode_description(self, *_args):
        descriptions = {
            "kids": "Strict filtering (removes all offensive words, including masked words)",
            "adult": "Moderate filtering (removes strong profanity only)",
            "custom": "Uses your custom profanity word list",
        }
        self.intelligence_mode_description_text.set(descriptions.get(self.intelligence_mode.get(), ""))
