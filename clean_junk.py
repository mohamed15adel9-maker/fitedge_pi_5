"""
clean_junk.py

Finds every .txt file under rag/ that contains bot-block / reCAPTCHA text
and DELETES it. Run from the project root:

    python clean_junk.py
"""

import os
from pathlib import Path

RAG_DIR = Path("./rag")

BLOCK_MARKERS = [
    "checking your browser",
    "recaptcha",
    "enable javascript",
    "are you a robot",
    "click here if you are not automatically redirected",
    "pmc.ncbi.nlm.nih.gov",
]


def is_junk(text):
    low = text.lower()
    return any(m in low for m in BLOCK_MARKERS)


def main():
    if not RAG_DIR.exists():
        print("No rag/ folder found. Run this from your project root.")
        return

    deleted = []
    kept = 0

    for path in RAG_DIR.rglob("*.txt"):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            print(f"  could not read {path}: {e}")
            continue

        if is_junk(text):
            path.unlink()                     # DELETE the junk file
            deleted.append(str(path))
            print(f"DELETED junk: {path}")
        else:
            kept += 1

    print("\n" + "=" * 50)
    print(f"Deleted {len(deleted)} junk file(s). Kept {kept} clean file(s).")
    print("=" * 50)
    if deleted:
        print("\nDeleted files:")
        for d in deleted:
            print("  -", d)


if __name__ == "__main__":
    main()
