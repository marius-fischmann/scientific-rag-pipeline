import hashlib
import json
import re
import uuid
from pathlib import Path

RESULTS_DIR = Path("data/interim/grobid")
PDF_DIR = Path("data/raw/pdfs")
OUTPUT_PATH = Path("data/interim/parsed_documents.jsonl")
# Fixed namespace for deterministic doc_ids; changing it changes every ID.
DOC_ID_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, "https://github.com/marius-fischmann/scientific-rag-pipeline")

FOOTNOTE_TOKEN = re.compile(r"foot_\d+")
FOOTNOTE_NUMBER = re.compile(r"(?P<word>[A-Za-z]+)\s\d{1,2}\s+(?=[).,;])")
NUMBER_REFERENCE_WORDS = {"Table", "Figure", "Fig", "Section", "Sec", "Eq", "Algorithm", "Step"}
SPACE_BEFORE_PUNCTUATION = re.compile(r"\s+([,.;:)])")
DROP_CAP = re.compile(r"^([A-Z]) ([A-Z]{2,})\b")
ROMAN_HEADING = re.compile(r"^[IVX]+\.\s")
LETTER_HEADING = re.compile(r"^[A-Z]\.\s")
# Captions are "Table 2." or "Figure 3:" followed by text; running sentences like "Figure 1 illustrates" do not match.
CAPTION_START = re.compile(r"^(Table|Figure|Fig\.)\s*\d+[.:]\s")
LIST_MARKER = re.compile(r"^(?:[•▪■–-]|o)\s+")
OPENING_BRACKET_SPACE = re.compile(r"\(\s+")


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
    text = OPENING_BRACKET_SPACE.sub("(", text)
    return " ".join(text.split())


def paragraph_type(block, text):
    if block.get("type") == "formula":
        return "formula"
    if CAPTION_START.match(text):
        return "caption"
    return "text"


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


def doc_id_for_pdf(pdf_path):
    content_hash = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
    return str(uuid.uuid5(DOC_ID_NAMESPACE, content_hash))


def build_document(data, doc_id, source_file):
    biblio = data.get("biblio", {})
    sections = []
    abstract_parts = []

    blocks = [(block, True) for block in biblio.get("abstract", [])]
    blocks += [(block, False) for block in data.get("body_text", [])]

    current_head = None
    for block, is_abstract in blocks:
        text = block["text"]

        # GROBID appends footnote link tokens such as "foot_1" to words.
        text = remove_footnote_tokens(text)
        text = remove_footnote_numbers(text)
        # GROBID separates the first letter of drop caps ("T HE" -> "THE").
        text = fix_drop_cap(text)
        text = normalize_whitespace(text)
        # Bullet glyphs become list text without a marker; blocks with no letters or digits (e.g. "•", ")") are dropped.
        text = LIST_MARKER.sub("", text)
        if not re.search(r"\w", text):
            continue

        if is_abstract:
            abstract_parts.append(text)
            continue

        # head_section mixes section and subsection levels, so only open a new heading when it changes.
        head = block.get("head_section")
        if head != current_head:
            open_heading(sections, head)
            current_head = head
        append_paragraph(sections, {"paragraph_id": block["id"], "type": paragraph_type(block, text), "text": text})

    assign_section_ids(sections)
    return {
        "doc_id": doc_id,
        "source_file": source_file,
        "grobid_metadata": {
            "title": biblio.get("title"),
            "authors": biblio.get("authors", []),
            "year": biblio.get("publication_year"),
            "doi": biblio.get("doi"),
        },
        "abstract": " ".join(abstract_parts),
        "sections": sections,
    }


def main():
    documents = []
    for path in sorted(RESULTS_DIR.glob("*.json")):
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
        pdf_path = PDF_DIR / f"{path.stem}.pdf"
        documents.append(build_document(data, doc_id_for_pdf(pdf_path), pdf_path.name))

    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        for document in documents:
            f.write(json.dumps(document, ensure_ascii=False) + "\n")
    print(f"{len(documents)} documents written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
