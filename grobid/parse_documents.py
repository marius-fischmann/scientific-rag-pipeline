import json
import re
from pathlib import Path

RESULTS_DIR = Path("grobid/results")
OUTPUT_PATH = Path("grobid/documents.jsonl")

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


def new_section(title):
    return {"section_id": None, "title": title, "paragraphs": [], "subsections": []}


def open_heading(sections, heading):
    if not heading:
        return
    if ROMAN_HEADING.match(heading):
        sections.append(new_section(heading))
    elif LETTER_HEADING.match(heading):
        if not sections:
            sections.append(new_section(None))
        sections[-1]["subsections"].append({"title": heading, "paragraphs": []})
    else:
        sections.append(new_section(heading))


def append_paragraph(sections, paragraph):
    if not sections:
        sections.append(new_section(None))
    section = sections[-1]
    target = section["subsections"][-1] if section["subsections"] else section
    target["paragraphs"].append(paragraph)


def assign_section_ids(sections):
    for index, section in enumerate(sections, start=1):
        section["section_id"] = f"s{index}"


def build_document(data, doc_id):
    biblio = data.get("biblio", {})
    sections = []
    abstract_parts = []

    blocks = [(block, True) for block in biblio.get("abstract", [])]
    blocks += [(block, False) for block in data.get("body_text", [])]

    current_head = None
    for block, is_abstract in blocks:
        text = block["text"]

        # Remove GROBID footnote link tokens such as "Actfoot_1", which are not part of the sentence.
        text = remove_footnote_tokens(text)
        # Remove footnote numbers such as "(3GPP 1 )" because they add noise to embeddings and keyword search.
        text = remove_footnote_numbers(text)
        # Fix the separated first letter of drop caps ("T HE" -> "THE") that GROBID produces for the first word.
        text = fix_drop_cap(text)
        # Collapse the gaps left by the removals above so that the text reads naturally again.
        text = normalize_whitespace(text)

        if is_abstract:
            abstract_parts.append(text)
            continue

        # Open a new section or subsection whenever GROBID's heading changes, so that paragraphs are nested
        # below the correct parent. head_section alone mixes section and subsection levels.
        head = block.get("head_section")
        if head != current_head:
            open_heading(sections, head)
            current_head = head
        append_paragraph(sections, {"paragraph_id": block["id"], "text": text})

    assign_section_ids(sections)
    return {
        "doc_id": doc_id,
        "title": biblio.get("title"),
        "authors": biblio.get("authors", []),
        "year": biblio.get("publication_year"),
        "doi": biblio.get("doi"),
        "abstract": " ".join(abstract_parts),
        "sections": sections,
    }


def main():
    documents = []
    for path in sorted(RESULTS_DIR.glob("*.json")):
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
        documents.append(build_document(data, path.stem))

    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        for document in documents:
            f.write(json.dumps(document, ensure_ascii=False) + "\n")
    print(f"{len(documents)} documents written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
