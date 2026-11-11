
import os
from pathlib import Path
import json
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

from document_processing import prepare_document


def ingest_directory(
    data_dir: str | Path,
    source_type: str,
    db_dir: str | None = None,
):
    """Incrementally ingest documentation from one provider."""

    data_dir = Path(data_dir)
    manifest_path = data_dir / "sources.json"
    source_urls = {}

    if manifest_path.exists():
        source_urls = json.loads(
            manifest_path.read_text(encoding="utf-8")
        )
    db_dir = db_dir or os.getenv(
        "CHROMA_DB_DIR", "./chroma_unity_test"
    )

    print(f"Loading embedding model for {source_type}...")

    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )

    print("Connecting to Chroma...")

    db = Chroma(
        persist_directory=db_dir,
        embedding_function=embeddings,
    )

    updated_files = 0
    skipped_files = 0

    for file_path in sorted(data_dir.glob("*.txt")):
        source = file_path.as_posix()

        print(f"\nChecking: {source}")

        current_hash, chunks = prepare_document(
        file_path=file_path,
        source_type=source_type,
        source_url=source_urls.get(file_path.name),
        )

        existing = db.get(where={"source": source})

        existing_ids = existing["ids"]
        existing_metadata = existing["metadatas"]

        if existing_ids and existing_metadata:
            stored_hash = existing_metadata[0].get(
                "content_hash"
            )

            if stored_hash == current_hash:
                updated_metadatas = []
                metadata_changed = False

                for existing_meta in existing_metadata:
                    new_meta = dict(existing_meta)

                    for key, value in chunks[0].metadata.items():
                        if new_meta.get(key) != value:
                            new_meta[key] = value
                            metadata_changed = True

                    updated_metadatas.append(new_meta)

                if metadata_changed:
                    db._collection.update(
                        ids=existing_ids,
                        metadatas=updated_metadatas,
                    )
                    print("Metadata updated without regenerating embeddings.")
                    updated_files += 1
                else:
                    print("No changes detected. Skipping embeddings.")
                    skipped_files += 1

                continue

        print("New or changed document detected.")

        chunk_ids = [
            f"{source_type}-{file_path.stem}-{index}"
            for index in range(len(chunks))
        ]

        if chunks:
            chunk_texts = [
                chunk.page_content for chunk in chunks
            ]

            chunk_embeddings = embeddings.embed_documents(
                chunk_texts
            )

            collection = db._collection

            if existing_ids:
                collection.delete(ids=existing_ids)
                print(
                    f"Removed {len(existing_ids)} outdated chunks."
                )

            collection.add(
                ids=chunk_ids,
                documents=chunk_texts,
                embeddings=chunk_embeddings,
                metadatas=[
                    chunk.metadata for chunk in chunks
                ],
            )

        print(f"Stored {len(chunks)} chunks.")
        updated_files += 1

    print("\n--- Ingestion Summary ---")
    print(f"Source: {source_type}")
    print(f"Updated documents: {updated_files}")
    print(f"Unchanged documents: {skipped_files}")
    print("Incremental ingestion completed!")
