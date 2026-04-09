import re
import unicodedata

def normalize(text):
    return unicodedata.normalize("NFC", text).lower().strip()

def tokenize(text):
    return re.findall(r"\w+", text)