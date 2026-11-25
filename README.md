# scientific-rag-pipeline
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