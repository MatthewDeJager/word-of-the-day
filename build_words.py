"""Build words.json from words.xlsx.

words.xlsx is the source of truth. Never edit words.json by hand.

Usage:
    python build_words.py

Exits non-zero (and leaves words.json untouched) if any row is invalid.
"""

import json
import os
import re
import sys

from openpyxl import load_workbook

HERE = os.path.dirname(os.path.abspath(__file__))
XLSX_PATH = os.path.join(HERE, "words.xlsx")
JSON_PATH = os.path.join(HERE, "words.json")

COLUMNS = ["word", "pos", "pronunciation", "definition", "example", "synonyms"]
REQUIRED = {"word", "pos", "definition", "example"}

# Parts of speech allowed in the `pos` column. Combos like "adverb / adjective"
# are fine; each part must be one of these. Add to this set if you need more.
KNOWN_POS = {
    "noun", "verb", "adjective", "adverb",
    "pronoun", "preposition", "conjunction", "interjection", "phrase",
}
POS_SPLIT = re.compile(r"\s*[/,;&]\s*|\s+or\s+|\s+and\s+")

# Respelling: hyphen-separated syllables, words separated by spaces,
# each syllable all-lowercase or ALL-UPPERCASE (stressed), at least one stressed.
SYLLABLE = re.compile(r"^(?:[a-z']+|[A-Z']+)$")


def cell_text(value):
    """Normalize a cell to a stripped string ('' for blank)."""
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return str(value).strip()


def check_pronunciation(text):
    """Return an error message, or None if `text` follows the convention."""
    syllables = [s for word in text.split() for s in word.split("-")]
    if not syllables or any(not SYLLABLE.match(s) for s in syllables):
        return (
            f"pronunciation {text!r} must be hyphen-separated syllables, each all "
            "lowercase or ALL UPPERCASE (e.g. per-spi-KASS-i-tee)"
        )
    if not any(s.isupper() for s in syllables):
        return f"pronunciation {text!r} has no STRESSED (uppercase) syllable"
    return None


def parse_row(row_num, cells, errors):
    """Turn one sheet row into an entry dict, appending any problems to `errors`."""
    extra = [c for c in cells[len(COLUMNS):] if cell_text(c)]
    if extra:
        errors.append(f"row {row_num}: has data beyond the '{COLUMNS[-1]}' column")

    values = {name: cell_text(cells[i]) if i < len(cells) else "" for i, name in enumerate(COLUMNS)}

    missing = [name for name in COLUMNS if name in REQUIRED and not values[name]]
    if missing:
        errors.append(f"row {row_num}: missing required field(s): {', '.join(missing)}")
        return None

    pos_parts = [p for p in POS_SPLIT.split(values["pos"].lower()) if p]
    unknown = [p for p in pos_parts if p not in KNOWN_POS]
    if unknown:
        errors.append(
            f"row {row_num}: unknown part of speech {', '.join(map(repr, unknown))} "
            f"(allowed: {', '.join(sorted(KNOWN_POS))})"
        )

    if values["pronunciation"]:
        problem = check_pronunciation(values["pronunciation"])
        if problem:
            errors.append(f"row {row_num}: {problem}")

    entry = {
        "word": values["word"],
        "pos": values["pos"],
        "pronunciation": values["pronunciation"],
        "definition": values["definition"],
        "example": values["example"],
        "synonyms": [s.strip() for s in values["synonyms"].split(";") if s.strip()],
    }
    # Omit empty optional fields entirely.
    return {k: v for k, v in entry.items() if v}


def build():
    if not os.path.exists(XLSX_PATH):
        sys.exit(f"ERROR: {XLSX_PATH} not found.")
    try:
        wb = load_workbook(XLSX_PATH, read_only=True, data_only=True)
    except PermissionError:
        sys.exit("ERROR: can't read words.xlsx. Close it in Excel and try again.")

    ws = wb.worksheets[0]
    rows = ws.iter_rows(values_only=True)

    header = [cell_text(c).lower() for c in next(rows, ())]
    while header and not header[-1]:
        header.pop()
    if header != COLUMNS:
        sys.exit(
            "ERROR: row 1 must be the header: " + " | ".join(COLUMNS)
            + "\n       found: " + " | ".join(header or ["(empty)"])
        )

    entries, errors, seen = [], [], {}
    for row_num, cells in enumerate(rows, start=2):
        if not any(cell_text(c) for c in cells):
            continue  # skip empty rows
        entry = parse_row(row_num, cells, errors)
        if entry is None:
            continue
        key = entry["word"].lower()
        if key in seen:
            errors.append(f"row {row_num}: duplicate word {entry['word']!r} (first seen on row {seen[key]})")
            continue
        seen[key] = row_num
        entries.append(entry)
    wb.close()

    if errors:
        print(f"ERROR: words.xlsx has {len(errors)} problem(s); words.json was NOT written.\n", file=sys.stderr)
        for e in errors:
            print("  " + e, file=sys.stderr)
        sys.exit(1)
    if not entries:
        sys.exit("ERROR: words.xlsx has no words; words.json was NOT written.")

    # Write to a temp file and swap it in, so a crash never leaves a half-written words.json.
    tmp_path = JSON_PATH + ".tmp"
    with open(tmp_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp_path, JSON_PATH)
    print(f"Wrote {len(entries)} words to words.json")


if __name__ == "__main__":
    build()
