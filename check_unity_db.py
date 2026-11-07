import chromadb

# Connect directly to our experimental Chroma database
client = chromadb.PersistentClient(path="./chroma_unity_test")

# Get the collection created by LangChain
collection = client.get_collection("langchain")

# Count the stored document chunks
print(f"Total stored chunks: {collection.count()}")

from collections import Counter

# Retrieve metadata for all stored chunks
records = collection.get(include=["metadatas"])

# Count how many chunks belong to each source
source_counts = Counter(
    metadata.get("source", "unknown")
    for metadata in records["metadatas"]
)

print("\nChunks per documentation source:")

for source, count in sorted(source_counts.items()):
    print(f"{source}: {count}")
