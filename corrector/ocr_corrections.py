"""
    Merge dictionaries with parse.py, load result here and 
    merge with frequency_dictionary or any specialized dict.
    Accepted input format => TXT => 1 word per line
    Output format => TXT => word 1
"""
import os
import re
import json
import torch
from pathlib import Path
from rapidfuzz import fuzz
from symspellpy import SymSpell, Verbosity
from transformers import  AutoModelForMaskedLM, AutoTokenizer
from dotenv import load_dotenv
load_dotenv()
from merge_symspell import convert_to_symspell_format, merge_dictionaries, validate_symspell_dictionary

# ========== Configuration ==========
OUT_DB = Path("db")
DST_DIR = Path(os.getenv("DST_DIR", "text_files"))  # fallback for manual testing
OUT_LOGS = Path("logs")

DICT = OUT_DB / "dictionary_wordlist.txt"

FREQ_DICT =  OUT_DB / "frequency_dictionary_en_82_765.txt" # add specialize dictionary here
MAX_EDIT_DISTANCE = 2   # Use the SymSpell or Levenshtein distance - 2 or 3 - good default for OCR correction

DICT_SYM = DICT.with_suffix(".symspell.txt")
SYM_DICT_OUT = OUT_DB / "ocr_dictionary_symspell_merged.txt"
WHITELIST = OUT_DB / "whitelist.txt"
OUTPUT_JSON = OUT_LOGS / "ocr_corrections.json"
OUTPUT_TXT = OUT_LOGS / "ocr_suggestions_report.txt"
OUTPUT_BERT = OUT_LOGS / "ocr_rejection_report.txt"

# ========== BERT masked language model ==========
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
model = AutoModelForMaskedLM.from_pretrained("bert-base-uncased").to(device)
model.eval()

# ========== Normalization Maps ==========
LIGATURES = {"ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ffl"}
PUNCTUATION = {"–": "-", "—": "-", "‘": "'", "’": "'", "“": '"', "”": '"', "…": "..."}

REGEX_FIXES = {
    r"\bfa9ade\b": "façade",
    r"\bmedireval\b": "mediaeval",
    r"\bsub- sequent\b": "subsequent",
    r"\bHermetic A rcanum\b": "Hermetic Arcanum",
    r"\bAutJuw\b": "Author",
    r"\bTableaz£ de l'inconstance\b": "Tableau de l'inconstance",
    r"\bPhysictZ RestituttZ\b": "Physica Restituta",
}

# ========== Load and Merge Dictionaries ==========
convert_to_symspell_format(DICT, DICT_SYM)
merge_dictionaries(FREQ_DICT, DICT_SYM, SYM_DICT_OUT)
validate_symspell_dictionary(SYM_DICT_OUT)


# ========== Helper Functions ==========
def normalize(text):
    for src, tgt in {**LIGATURES, **PUNCTUATION}.items():
        text = text.replace(src, tgt)
    return text

def extract_words(text):
    return re.findall(r"\b[a-zA-Z0-9’'-]{3,}\b", text)

def load_whitelist(path):
    if not Path(path).exists():
        return set()
    with open(path, "r", encoding="utf-8") as f:
        return {line.strip().lower() for line in f if line.strip()}


# ========== BERT Check ==========
def is_bert_semantically_compatible_offset(
    original_line: str,
    target_word: str,
    suggestion: str,
    tokenizer,
    model,
    device,
    threshold_rank=3,
    fuzzy_threshold=85
) -> bool:
    """
    Checks if the suggestion is semantically valid in context using BERT masked LM with offset alignment.
    - Handles subword splits and tokenization mismatches using offset mapping + fuzzy match fallback.
    """
    # Tokenize with offset mapping for alignment
    inputs = tokenizer(original_line, return_offsets_mapping=True, return_tensors="pt")
    input_ids = inputs["input_ids"].to(device)
    offsets = inputs["offset_mapping"][0].tolist()
    tokens = tokenizer.convert_ids_to_tokens(input_ids[0])

    target_word_lower = target_word.lower()
    best_match_idx = None
    best_ratio = 0

    # Try exact match on raw offsets
    for i, (start, end) in enumerate(offsets):
        if start == end:
            continue  # special tokens like [CLS], [SEP]
        span = original_line[start:end].lower()
        if span == target_word_lower:
            best_match_idx = i
            break
        else:
            # Fuzzy fallback if exact match fails
            ratio = fuzz.ratio(span, target_word_lower)
            if ratio > best_ratio and ratio >= fuzzy_threshold:
                best_ratio = ratio
                best_match_idx = i

    if best_match_idx is None:
        return False  # Couldn’t align the word

    # Mask the identified token
    masked_input_ids = input_ids.clone()
    masked_input_ids[0, best_match_idx] = tokenizer.mask_token_id

    with torch.no_grad():
        outputs = model(masked_input_ids)
        logits = outputs.logits

    # Get top-k predictions for masked position
    predicted_ids = torch.topk(logits[0, best_match_idx], k=threshold_rank).indices
    predicted_tokens = tokenizer.convert_ids_to_tokens(predicted_ids)

    return suggestion.lower() in [t.lower() for t in predicted_tokens]

