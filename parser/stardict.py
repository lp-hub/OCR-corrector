from pathlib import Path
import struct
import gzip

def parse_ifo(ifo_path: Path) -> dict:
    meta = {}
    with open(ifo_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if "=" in line:
                key, val = line.split("=", 1)
                meta[key.strip()] = val.strip()
    return meta

def parse_idx(idx_path: Path) -> list:
    entries = []
    with open(idx_path, "rb") as f:
        while True:
            word_bytes = bytearray()
            while (b := f.read(1)) and b != b'\x00':
                word_bytes.extend(b)
            if not word_bytes:
                break
            word = word_bytes.decode('utf-8')
            offset_bytes = f.read(4)
            length_bytes = f.read(4)
            if len(offset_bytes) < 4 or len(length_bytes) < 4:
                break
            offset = struct.unpack(">I", offset_bytes)[0]
            length = struct.unpack(">I", length_bytes)[0]
            entries.append((word, offset, length))
    return entries

def parse_dict(dict_path: Path, entries: list, compressed: bool = False) -> dict:
    result = {}
    open_fn = gzip.open if compressed else open
    with open_fn(dict_path, "rb") as f:
        for word, offset, length in entries:
            f.seek(offset)
            definition_bytes = f.read(length)
            try:
                definition = definition_bytes.decode('utf-8')
            except UnicodeDecodeError:
                definition = definition_bytes.decode('latin-1') # fallback
            result[word] = definition
    return result

def parse_stardict_from_base(base_path: Path) -> dict:
    try:
        ifo_path = base_path.with_suffix(".ifo")
        idx_path = base_path.with_suffix(".idx")
        dict_path = base_path.with_suffix(".dict")
        dict_dz_path = base_path.with_suffix(".dict.dz")

        if not ifo_path.exists() or not idx_path.exists():
            print(f"[SKIP] Missing .ifo or .idx for {base_path.stem}")
            return {}

        entries = parse_idx(idx_path)

        if dict_path.exists():
            dictionary = parse_dict(dict_path, entries, compressed=False)
        elif dict_dz_path.exists():
            dictionary = parse_dict(dict_dz_path, entries, compressed=True)
        else:
            print(f"[SKIP] No .dict or .dict.dz found for {base_path.stem}")
            return {}

        print(f"[OK] Parsed {len(dictionary)} entries from {base_path.stem}")
        return dictionary

    except Exception as e:
        print(f"[ERROR] Failed parsing {base_path.stem}: {e}")
        return {}

def parse_all_stardicts_in_dir(root_dir: Path) -> tuple[set, list]:
    s_all_words = set()
    s_skipped_files = []
    for ifo_file in root_dir.rglob("*.ifo"):
        base = ifo_file.with_suffix("")  # strip .ifo
        result = parse_stardict_from_base(base)
        if result:
            s_all_words.update(result.keys())
        else:
            s_skipped_files.append(str(base))
    return s_all_words, s_skipped_files

# === Main Function for CLI or Import Use ===
def stardict(input: Path, output: Path) -> tuple[set, list]:
    output.mkdir(parents=True, exist_ok=True)
    s_all_words, s_skipped_files = parse_all_stardicts_in_dir(input)
    if not s_all_words:
        print(f"[INFO] No Stardict files found in {input}")

    # Write word list
    out_file = output / "stardict_wordlist.txt"
    with out_file.open("w", encoding="utf-8") as f:
        for word in sorted(s_all_words):
            f.write(word + "\n")
        if not (output):
           print(f"[INFO] No Stardict files found in {input}")

    # Write skipped files
    skipped_log = output / "skipped_stardict.txt"
    if s_skipped_files:
        with skipped_log.open("w", encoding="utf-8") as f:
            for item in s_skipped_files:
                f.write(item + "\n")

    print(f"\n[DONE] Extracted {len(s_all_words)} words to {out_file.resolve()}")
    if s_skipped_files:
        print(f"[INFO] Skipped {len(s_skipped_files)} files. See {skipped_log.resolve()}")
    return s_all_words, s_skipped_files

# === Usage ===
if __name__ == "__main__":
    input = Path("INPUT_DICT")     # Replace with actual input path
    output = Path("OUTPUT_DICT")   # Replace with actual output path
    stardict(input, output)