import os
from pathlib import Path

from grobid_client.grobid_client import GrobidClient

CONFIG_PATH = Path("pipeline/grobid_config.json")
GROBID_SERVER = os.environ.get("GROBID_SERVER", "http://localhost:8071")
PDF_DIR = Path("data/raw/pdfs")
RESULTS_DIR = Path("data/interim/grobid")
# Only process the first PDFs for now, so the results can be reviewed early.
PDF_LIMIT = 20
# Low concurrency: with 10 parallel requests GROBID exceeded the client timeout.
CONCURRENCY = 2


def main():
    client = GrobidClient(grobid_server=GROBID_SERVER, config_path=str(CONFIG_PATH))
    pdf_paths = sorted(PDF_DIR.glob("*.pdf"))[:PDF_LIMIT]
    # Remove old results so a failed document cannot silently keep its previous output.
    for path in pdf_paths:
        for suffix in (".json", ".grobid.tei.xml"):
            (RESULTS_DIR / f"{path.stem}{suffix}").unlink(missing_ok=True)
    client.process_paths(
        service="processFulltextDocument",
        inputs=[str(path) for path in pdf_paths],
        output=str(RESULTS_DIR),
        n=CONCURRENCY,
        consolidate_header=False,
        consolidate_citations=False,
        include_raw_citations=True,
        force=True,
        json_output=True,
    )
    missing = [path.name for path in pdf_paths if not (RESULTS_DIR / f"{path.stem}.json").exists()]
    if missing:
        raise RuntimeError(f"GROBID produced no output for {len(missing)} PDF(s): {', '.join(missing)}")
    print(f"{len(pdf_paths)} PDFs processed into {RESULTS_DIR}")


if __name__ == "__main__":
    main()
