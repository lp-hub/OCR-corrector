"""
    Merge dictionaries function modeule
"""
from pathlib import Path

# ========== Load and Merge Dictionaries ==========
def convert_to_symspell_format(input_path: Path, output_path: Path):
    """Convert raw wordlist to SymSpell format with dummy frequency."""
    with open(input_path, "r", encoding="utf-8") as infile, open(output_path, "w", encoding="utf-8") as outfile:
        for word in infile:
            word = word.strip()
            if word:
                # outfile.write(f"{word}\t1\n") # TAB
                outfile.write(f"{word} 1\n")  # space-separated


# ========== Merge frequency dict + wordlist, space-separated ==========
def merge_dictionaries(freq_path: Path, wordlist_path: Path, output_path: Path):
    seen = set()

    with open(output_path, "w", encoding="utf-8") as out:
        # Add frequency dictionary (already space-separated)
        with open(freq_path, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) == 2 and parts[1].isdigit():
                    word, freq = parts
                    if word not in seen:
                        out.write(f"{word} {freq}\n")
                        seen.add(word)

        # Add wordlist (already space-separated)
        with open(wordlist_path, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) == 2 and parts[1].isdigit():
                    word = parts[0]
                    if word not in seen:
                        out.write(f"{word} 1\n")
                        seen.add(word)

    print(f"[✓] Merged dictionary saved to: {output_path}")
    print(f"[DEBUG] Merged dictionary has {sum(1 for _ in open(output_path, 'r', encoding='utf-8'))} entries.")


# ========== Vealidate result ==========
def validate_symspell_dictionary(dict_path: Path):
    import re
    error_count = 0
    with open(dict_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            parts = line.rstrip("\n").split("\t")
            if len(parts) != 2:
                print(f"[LINE {i}] Invalid format (tab count ≠ 1): {line.strip()}")
                error_count += 1
                continue
            word, freq = parts
            if not re.fullmatch(r"\d+", freq):
                print(f"[LINE {i}] Invalid frequency: '{freq}' in line: {line.strip()}")
                error_count += 1
    if error_count:
        print(f"\n[!] Total validation errors: {error_count}")
    else:
        print("✓ Dictionary format validated successfully.")


# if __name__ == "__main__":
#     convert_to_symspell_format(DICT, DICT_SYM)
#     merge_dictionaries(FREQ_DICT, DICT_SYM, SYM_DICT_OUT)
#     validate_symspell_dictionary(SYM_DICT_OUT)