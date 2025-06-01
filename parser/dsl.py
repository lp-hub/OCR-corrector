import re
import gzip
import chardet
from pathlib import Path
from pyglossary.glossary_v2 import Glossary

def extract_words(text):
    return re.findall(r"\b[a-zA-Z][a-zA-Z0-9\-']{1,}\b", text)

def detect_encoding(filepath: Path):
    with open(filepath, 'rb') as f:
        raw = f.read(4096)
        result = chardet.detect(raw)
        return result["encoding"] or "utf-8"

def read_dsl_lines(filepath: Path):
    if filepath.suffix == ".dz" or filepath.suffixes[-2:] == [".dict", ".dsl", ".dz", ".dct", ".dsl.dz"]:
        with gzip.open(filepath, 'rb') as f:
            raw = f.read()
    else:
        with open(filepath, 'rb') as f:
            raw = f.read()
    encoding = chardet.detect(raw)["encoding"] or "utf-8"
    text = raw.decode(encoding, errors="ignore")
    return text.splitlines()

def parse_dsl_file(filepath: Path, all_words: set, skipped_files: list):
    try:
        glossary = Glossary()
        glossary.read(str(filepath), read_options={"format": "Auto"})
        for entry in glossary.entries():
            all_words.update(extract_words(entry.term))
            all_words.update(extract_words(entry.definition or ""))
        print(f"[OK] glossary_v2 parsed: {filepath}")
    except Exception as e:
        try:
            # Fallback to manual DSL parsing
            lines = read_dsl_lines(filepath)
            for line in lines:
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("﻿#"):
                    continue
                if line.startswith("\t"):
                    continue
                words = extract_words(line)
                all_words.update(words)
            print(f"[OK] Manual DSL parsed: {filepath}")
        except Exception as err:
            print(f"[SKIP] Failed DSL: {filepath} — {err}")
            skipped_files.append(f"{filepath} — {err}")

def dsl(input_dir: Path, output_dir: Path) -> tuple[set, list]:
    all_words = set()
    skipped_files = []

    dsl_files = list(input_dir.rglob("*.dsl")) + list(input_dir.rglob("*.dsl.dz")) + list(input_dir.rglob("*.dz"))
    if not dsl_files:
        print(f"[INFO] No DSL files found in {input_dir}")
        return all_words, skipped_files

    for filepath in dsl_files:
        parse_dsl_file(filepath, all_words, skipped_files)

    output_dir.mkdir(parents=True, exist_ok=True)

    out_file = output_dir / "dsl_wordlist.txt"
    with out_file.open("w", encoding="utf-8") as f:
        for word in sorted(all_words):
            f.write(word + "\n")

    skipped_log = output_dir / "skipped_dsl.txt"
    if skipped_files:
        with skipped_log.open("w", encoding="utf-8") as f:
            for item in skipped_files:
                f.write(item + "\n")

    print(f"\n[DONE] Extracted {len(all_words)} words to {out_file.resolve()}")
    if skipped_files:
        print(f"[INFO] Skipped {len(skipped_files)} DSL files. See {skipped_log.resolve()}")
    return all_words, skipped_files

if __name__ == "__main__":
    input_dir = Path("INPUT_DICT")
    output_dir = Path("OUTPUT_DICT")
    dsl(input_dir, output_dir)