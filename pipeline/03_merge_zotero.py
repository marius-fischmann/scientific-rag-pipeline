import csv
import json
import re
from pathlib import Path

DOCUMENTS_PATH = Path("data/interim/documents.jsonl")
ZOTERO_PATH = Path("data/raw/zotero/zotero_corpus.csv")
OUTPUT_PATH = Path("data/processed/corpus.jsonl")

DOI_PREFIX = re.compile(r"^(https?://(dx\.)?doi\.org/|doi:)", re.IGNORECASE)


def normalize_doi(doi):
    # DOIs kommen in unterschiedlicher Schreibweise vor (Groß/Klein, Präfix); für den Vergleich vereinheitlichen.
    if not doi:
        return None
    return DOI_PREFIX.sub("", doi.strip()).lower()


def normalize_title(title):
    # Titel-Vergleich unabhängig von Groß/Klein, Satzzeichen und Leerzeichen.
    if not title:
        return None
    return re.sub(r"[^a-z0-9]+", "", title.lower()) or None


def format_author(author):
    # Zotero-CSV schreibt "Nachname, Vorname"; korporative Autoren haben kein Komma.
    family, _, given = author.partition(", ")
    return f"{given} {family}" if given else family


def format_authors(field):
    return [format_author(author) for author in field.split(";") if author.strip()]


def zotero_metadata(row):
    year = row["Publication Year"].strip()
    return {
        "zotero_id": row["Key"],
        "title": row["Title"],
        "authors": format_authors(row["Author"]),
        "year": int(year) if year.isdigit() else None,
        "doi": row["DOI"] or None,
        "venue": row["Publication Title"] or None,
        "type": row["Item Type"],
    }


def build_indexes(rows):
    by_doi = {}
    by_title = {}
    for row in rows:
        doi = normalize_doi(row["DOI"])
        if doi:
            by_doi.setdefault(doi, []).append(row)
        title = normalize_title(row["Title"])
        if title:
            by_title.setdefault(title, []).append(row)
    return by_doi, by_title


def match_item(document, by_doi, by_title):
    # Zuerst über die DOI zuordnen; nur wenn keine DOI vorliegt oder sie nicht passt, über den Titel.
    grobid = document["grobid_metadata"]
    for key, index in ((normalize_doi(grobid.get("doi")), by_doi), (normalize_title(grobid.get("title")), by_title)):
        candidates = index.get(key, []) if key else []
        if len(candidates) == 1:
            return candidates[0], None
        if len(candidates) > 1:
            return None, f"mehrdeutig ({len(candidates)} Treffer)"
    return None, "kein Treffer über DOI oder Titel"


def main():
    with DOCUMENTS_PATH.open(encoding="utf-8") as f:
        documents = [json.loads(line) for line in f]
    # utf-8-sig, weil Zotero-CSV mit BOM geschrieben wird.
    with ZOTERO_PATH.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    by_doi, by_title = build_indexes(rows)
    corpus = []
    unmatched = []
    for document in documents:
        row, reason = match_item(document, by_doi, by_title)
        if row is None:
            unmatched.append((document["doc_id"], reason))
            continue
        # Zotero-Abstract ist die Quelle; ohne Zotero-Abstract bleibt der GROBID-Abstract.
        zotero_abstract = row["Abstract Note"].strip()
        corpus.append({
            "doc_id": document["doc_id"],
            "metadata": zotero_metadata(row),
            "abstract": zotero_abstract or document["abstract"],
            "abstract_source": "zotero" if zotero_abstract else "grobid",
            "sections": document["sections"],
            "grobid_metadata": document["grobid_metadata"],
        })

    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        for entry in corpus:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"{len(corpus)} von {len(documents)} Dokumenten zugeordnet, geschrieben nach {OUTPUT_PATH}")
    for doc_id, reason in unmatched:
        print(f"  nicht zugeordnet: {doc_id[:60]} ({reason})")


if __name__ == "__main__":
    main()