# Step 3: Load merged dictionary into SymSpell
sym_spell = SymSpell(max_dictionary_edit_distance=MAX_EDIT_DISTANCE, prefix_length=7)
if not sym_spell.load_dictionary(SYM_DICT_OUT, term_index=0, count_index=1):
    raise RuntimeError(f"Failed to load dictionary from {SYM_DICT_OUT}")
else:
    print(f"Loaded merged dictionary: {len(sym_spell._words)} words")


# ========== Process Text Files ==========
whitelist = load_whitelist(WHITELIST)
bert_rejections = []
corrections = {}
lines_with_corrections = []

for file_path in DST_DIR.rglob("*.txt"):
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        for line_num, raw_line in enumerate(f, start=1):
            line = normalize(raw_line)

            # Apply regex artifact rules
            for pattern, replacement in REGEX_FIXES.items():
                if re.search(pattern, line):
                    fixed = re.sub(pattern, replacement, line)
                    lines_with_corrections.append({
                        "file": str(file_path),
                        "line": line_num,
                        "original": line.strip(),
                        "suggested": fixed.strip()
                    })
                    corrections[pattern] = replacement

            # Spellcheck individual words
            words = set(extract_words(line.lower()))
            for word in words:
                if word in whitelist or sym_spell._words.get(word, 0) > 0:
                    continue
                
                suggestions = sym_spell.lookup(word, Verbosity.TOP, max_edit_distance=MAX_EDIT_DISTANCE)
                if suggestions:
                    best = suggestions[0]
                    if best.term != word:
                        context_ok = is_bert_semantically_compatible_offset(
                            original_line=line,
                            target_word=word,
                            suggestion=best.term,
                            tokenizer=tokenizer,
                            model=model,
                            device=device
                        )
                        if context_ok:
                            lines_with_corrections.append({
                                "file": str(file_path),
                                "line": line_num,
                                "original": word,
                                "suggested": best.term
                            })
                            corrections[word] = best.term
                        else:
                            bert_rejections.append({
                                "word": word,
                                "suggested": best.term,
                                "context": line.strip()
                            })
                        print(f"[BERT REJECT] '{word}' → '{best.term}' in: {line.strip()}")

# ========== Output Results ==========
with open(OUTPUT_JSON, "w", encoding="utf-8") as f: # Save JSON report
    json.dump({
        "corrections": corrections,
        "lines": lines_with_corrections
    }, f, indent=2, ensure_ascii=False)

with open(OUTPUT_TXT, "w", encoding="utf-8") as f: # Save text report
    for entry in lines_with_corrections:
        f.write(f"[{entry['file']}:{entry['line']}] '{entry['original']}' → '{entry['suggested']}'\n")

with open(OUTPUT_BERT, "w", encoding="utf-8") as f: # Save text report
    for entry in bert_rejections:
        f.write(f"[BERT REJECT] '{entry['word']}' → '{entry['suggested']}' in: {entry['context']}\n")

print(f"[DONE] Corrections saved to {OUTPUT_JSON} and {OUTPUT_TXT}")
print(f"[DONE] BERT rejections saved to {OUTPUT_BERT}")

# Regex-based artifact replacement
# Ligature/punctuation normalization
# SymSpell-based OCR correction
# Whitelist filtering
# .json + .txt output
# File and line-level logging
# You can also post-process the JSON output like this:
# regex_map = {fr"\\b{k}\\b": v for k, v in corrections.items()}