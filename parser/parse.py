"""
    Script EXTRACTS WORDS from dictionaries for whitelist.py
    Unsupported formats are ingoned. pip install pyglossary
"""
from pathlib import Path
from parser.find import copy_files_with_specific_lang
from parser.stardict import stardict
from parser.dsl import dsl

ADD_LANG = 'en' # find English dictionaries
SKIP_LANG = ['ruen', 'uken', 'esen'] # skip files containing...
SRC_DICT = Path("/alldict/") # source folder to copy from
INPUT_DICT = Path("/EN/") # destintation for copy but input for parsers
OUTPUT_DICT = Path("db")
OUTPUT_DICT.mkdir(parents=True, exist_ok=True)

OUTPUT_WORDLIST = OUTPUT_DICT / "dictionary_wordlist.txt"
OUTPUT_SKIPPED = OUTPUT_DICT / "skipped_dictionaries.txt"

# Copy dictionaries with selected language => # comment if not needed
copy_files_with_specific_lang(SRC_DICT, INPUT_DICT, SKIP_LANG, ADD_LANG)

# Validate input path
if not INPUT_DICT.exists() or not INPUT_DICT.is_dir():
    print("[ERROR] No input! Check path to dictionaries.")
    exit(1)

# Check if directory is empty
if not any(INPUT_DICT.iterdir()):
    print(f"[ERROR] Input directory '{INPUT_DICT}' is empty.")
    exit(1)

def all_dictionaries():
    # Proceed if directory is valid and non-empty
    OUTPUT_DICT.mkdir(parents=True, exist_ok=True)
    
    # Expect these functions to return (set_of_words, list_of_skipped_files)
    dsl_words, dsl_skipped = dsl(INPUT_DICT, OUTPUT_DICT)
    stardict_words, stardict_skipped = stardict(INPUT_DICT, OUTPUT_DICT)

    all_words = dsl_words.union(stardict_words)
    skipped_files = dsl_skipped + stardict_skipped

    # Write extracted word list
    with open(OUTPUT_WORDLIST, "w", encoding="utf-8") as f:
        for word in sorted(all_words):
            f.write(f"{word}\n")

    # Write skipped dictionary logs
    if skipped_files:
        with open(OUTPUT_SKIPPED, "w", encoding="utf-8") as f:
            for item in skipped_files:
                f.write(f"{item}\n")

    print(f"[DONE] Extracted {len(all_words)} unique words into: {OUTPUT_WORDLIST}")
    print(f"[INFO] Logged {len(skipped_files)} skipped/errored files into: {OUTPUT_SKIPPED}")

if __name__ == "__main__":
    all_dictionaries()