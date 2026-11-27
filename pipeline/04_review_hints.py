import json
import re
from collections import Counter
from pathlib import Path

DOCUMENTS_PATH = Path("data/processed/canonical_corpus.jsonl")
LOG_PATH = Path("data/interim/logs/review_hints.log")

NUMBERED_HEADING = re.compile(r"^([IVX]+|[A-Z])\.\s")
COMMON_HEADINGS = {
    "abstract",
    "introduction",
    "background",
    "related work",
    "related works",
    "literature review",
    "motivation",
    "problem statement",
    "preliminaries",
    "methodology",
    "methods",
    "method",
    "approach",
    "proposed approach",
    "proposed method",
    "proposed system",
    "system design",
    "system architecture",
    "architecture",
    "implementation",
    "experimental setup",
    "experiments",
    "evaluation",
    "experimental evaluation",
    "results",
    "results and discussion",
    "discussion",
    "limitations",
    "threats to validity",
    "future work",
    "conclusion",
    "conclusions",
    "conclusion and future work",
    "conclusions and future work",
    "acknowledgment",
    "acknowledgments",
    "acknowledgement",
    "acknowledgements",
    "references",
    "bibliography",
    "appendix",
    "author contributions",
    "funding",
    "data availability",
}
ARTIFACT = re.compile(r"foot_\d|\s\d+\s\)|\(\s|\s\)")
SYMBOL_IN_HEADING = re.compile(r"[%:]")
SHORT_PARAGRAPH_WORDS = 6


def all_paragraphs(section):
    # Formulas are not prose, so text checks would only report noise for them.
    for paragraph in section["paragraphs"]:
        if paragraph["type"] != "formula":
            yield paragraph
    for subsection in section["subsections"]:
        for paragraph in subsection["paragraphs"]:
            if paragraph["type"] != "formula":
                yield paragraph


def check_missing_metadata(document):
    # Missing metadata often only surfaces late, when selecting papers for the benchmark.
    missing = [field for field in ("title", "year", "doi") if not document["metadata"].get(field)]
    if missing:
        return [("missing_metadata", None, f"missing: {', '.join(missing)}")]
    return []


def check_unnumbered_section(document):
    # Headings without a Roman numeral or letter are often figure text or table remnants.
    # Headings with symbols are reported by check_heading_symbols instead, so they are not listed twice.
    hints = []
    for section in document["sections"]:
        title = section["title"] or ""
        if not title or NUMBERED_HEADING.match(title) or title.lower() in COMMON_HEADINGS:
            continue
        if SYMBOL_IN_HEADING.search(title):
            continue
        hints.append(("unnumbered_section", section["section_id"], title))
    return hints


def check_heading_symbols(document):
    # Percent signs or colons in headings often indicate embedded graphics.
    hints = []
    for section in document["sections"]:
        title = section["title"] or ""
        if SYMBOL_IN_HEADING.search(title):
            hints.append(("heading_symbols", section["section_id"], title))
    return hints


def check_duplicate_subsections(document):
    # Duplicate subsection titles within the same section usually mean the structure was misdetected.
    hints = []
    for section in document["sections"]:
        counts = Counter(sub["title"] for sub in section["subsections"])
        for title, count in counts.items():
            if count > 1:
                hints.append(("duplicate_subsection", section["section_id"], f"{title} ({count}x)"))
    return hints


def check_empty_section(document):
    # Empty sections appear when GROBID detects a heading without body text.
    return [
        ("empty_section", section["section_id"], section["title"] or "")
        for section in document["sections"]
        if not section["paragraphs"] and not section["subsections"]
    ]


def check_short_paragraphs(document):
    # Very short paragraphs are often list remnants, figure captions, or line breaks.
    hints = []
    for section in document["sections"]:
        for paragraph in all_paragraphs(section):
            if len(paragraph["text"].split()) < SHORT_PARAGRAPH_WORDS:
                hints.append(("short_paragraph", paragraph["paragraph_id"], paragraph["text"]))
    return hints


def check_lowercase_start(document):
    # Paragraphs starting in lowercase were often split at the wrong position.
    hints = []
    for section in document["sections"]:
        for paragraph in all_paragraphs(section):
            text = paragraph["text"]
            if text and text[0].islower():
                hints.append(("lowercase_start", paragraph["paragraph_id"], text))
    return hints


def check_residual_artifacts(document):
    # Leftovers from cleaning (footnote tokens, brackets with spaces) point to gaps in the parser.
    hints = []
    for section in document["sections"]:
        for paragraph in all_paragraphs(section):
            if ARTIFACT.search(paragraph["text"]):
                hints.append(("residual_artifact", paragraph["paragraph_id"], paragraph["text"]))
    return hints


CHECKS = [
    check_missing_metadata,
    check_unnumbered_section,
    check_heading_symbols,
    check_duplicate_subsections,
    check_empty_section,
    check_short_paragraphs,
    check_lowercase_start,
    check_residual_artifacts,
]


def snippet(text, length=100):
    text = text or ""
    return text if len(text) <= length else text[:length] + "..."


def main():
    with DOCUMENTS_PATH.open(encoding="utf-8") as f:
        documents = [json.loads(line) for line in f]

    lines = []
    total = 0
    for document in documents:
        hints = [hint for check in CHECKS for hint in check(document)]
        if not hints:
            continue
        total += len(hints)
        title = document["metadata"].get("title") or "(no title)"
        lines.append(f"\n== {title} | {document['doc_id']} ({len(hints)} hints)")
        for rule, location, detail in hints:
            lines.append(f"  [{rule}] {location or '-'}: {snippet(detail)}")

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.write_text("\n".join(lines).lstrip("\n") + "\n", encoding="utf-8")
    print(f"{total} hints in {len(documents)} documents, written to {LOG_PATH}")


if __name__ == "__main__":
    main()
