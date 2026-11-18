"""Validate the Unity/Godot Chroma database before deployment."""

import os
from collections import Counter
from pathlib import Path

import chromadb


EXPECTED_ENGINES = {"unity", "godot"}


def validate_database(db_dir=None):
    db_dir = Path(
        db_dir or os.getenv(
            "CHROMA_DB_DIR",
            "./chroma_unity_test",
        )
    )

    if not (db_dir / "chroma.sqlite3").is_file():
        raise RuntimeError(f"Chroma database not found: {db_dir}")

    client = chromadb.PersistentClient(path=str(db_dir))
    collection = client.get_collection("langchain")

    total = collection.count()
    counts = Counter()
    missing_urls = 0
    missing_hashes = 0

    for offset in range(0, total, 500):
        batch = collection.get(
            limit=500,
            offset=offset,
            include=["metadatas"],
        )

        for metadata in batch["metadatas"]:
            metadata = metadata or {}
            counts[metadata.get("source_type", "unknown")] += 1

            if not metadata.get("source_url"):
                missing_urls += 1

            if not metadata.get("content_hash"):
                missing_hashes += 1

    print("Total chunks:", total)
    print("Chunks by engine:", dict(counts))
    print("Missing source URLs:", missing_urls)
    print("Missing content hashes:", missing_hashes)

    missing_engines = EXPECTED_ENGINES - {
        engine for engine, count in counts.items() if count > 0
    }

    if total == 0:
        raise RuntimeError("Database is empty")

    if missing_engines:
        raise RuntimeError(
            f"Missing documentation engines: {sorted(missing_engines)}"
        )

    if missing_urls or missing_hashes:
        raise RuntimeError(
            "Database contains chunks with missing source metadata"
        )

    print("PASS: Ludex Chroma database validated.")


if __name__ == "__main__":
    validate_database()
