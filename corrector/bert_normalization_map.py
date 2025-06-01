"""
    If you have very bad text, don't waste time.
    Rescan it, bacuse BERT won't restore anything.
    Model will be just hallucinating on the noise.
        What script does?
    Auto-accepts corrections with:
        High lexical similarity (e.g., "enviroment" → "environment")
        OR better fluency score with corrected sentence
    Outputs clean JSON for patching your normalization_map.json
    Logs fuzzy/uncertain cases to bert_manual_review.txt
"""
import json
import re
from pathlib import Path
from rapidfuzz import fuzz
from transformers import AutoModelForMaskedLM, AutoTokenizer
import torch

# ========== Config ==========
REJECTION_FILE = Path("logs") / "ocr_bert_rejection_report.txt"
NORMALIZATION_PATCH = Path("db") / "normalization_map.json"
REVIEW_FILE = Path("logs") / "bert_manual_review.txt"
SIMILARITY_THRESHOLD = 85  # Lexical similarity
LM_SCORE_THRESHOLD = 3.0   # log-prob gain needed to accept correction

# ========== Load BERT ==========
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
model = AutoModelForMaskedLM.from_pretrained("bert-base-uncased").to(device)
model.eval()

def score_sentence(text: str) -> float:
    # Compute average token log-probability using masked LM
    inputs = tokenizer(text, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs = model(**inputs, labels=inputs["input_ids"])
        loss = outputs.loss
    return -loss.item() * len(inputs["input_ids"][0])  # pseudo log-prob
def is_mostly_digits(word: str) -> bool:
    # Reject things like '2001', '140s', '19a', '86', etc.
    return bool(re.fullmatch(r"\d{2,5}[a-z]?", word.lower()))
# ========== Processing ==========
accepted = {}
manual_review = []

with REJECTION_FILE.open("r", encoding="utf-8") as f:
    for line in f:
        if not line.startswith("[BERT REJECT]"):
            continue
        try:
            # if word.isdigit() or re.match(r"^\d+[a-z]?$", word.lower()):
            #     continue  # Skip BERT check
            wrong = line.split("'")[1]
            suggestion = line.split("→")[1].split("'")[1]
            context = line.split("in: ", 1)[1].strip()
            # === Skip numeric-like tokens ===
            if is_mostly_digits(wrong):
                continue
            # Lexical similarity
            sim = fuzz.ratio(wrong, suggestion)

            # Score original and fixed sentence
            context_fixed = context.replace(wrong, suggestion)
            score_orig = score_sentence(context)
            score_fixed = score_sentence(context_fixed)
            gain = score_fixed - score_orig

            # Accept if lexical match + language score gain
            if sim >= SIMILARITY_THRESHOLD or gain >= LM_SCORE_THRESHOLD:
                pattern = rf"\\b{re.escape(wrong)}\\b"
                accepted[pattern] = suggestion
            else:
                manual_review.append({
                    "word": wrong,
                    "suggestion": suggestion,
                    "context": context,
                    "similarity": sim,
                    "gain": round(gain, 2)
                })

        except Exception as e:
            print(f"[ERROR] Failed to parse or score: {line.strip()} - {e}")

# ========== Save accepted corrections ==========
with NORMALIZATION_PATCH.open("w", encoding="utf-8") as f:
    json.dump({"ocr_artifacts": accepted}, f, indent=2, ensure_ascii=False)

# ========== Save manual review file ==========
with REVIEW_FILE.open("w", encoding="utf-8") as f:
    for entry in manual_review:
        f.write(f"[UNCERTAIN] '{entry['word']}' → '{entry['suggestion']}' "
                f"(sim={entry['similarity']}, gain={entry['gain']}) in: {entry['context']}\n")

print(f"[OK] Auto-accepted: {len(accepted)} corrections → {NORMALIZATION_PATCH}")
print(f"[REVIEW] Remaining: {len(manual_review)} lines → {REVIEW_FILE}")