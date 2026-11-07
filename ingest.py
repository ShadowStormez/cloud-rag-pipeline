from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# 1. Load the text
print("Loading document...")
loader = TextLoader("data/game_mechanics.md")
documents = loader.load()

# 2. Chunk the text into manageable pieces
print("Chunking text...")
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = text_splitter.split_documents(documents)
print(f"Split document into {len(chunks)} chunks.")

# 3. Convert to embeddings and save to ChromaDB
print("Generating embeddings and saving to database...")
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
db = Chroma.from_documents(chunks, embeddings, persist_directory="./chroma_db")

print("Success! Database saved to the ./chroma_db folder.")
