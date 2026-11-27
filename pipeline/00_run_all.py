import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PIPELINE_DIR = Path(__file__).resolve().parent
STEPS = [
    "01_extract_grobid.py",
    "02_parse_documents.py",
    "03_merge_zotero.py",
    "04_review_hints.py",
]


def main():
    for step in STEPS:
        print(f"== running {step}")
        # Scripts use paths relative to the repository root.
        subprocess.run([sys.executable, str(PIPELINE_DIR / step)], cwd=REPO_ROOT, check=True)
    print("pipeline finished")


if __name__ == "__main__":
    main()
