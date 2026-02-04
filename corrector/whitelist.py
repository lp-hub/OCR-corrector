"""
    Build a Smart Whitelist Automatically
    Step 1: Extract Candidate Words from Your Corpus
    Scan all your OCR'd .txt files and collect:
        Words that appear frequently across books (e.g. frequency ≥ 2)
        Capitalized words that aren't sentence-initial (likely proper nouns)
        Unrecognized words that repeat often (misspellings or foreign terms)
        Result: a base vocabulary that's tailored to your actual books, not to generic English.
    Step 2: Filter Out Obvious Junk
    Use regex or basic rules to exclude:
        1–2 letter junk
        Pure numbers, or weird symbols
        Low-occurrence typos (occur once → noise)
"""
import nltk
import os
import re
from collections import Counter
from pathlib import Path
from nltk.corpus import names
nltk.download('names', quiet=True) # Download names corpus if not already available

def build_whitelist_from_texts(base_dir, min_occurrences=2):
    word_counter = Counter()
    for path in Path(base_dir).rglob("*.txt"):
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                words = re.findall(r"\b[a-zA-Z’'-]{3,}\b", line)
                word_counter.update(w.lower() for w in words)
    return {word for word, freq in word_counter.items() if freq >= min_occurrences}

def load_dictionary_words(dict_path):
    dict_file = Path(dict_path)
    if not dict_file.exists():
        print(f"[WARN] Dictionary file not found: {dict_path}")
        return set()
    with open(dict_file, "r", encoding="utf-8", errors="ignore") as f:
        return {line.strip().lower() for line in f if line.strip()}

def save_whitelist(whitelist, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for word in sorted(whitelist):
            f.write(word + "\n")

# ========== MAIN EXECUTION ==========
OCR_DIR = os.getenv("MEDIA") / "txt/" # OCRd texts directory
DICT_WORDLIST = "db/dictionary_wordlist.txt"
OUTPUT_FILE = "db/whitelist.txt"

# Step 1–2: Build whitelist from OCR'd text
whitelist = build_whitelist_from_texts(OCR_DIR, min_occurrences=2)

# Step 3: Enrich with NLTK names corpus
whitelist |= {name.lower() for name in names.words()}

# Save to logs/
save_whitelist(whitelist, OUTPUT_FILE)
print(f"[DONE] Saved whitelist with {len(whitelist):,} words to {OUTPUT_FILE}")

# Wikidata Names Dump:
# https://dumps.wikimedia.org/wikidatawiki/entities/
#     Not officially offered as a names-only download.
#     WikiMedia Dumps can be filtered via wikidata-filter or SPARQL queries.
# Domain-specific glossaries:
#         WordNet® is a large lexical database:
# https://wordnet.princeton.edu/
#         UMLS Metathesaurus
# https://wordnet.princeton.edu/
#         Domain-specific Wikibooks/Wikipedia/Glossaries
#         Export from structured datasets in arXiv/CORD-19/ACL Anthology