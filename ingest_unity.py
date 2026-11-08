from utils import calculate_hash
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document


DATA_DIR = Path("data/unity")
DB_DIR = "./chroma_unity_test"

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

    # Read the current document
    content = file_path.read_text(encoding="utf-8")

    # Calculate its SHA-256 fingerprint
    current_hash = calculate_hash(content)

    # Find existing chunks for this document
    existing = db.get(
        where={"source": source}
    )

    existing_ids = existing["ids"]
    existing_metadata = existing["metadatas"]

    # Check the hash saved with the existing chunks
    if existing_ids and existing_metadata:
        stored_hash = existing_metadata[0].get("content_hash")

        if stored_hash == current_hash:
            print("No changes detected. Skipping embeddings.")
            skipped_files += 1
            continue

    print("New or changed document detected.")

    # Split the document into chunks
    document = Document(
        page_content=content,
        metadata={
            "source": source,
            "content_hash": current_hash
        }
    )

    chunks = text_splitter.split_documents([document])

    # Generate predictable IDs
    chunk_ids = [
        f"unity-{file_path.stem}-{index}"
        for index in range(len(chunks))
    ]

    # Remove outdated chunks
    if existing_ids:
        db.delete(ids=existing_ids)
        print(f"Removed {len(existing_ids)} outdated chunks.")

    # Chroma generates embeddings when documents are added
    if chunks:
        db.add_documents(
            documents=chunks,
            ids=chunk_ids
        )

    print(f"Stored {len(chunks)} chunks.")

    updated_files += 1


print("\n--- Ingestion Summary ---")
print(f"Updated documents: {updated_files}")
print(f"Unchanged documents: {skipped_files}")
print("Incremental ingestion completed!")