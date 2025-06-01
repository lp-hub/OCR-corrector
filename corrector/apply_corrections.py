'''
    Apllying correction of OCRD txt files using suggestions
    from suggest_corrections.py
    Use if needed.
'''
import json
import os
import re
from pathlib import Path

OCR_DIR = os.getenv("MEDIA") / "ocrd/"
OUTPUT_DIR = "logs/corrected_texts"
CORRECTIONS_FILE = "logs/ocr_corrections.json"
WHITELIST_FILE = "logs/whitelist.txt"

def load_corrections(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data.get("corrections", {})

def load_whitelist(path):
    with open(path, "r", encoding="utf-8") as f:
        return {line.strip().lower() for line in f}

def correct_text(text, corrections, whitelist):
    def replace_word(match):
        word = match.group(0)
        lower_word = word.lower()
        if lower_word in whitelist:
            return word  # leave it
        return corrections.get(lower_word, word)
    return re.sub(r"\b[a-zA-Z’'-]{3,}\b", replace_word, text)

def process_files(input_dir, output_dir, corrections, whitelist):
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for txt_file in input_dir.rglob("*.txt"):
        with open(txt_file, "r", encoding="utf-8", errors="ignore") as f:
            original_text = f.read()
        corrected_text = correct_text(original_text, corrections, whitelist)
        output_path = output_dir / txt_file.relative_to(input_dir)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(corrected_text)
        print(f"[DONE] Corrected: {output_path}")

# Load everything
corrections = load_corrections(CORRECTIONS_FILE)
whitelist = load_whitelist(WHITELIST_FILE)

# Apply to OCR text files
process_files(OCR_DIR, OUTPUT_DIR, corrections, whitelist)