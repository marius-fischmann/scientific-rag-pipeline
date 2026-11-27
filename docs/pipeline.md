# Korpus-Pipeline

Die Pipeline erzeugt aus den PDFs die kanonische Darstellung des Korpus (`data/processed/corpus.jsonl`). Sie führt keine RAG-Schritte aus.

```mermaid
flowchart LR
    subgraph raw["data/raw (Eingabe)"]
        pdfs["pdfs/*.pdf"]
        zot["zotero/zotero_corpus.csv"]
    end

    grobid["GROBID-Server<br/>(docker/compose.yaml)"]
    s1["01_extract_grobid.py"]
    s2["02_parse_documents.py"]
    s3["03_merge_zotero.py"]
    s4["04_review_hints.py"]

    subgraph interim["data/interim (Zwischenstand)"]
        tei["grobid/*.json<br/>(rohe GROBID-Ausgabe)"]
        docs["documents.jsonl<br/>(bereinigter Text, GROBID-Metadaten)"]
    end

    subgraph processed["data/processed (Ergebnis)"]
        corpus["corpus.jsonl<br/>(Text + Zotero-Metadaten)"]
    end

    hints["Konsole: Prüfhinweise<br/>(ändern keine Daten)"]

    pdfs --> s1
    s1 -->|HTTP| grobid
    grobid --> s1
    s1 --> tei
    tei --> s2 --> docs
    docs --> s3
    zot --> s3
    s3 --> corpus
    corpus --> s4 --> hints
```

## Schritte

| Skript | Eingabe | Ausgabe | Zweck |
|---|---|---|---|
| `pipeline/01_extract_grobid.py` | `data/raw/pdfs/` | `data/interim/grobid/` | PDFs über GROBID in strukturiertes JSON umwandeln. GROBID macht nur Text- und Strukturextraktion. |
| `pipeline/02_parse_documents.py` | `data/interim/grobid/` | `data/interim/documents.jsonl` | Text bereinigen, Abschnittshierarchie ableiten, stabile `paragraph_id`s vergeben. |
| `pipeline/03_merge_zotero.py` | `data/interim/documents.jsonl`, `data/raw/zotero/zotero_corpus.csv` | `data/processed/corpus.jsonl` | Bibliografische Metadaten und Abstracts aus Zotero übernehmen. Zuordnung über DOI, sonst normalisierter Titel. |
| `pipeline/04_review_hints.py` | `data/processed/corpus.jsonl` | Konsole | Stellen markieren, die manuell geprüft werden sollten. Die Daten bleiben unverändert. |

Die Skripte laufen aus dem Repository-Wurzelverzeichnis, weil die Pfade relativ sind.

## Ausführung

```bash
docker compose -f docker/compose.yaml up -d
source .venv/bin/activate
python pipeline/01_extract_grobid.py
python pipeline/02_parse_documents.py
python pipeline/03_merge_zotero.py
python pipeline/04_review_hints.py
```

## Datenordner

`data/` ist vollständig in `.gitignore` eingetragen. Die Dateien enthalten Volltext und Metadaten aus fremden Veröffentlichungen. Die Skripte erzeugen alles neu, sodass nichts Eigenes verloren geht. Die Ausnahme bildet der Zotero-Export: Er muss manuell neu aus Zotero exportiert werden.
