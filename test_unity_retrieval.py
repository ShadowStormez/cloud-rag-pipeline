from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# 1. Load the same embedding model used during ingestion
print("Loading embedding model...")

embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2"
)

# 2. Connect to our existing Unity database
db = Chroma(
    persist_directory="./chroma_unity_test",
    embedding_function=embeddings
)

# 3. Search the database
question = "How can I change the color of a sprite in Unity?"

print(f"\nQuestion: {question}")
print("\nSearching for relevant documentation...")

results = db.similarity_search(question, k=2)

# 4. Display the retrieved chunks
for i, document in enumerate(results, start=1):
    print(f"\n--- Result {i} ---")
    print(f"Source: {document.metadata.get('source')}")
    print(document.page_content[:700])