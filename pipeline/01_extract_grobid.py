from pathlib import Path

from grobid_client.grobid_client import GrobidClient

# Initialize with config file
client = GrobidClient(config_path="pipeline/grobid_config.json")

# Process documents from pdf to json in S2ORC like format
def process_documents():
    pdf_paths = sorted(Path("data/raw/pdfs").glob("*.pdf"))[:3]
    client.process_paths(
        service="processFulltextDocument",
        inputs=[str(path) for path in pdf_paths],
        output="data/interim/grobid",
        consolidate_header=True,
        consolidate_citations=True,
        include_raw_citations=True,
        force=True,
        json_output=True,
    )

if __name__ == "__main__":
    # Process documents
    process_documents()