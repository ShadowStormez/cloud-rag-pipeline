
import os
import tarfile
import tempfile
from pathlib import Path

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient


STORAGE_ACCOUNT = "cloudragstorearya26"
CONTAINER_NAME = "chroma-snapshots"
BLOB_NAME = os.getenv(
    "CHROMA_BLOB_NAME",
    "chroma-unity-snapshot-clean.tar.gz",
)

# Use a separate directory during our first test.
RESTORE_DIR = Path(
    os.getenv("CHROMA_DB_DIR", "./chroma_restore_test")
)


def restore_chroma():
    if RESTORE_DIR.exists():
        if (RESTORE_DIR / "chroma.sqlite3").is_file():
            print(
                f"Existing Chroma database found at {RESTORE_DIR}. "
                "Skipping restoration.",
                flush=True,
            )
            return

        raise RuntimeError(
            f"Restore destination exists but has no Chroma database: "
            f"{RESTORE_DIR}"
        )

    account_url = f"https://{STORAGE_ACCOUNT}.blob.core.windows.net"

    credential = DefaultAzureCredential(
        exclude_interactive_browser_credential=True
    )

    try:
        service = BlobServiceClient(
            account_url=account_url,
            credential=credential,
        )

        blob = service.get_blob_client(
            container=CONTAINER_NAME,
            blob=BLOB_NAME,
        )

        RESTORE_DIR.parent.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory(
            dir=RESTORE_DIR.parent
        ) as temp_dir:
            archive = Path(temp_dir) / "snapshot.tar.gz"
            staging = Path(temp_dir) / "extracted"
            staging.mkdir()

            print("Downloading Chroma snapshot...", flush=True)

            with archive.open("wb") as file:
                stream = blob.download_blob()
                stream.readinto(file)

            print("Validating and extracting snapshot...", flush=True)

            with tarfile.open(archive, "r:gz") as tar:
                members = tar.getmembers()

                if not members:
                    raise ValueError("Snapshot archive is empty")

                for member in members:
                    path = Path(member.name)

                    if (
                        path.is_absolute()
                        or ".." in path.parts
                        or not (
                            path.parts
                            and path.parts[0] == "chroma_unity_test"
                        )
                        or not (member.isfile() or member.isdir())
                    ):
                        raise ValueError(
                            f"Unsafe archive member: {member.name}"
                        )

                tar.extractall(
                    path=staging,
                    filter="data",
                )

            source = staging / "chroma_unity_test"

            if not (source / "chroma.sqlite3").is_file():
                raise ValueError("Snapshot is missing chroma.sqlite3")

            # Atomically move the restored database into place.
            os.rename(source, RESTORE_DIR)

        print(f"Chroma restored successfully to {RESTORE_DIR}")

    finally:
        credential.close()


if __name__ == "__main__":
    restore_chroma()
