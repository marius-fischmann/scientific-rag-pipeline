# scientific-rag-pipeline

## Setup

### Start GROBID

GROBID runs as a Docker service defined in [docker/compose.yaml](docker/compose.yaml). Start it with:

```bash
docker compose -f docker/compose.yaml up -d
```

The service is then available at `http://localhost:8070`.

### Install the GROBID Python client

Create a virtual environment first (system-wide `pip install` is blocked on Debian/Ubuntu, see PEP 668):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install grobid-client-python
```

If `python3 -m venv` fails with an `ensurepip` error, install `python3.12-venv` via `sudo apt install python3.12-venv`.

Usage and documentation: https://github.com/grobidOrg/grobid-client-python

scientific-retrieval-benchmark/
│
├── datasets/
│   ├── qasper/
│   │
│   └── custom_scientific_corpus/
│       ├── corpus/
│       │   ├── documents.jsonl
│       │   └── raw/
│       │
│       ├── queries/
│       │   └── queries.jsonl
│       │
│       ├── ground_truth/
│       │   ├── evidence.jsonl
│       │   └── qrels.jsonl
│       │
│       └── dataset_metadata.yaml
│
├── src/
│   ├── ingestion/
│   │   ├── parsers/
│   │   └── preprocessing/
│   │
│   ├── chunking/
│   ├── embeddings/
│   ├── retrieval/
│   │
│   └── evaluation/
│       ├── metrics/
│       └── evaluator.py
│
├── configs/
│   ├── chunking/
│   ├── embeddings/
│   └── retrieval/
│
├── experiments/
│
├── tests/
│
└── README.md