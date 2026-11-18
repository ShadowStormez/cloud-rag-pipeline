"""Incrementally ingest downloaded Unity and Godot documentation."""

import os
from pathlib import Path

from ingestion_engine import ingest_directory


def main():
    db_dir = os.getenv(
        "CHROMA_DB_DIR",
        "./chroma_ludex_combined_test",
    )

    for engine in ("unity", "godot"):
        data_dir = Path("data/automatic") / engine

        if not data_dir.is_dir():
            raise FileNotFoundError(
                f"Documentation directory not found: {data_dir}"
            )

        if not (data_dir / "sources.json").is_file():
            raise FileNotFoundError(
                f"Documentation manifest not found: {data_dir}"
            )

        print(f"\n=== Ingesting {engine.upper()} ===", flush=True)

        ingest_directory(
            data_dir=data_dir,
            source_type=engine,
            db_dir=db_dir,
        )

    print("\nLudex documentation ingestion completed.")


if __name__ == "__main__":
    main()
