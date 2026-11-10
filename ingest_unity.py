
from pathlib import Path

from ingestion_engine import ingest_directory

DATA_DIR = Path("data/unity")


def ingest_documents():
    """Incrementally ingest Unity documentation into Chroma."""
    return ingest_directory(
        data_dir=DATA_DIR,
        source_type="unity",
    )


if __name__ == "__main__":
    ingest_documents()
