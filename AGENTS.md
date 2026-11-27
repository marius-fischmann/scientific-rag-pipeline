# AGENTS.md

Rules for changes in this repository. The goal is a uniform codebase with clear patterns.

## Scope

This repository builds the canonical corpus for a RAG benchmark: PDF → GROBID → parsing → Zotero merge → `canonical_corpus.jsonl`. Chunking, retrieval, and evaluation do not belong here.

## Execution

- Always run scripts from the repository root, because all paths are relative to it.
- Install dependencies with `uv sync` and add new ones with `uv add <package>`. Dependencies are declared in `pyproject.toml` and pinned in `uv.lock`. Only add a dependency after consulting the user.
- Run Python via `uv run python <script>` or `.venv/bin/python`. System pip is blocked by PEP 668.
- Run the pipeline steps in this order: `01_extract_grobid.py`, `02_parse_documents.py`, `03_merge_zotero.py`, `04_review_hints.py`. `00_run_all.py` runs all four in this order.

## Structure of a pipeline script

- Paths are `Path` constants in UPPER_CASE directly below the imports. No path is written inline in the code.
- Logic lives in functions. The entry point is always `def main()`, called via `if __name__ == "__main__": main()`.
- Two blank lines between top-level definitions.
- Magic values (e.g. limits) are defined as named constants.

## Data

- `data/raw/` is the unchanged input and is never overwritten.
- `data/interim/` contains intermediate results.
- `data/processed/` contains final results.
- `data/` is fully listed in `.gitignore`. Data is not committed.
- Output files get descriptive names (`canonical_corpus.jsonl`, `parsed_documents.jsonl`), not generic ones like `output.json`.

## Language

- Everything is in English: comments, docstrings, console output, and identifiers.
- Documentation (`docs/`, `AGENTS.md`) is in English as well.

## Comments

- Only comment code that needs explanation, such as the reason for a rule or a non-obvious data source.
- No comments that merely repeat what the code already says.

## Dependencies and documentation

- Add new dependencies only after consulting the user.
- If a path, a command, or the flow changes, `docs/pipeline.md` and `README.md` must be updated in the same step.
- Design decisions belong in the notes, not in the code.

## Verification before finishing

- After every script change, run the step and check the output. Before and after should produce identical results, unless the behavior was changed on purpose.
