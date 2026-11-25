from grobid_client.grobid_client import GrobidClient

# Initialize with config file
client = GrobidClient(config_path="grobid/grobid_config.json")

# Process documents from pdf to json in S2ORC like format
def process_documents():
    client.process(
        service="processFulltextDocument",
        input_path="grobid/corpus_documents",
        output="grobid/results",
        consolidate_citations=True,
        include_raw_citations=True,
        force=True,
        n=3,
        json_output=True,
    )

if __name__ == "__main__":
    # Process documents
    process_documents()