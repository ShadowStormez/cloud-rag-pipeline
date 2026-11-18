"""Normalize legacy Unity source paths in an existing Chroma database."""

import os
from pathlib import Path

from chromadb import PersistentClient


OLD_PREFIX = "data/ludex_ingestion_snapshot/unity/"
NEW_PREFIX = "data/automatic/unity/"


def normalize_sources(db_dir: str, batch_size: int = 500):
    collection = PersistentClient(
        path=db_dir
    ).get_collection("langchain")

    original_count = collection.count()
    updated_records = 0
    updated_sources = set()

    for offset in range(0, original_count, batch_size):
        batch = collection.get(
            limit=batch_size,
            offset=offset,
            include=["metadatas"],
        )

        ids = []
        metadatas = []

        for record_id, metadata in zip(
            batch["ids"], batch["metadatas"]
        ):
            source = metadata.get("source", "")

            if not source.startswith(OLD_PREFIX):
                continue

            new_source = NEW_PREFIX + source[len(OLD_PREFIX):]

            if not Path(new_source).is_file():
                raise FileNotFoundError(
                    f"Matching documentation not found: {new_source}"
                )

            updated_metadata = dict(metadata)
            updated_metadata["source"] = new_source

            ids.append(record_id)
            metadatas.append(updated_metadata)
            updated_sources.add(source)

        if ids:
            collection.update(
                ids=ids,
                metadatas=metadatas,
            )
            updated_records += len(ids)

    if collection.count() != original_count:
        raise RuntimeError("Chunk count changed during normalization.")

    print(f"Normalized sources: {len(updated_sources)}")
    print(f"Updated metadata records: {updated_records}")
    print(f"Total chunks preserved: {original_count}")


if __name__ == "__main__":
    db_dir = os.getenv("CHROMA_DB_DIR")

    if not db_dir:
        raise RuntimeError(
            "Set CHROMA_DB_DIR explicitly before running normalization."
        )

    normalize_sources(db_dir)
