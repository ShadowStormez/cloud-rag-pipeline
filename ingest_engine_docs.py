import argparse

from ingestion_engine import ingest_directory


def main():
    parser = argparse.ArgumentParser(
        description="Ingest Unity or Godot documentation into Chroma."
    )

    parser.add_argument(
        "--engine",
        choices=("unity", "godot"),
        required=True,
    )

    parser.add_argument(
        "--data-dir",
        required=True,
        help="Directory containing documentation .txt files and sources.json",
    )

    args = parser.parse_args()

    ingest_directory(
        data_dir=args.data_dir,
        source_type=args.engine,
    )


if __name__ == "__main__":
    main()