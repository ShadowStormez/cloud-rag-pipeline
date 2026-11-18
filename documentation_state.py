"""Manage persistent Ludex documentation state in Azure Blob Storage."""

import argparse
import os
import tarfile
import tempfile
from pathlib import Path

from azure.core import MatchConditions
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient


ACCOUNT = "cloudragstorearya26"
CONTAINER = "chroma-snapshots"
BLOB = "ludex-documentation-state.tar.gz"

ARCHIVE_PATH = Path("ludex-documentation-state.tar.gz")

DIRECTORIES = (
    Path("data/discovery"),
    Path("data/automatic/unity"),
    Path("data/automatic/godot"),
)


def create_archive():
    with tarfile.open(ARCHIVE_PATH, "w:gz") as archive:
        for directory in DIRECTORIES:
            if not directory.is_dir():
                raise FileNotFoundError(directory)

            archive.add(directory, arcname=directory.as_posix())

    print(f"Created {ARCHIVE_PATH}")


def safe_extract(archive_path):
    with tarfile.open(archive_path, "r:gz") as archive:
        for member in archive.getmembers():
            path = Path(member.name)

            if (
                path.is_absolute()
                or ".." in path.parts
                or not member.name.startswith("data/")
                or not (member.isfile() or member.isdir())
                or not any(
                    path == directory
                    or directory in path.parents
                    or path in directory.parents
                    for directory in DIRECTORIES
                )
            ):
                raise ValueError(f"Unsafe archive member: {member.name}")

        archive.extractall(".", filter="data")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "action",
        choices=("upload", "download", "status"),
    )
    args = parser.parse_args()

    credential = DefaultAzureCredential(
        exclude_interactive_browser_credential=True
    )

    try:
        service = BlobServiceClient(
            account_url=f"https://{ACCOUNT}.blob.core.windows.net",
            credential=credential,
        )
        blob = service.get_blob_client(CONTAINER, BLOB)

        if args.action == "status":
            if blob.exists():
                props = blob.get_blob_properties()
                print(f"Blob: {BLOB}")
                print(f"Size: {props.size:,} bytes")
                print(f"ETag: {props.etag}")
            else:
                print("Documentation state archive not uploaded yet.")

        elif args.action == "upload":
            create_archive()

            if blob.exists():
                etag = blob.get_blob_properties().etag
                with ARCHIVE_PATH.open("rb") as file:
                    blob.upload_blob(
                        file,
                        overwrite=True,
                        etag=etag,
                        match_condition=MatchConditions.IfNotModified,
                    )
            else:
                with ARCHIVE_PATH.open("rb") as file:
                    blob.upload_blob(file, overwrite=False)

            print("Documentation state uploaded successfully.")

        elif args.action == "download":
            if any(directory.exists() for directory in DIRECTORIES):
                raise RuntimeError(
                    "Documentation directories already exist. "
                    "Refusing to overwrite local state."
                )

            with tempfile.TemporaryDirectory() as temp:
                archive_path = Path(temp) / "state.tar.gz"

                with archive_path.open("wb") as file:
                    blob.download_blob().readinto(file)

                safe_extract(archive_path)

            print("Documentation state restored successfully.")

    finally:
        credential.close()


if __name__ == "__main__":
    main()
