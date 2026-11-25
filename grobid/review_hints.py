import json
import re
from collections import Counter
from pathlib import Path

DOCUMENTS_PATH = Path("grobid/documents.jsonl")

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
SHORT_PARAGRAPH_WORDS = 6


def all_paragraphs(section):
    yield from section["paragraphs"]
    for subsection in section["subsections"]:
        yield from subsection["paragraphs"]


def check_missing_metadata(document):
    # Fehlende Metadaten fallen bei der Auswahl für den Benchmark oft erst spät auf.
    missing = [field for field in ("title", "year", "doi") if not document.get(field)]
    if missing:
        return [("missing_metadata", None, f"fehlt: {', '.join(missing)}")]
    return []


def check_unnumbered_section(document):
    # Überschriften ohne römische Zahl oder Buchstabe sind oft Abbildungstext oder Tabellenreste.
    hints = []
    for section in document["sections"]:
        title = section["title"] or ""
        if not title or NUMBERED_HEADING.match(title) or title.lower() in COMMON_HEADINGS:
            continue
        hints.append(("unnumbered_section", section["section_id"], title))
    return hints


def check_heading_symbols(document):
    # Prozentzeichen oder Doppelpunkte in Überschriften deuten auf eingebettete Grafiken hin.
    hints = []
    for section in document["sections"]:
        title = section["title"] or ""
        if re.search(r"[%:]", title):
            hints.append(("heading_symbols", section["section_id"], title))
    return hints


def check_duplicate_subsections(document):
    # Doppelte Unterabschnitts-Titel in derselben Section sind meist eine falsch erkannte Gliederung.
    hints = []
    for section in document["sections"]:
        counts = Counter(sub["title"] for sub in section["subsections"])
        for title, count in counts.items():
            if count > 1:
                hints.append(("duplicate_subsection", section["section_id"], f"{title} ({count}x)"))
    return hints


def check_empty_section(document):
    # Leere Sections entstehen, wenn GROBID eine Überschrift ohne Fließtext erkennt.
    return [
        ("empty_section", section["section_id"], section["title"] or "")
        for section in document["sections"]
        if not section["paragraphs"] and not section["subsections"]
    ]


def check_short_paragraphs(document):
    # Sehr kurze Absätze sind häufig Listenreste, Bildbeschriftungen oder Zeilenumbrüche.
    hints = []
    for section in document["sections"]:
        for paragraph in all_paragraphs(section):
            if len(paragraph["text"].split()) < SHORT_PARAGRAPH_WORDS:
                hints.append(("short_paragraph", paragraph["paragraph_id"], paragraph["text"]))
    return hints


def check_lowercase_start(document):
    # Absätze, die klein anfangen, wurden oft an einer falschen Stelle getrennt.
    hints = []
    for section in document["sections"]:
        for paragraph in all_paragraphs(section):
            text = paragraph["text"]
            if text and text[0].islower():
                hints.append(("lowercase_start", paragraph["paragraph_id"], text))
    return hints


def check_residual_artifacts(document):
    # Reste der Bereinigung (Fußnoten-Tokens, Klammern mit Leerzeichen) sind Hinweise auf Lücken im Parser.
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

    total = 0
    for document in documents:
        hints = [hint for check in CHECKS for hint in check(document)]
        if not hints:
            continue
        total += len(hints)
        print(f"\n== {document['doc_id']} ({len(hints)} Hinweise)")
        for rule, location, detail in hints:
            print(f"  [{rule}] {location or '-'}: {snippet(detail)}")
    print(f"\n{total} Hinweise in {len(documents)} Dokumenten")


if __name__ == "__main__":
    main()
