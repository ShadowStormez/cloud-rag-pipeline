
import os
from collections import Counter

import chromadb


EXPECTED_ENGINES = {"unity", "godot", "unreal"}


def validate_database(db_dir=None):
    db_dir = db_dir or os.getenv(
        "CHROMA_DB_DIR", "./chroma_unity_test"
    )

    client = chromadb.PersistentClient(path=db_dir)
    collection = client.get_collection("langchain")

    records = collection.get(include=["metadatas"])

    counts = Counter(
        metadata.get("source_type", "legacy")
        for metadata in records["metadatas"]
    )

    print(f"Total chunks: {collection.count()}")
    print(f"Chunks by engine: {dict(counts)}")

    missing = EXPECTED_ENGINES - {
        engine for engine, count in counts.items() if count > 0
    }

    if missing:
        raise RuntimeError(
            f"Missing documentation engines: {sorted(missing)}"
        )

    print("Multi-engine database validation passed!")


if __name__ == "__main__":
    validate_database()
