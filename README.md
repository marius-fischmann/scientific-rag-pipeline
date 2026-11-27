# scientific-rag-pipeline

Builds the canonical corpus for a RAG benchmark on scientific full-text papers. The pipeline converts PDFs into a clean, structured representation with bibliographic metadata from Zotero. It does not perform any RAG steps (chunking, retrieval, evaluation).

## Repository layout

```
docker/compose.yaml      GROBID server (Docker)
pipeline/                numbered pipeline scripts and the GROBID client config
docs/pipeline.md         pipeline diagram, steps, and run commands
data/                    raw input, intermediate and final results (git-ignored)
AGENTS.md                coding and structure rules for this repository
```

## Setup

### 1. Start GROBID

GROBID runs as a Docker service defined in [docker/compose.yaml](docker/compose.yaml):

```bash
docker compose -f docker/compose.yaml up -d
```

The service is then available at `http://localhost:8070`.

The `grobid-full` service (Deep Learning models, about 8 GB) is commented out in the same file. To use it, uncomment the service block, start it with `docker compose -f docker/compose.yaml up -d grobid-full`, and run the pipeline with:

```bash
GROBID_SERVER=http://localhost:8071 python pipeline/01_extract_grobid.py
```

The full image runs on the CPU without a GPU, but is slower and needs more RAM. The compose file does not request a GPU, so it works on machines without an NVIDIA card.

### 2. Install the Python dependencies

The project uses [uv](https://docs.astral.sh/uv/) to manage Python and its dependencies. `uv sync` creates `.venv/` and installs everything pinned in `uv.lock`, including the GROBID client:

```bash
uv sync
```

Client documentation: https://github.com/grobidOrg/grobid-client-python

## Pipeline

Run the whole chain from the repository root (GROBID must be running):

```bash
uv run python pipeline/00_run_all.py
```

Or run the steps individually, in this order:

```bash
uv run python pipeline/01_extract_grobid.py
uv run python pipeline/02_parse_documents.py
uv run python pipeline/03_merge_zotero.py
uv run python pipeline/04_review_hints.py
```

| Script | Output |
|---|---|
| `00_run_all.py` | runs steps 01 to 04 in order, stops on the first error |
| `01_extract_grobid.py` | `data/interim/grobid/` (raw GROBID TEI/JSON) |
| `02_parse_documents.py` | `data/interim/parsed_documents.jsonl` |
| `03_merge_zotero.py` | `data/processed/canonical_corpus.jsonl` |
| `04_review_hints.py` | `data/interim/logs/review_hints.log` (hints to check manually) |

Inputs: PDFs in `data/raw/pdfs/` and the Zotero export `data/raw/zotero/zotero_corpus.csv` (CSV export including `Abstract Note`).

Details, the flow diagram, and the data policy are in [docs/pipeline.md](docs/pipeline.md). Coding rules are in [AGENTS.md](AGENTS.md).
