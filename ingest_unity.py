
from pathlib import Path

from utils import calculate_hash
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document


DATA_DIR = Path("data/unity")
DB_DIR = "./chroma_unity_test"


def ingest_documents():
    """Incrementally ingest Unity documentation into Chroma."""

    print("Loading embedding model...")

    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )

    print("Connecting to Chroma...")

    db = Chroma(
        persist_directory=DB_DIR,
        embedding_function=embeddings
    )

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    updated_files = 0
    skipped_files = 0

    # Process each documentation file independently
    for file_path in sorted(DATA_DIR.glob("*.txt")):

        source = file_path.as_posix()

        print(f"\nChecking: {source}")

        content = file_path.read_text(encoding="utf-8")
        current_hash = calculate_hash(content)

        existing = db.get(
            where={"source": source}
        )

        existing_ids = existing["ids"]
        existing_metadata = existing["metadatas"]

        if existing_ids and existing_metadata:
            stored_hash = existing_metadata[0].get("content_hash")

            if stored_hash == current_hash:
                print("No changes detected. Skipping embeddings.")
                skipped_files += 1
                continue

        print("New or changed document detected.")

        document = Document(
            page_content=content,
            metadata={
                "source": source,
                "content_hash": current_hash
            }
        )

        chunks = text_splitter.split_documents([document])

        chunk_ids = [
            f"unity-{file_path.stem}-{index}"
            for index in range(len(chunks))
        ]

        
        # Generate embeddings before deleting existing chunks
        if chunks:
            chunk_texts = [chunk.page_content for chunk in chunks]

            chunk_embeddings = embeddings.embed_documents(chunk_texts)

            # Store prepared embeddings in Chroma
            collection = db._collection

            # Delete outdated chunks only after embedding succeeds
            if existing_ids:
                collection.delete(ids=existing_ids)
                print(f"Removed {len(existing_ids)} outdated chunks.")

            collection.add(
                ids=chunk_ids,
                documents=chunk_texts,
                embeddings=chunk_embeddings,
                metadatas=[chunk.metadata for chunk in chunks]
            )

        print(f"Stored {len(chunks)} chunks.")

        updated_files += 1


    print("\n--- Ingestion Summary ---")
    print(f"Updated documents: {updated_files}")
    print(f"Unchanged documents: {skipped_files}")
    print("Incremental ingestion completed!")


if __name__ == "__main__":
    ingest_documents()
