from ingestion_engine import ingest_directory


def main():
    for engine in ("godot", "unreal"):
        ingest_directory(
            data_dir=f"data/{engine}",
            source_type=engine,
        )


if __name__ == "__main__":
    main()