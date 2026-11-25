import json
import re
from pathlib import Path

RESULTS_DIR = Path("grobid/results")
OUTPUT_PATH = Path("grobid/paragraphs.jsonl")

FOOTNOTE_TOKEN = re.compile(r"foot_\d+")
FOOTNOTE_NUMBER = re.compile(r"(?P<word>[A-Za-z]+)\s\d{1,2}\s+(?=[).,;])")
NUMBER_REFERENCE_WORDS = {"Table", "Figure", "Fig", "Section", "Sec", "Eq", "Algorithm", "Step"}
SPACE_BEFORE_PUNCTUATION = re.compile(r"\s+([,.;:)])")
DROP_CAP = re.compile(r"^([A-Z]) ([A-Z]{2,})\b")
ROMAN_HEADING = re.compile(r"^[IVX]+\.\s")
LETTER_HEADING = re.compile(r"^[A-Z]\.\s")


def remove_footnote_tokens(text):
    return FOOTNOTE_TOKEN.sub("", text)


def remove_footnote_numbers(text):
    def _strip(match):
        if match.group("word") in NUMBER_REFERENCE_WORDS:
            return match.group(0)
        return match.group("word")

    return FOOTNOTE_NUMBER.sub(_strip, text)


def fix_drop_cap(text):
    return DROP_CAP.sub(lambda m: m.group(1) + m.group(2), text)


def normalize_whitespace(text):
    text = SPACE_BEFORE_PUNCTUATION.sub(r"\1", text)
    return " ".join(text.split())


def update_section_state(heading, section, subsection):
    if not heading:
        return section, subsection
    if ROMAN_HEADING.match(heading):
        return heading, None
    if LETTER_HEADING.match(heading):
        return section, heading
    return heading, None


def build_records(data, doc_id):
    records = []
    section = None
    subsection = None
    blocks = [{**block, "head_section": "Abstract"} for block in data.get("biblio", {}).get("abstract", [])]
    blocks += data.get("body_text", [])

    for block in blocks:
        text = block["text"]

        # Remove GROBID footnote link tokens such as "Actfoot_1", which are not part of the sentence.
        text = remove_footnote_tokens(text)
        # Remove footnote numbers such as "(3GPP 1 )" because they add noise to embeddings and keyword search.
        text = remove_footnote_numbers(text)
        # Fix the separated first letter of drop caps ("T HE" -> "THE") that GROBID produces for the first word.
        text = fix_drop_cap(text)
        # Collapse the gaps left by the removals above so that the text reads naturally again.
        text = normalize_whitespace(text)
        # Keep section and subsection separate, because head_section alone mixes both levels.
        section, subsection = update_section_state(block.get("head_section"), section, subsection)

        records.append({
            "doc_id": doc_id,
            "paragraph_id": block["id"],
            "section": section,
            "subsection": subsection,
            "text": text,
        })
    return records


def main():
    records = []
    for path in sorted(RESULTS_DIR.glob("*.json")):
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
        records.extend(build_records(data, path.stem))

    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"{len(records)} paragraphs written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
