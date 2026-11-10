
import os
import tarfile
from pathlib import Path

DB_DIR = Path(os.getenv("CHROMA_DB_DIR", "./chroma_unity_test"))
SNAPSHOT_PATH = Path(
    os.getenv("CHROMA_SNAPSHOT_PATH", "./chroma-snapshot.tar.gz")
)

# restore_chroma.py expects this directory name inside the archive.
ARCHIVE_ROOT = "chroma_unity_test"


def create_snapshot():
    """Create a compressed snapshot of the Chroma database."""

    if not (DB_DIR / "chroma.sqlite3").is_file():
        raise FileNotFoundError(
            f"Chroma database not found at {DB_DIR}"
        )

    SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)

    print(f"Creating snapshot from {DB_DIR}...")

    with tarfile.open(SNAPSHOT_PATH, "w:gz") as archive:
        archive.add(
            DB_DIR,
            arcname=ARCHIVE_ROOT,
        )

    print(f"Snapshot created: {SNAPSHOT_PATH}")
    print(f"Snapshot size: {SNAPSHOT_PATH.stat().st_size:,} bytes")


if __name__ == "__main__":
    create_snapshot()
