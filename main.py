import os
from api import app
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_groq import ChatGroq
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()


# Setup RAG components globally so they load once when the server starts
print("Loading database and LLM...")
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
DB_DIR = os.getenv("CHROMA_DB_DIR", "./chroma_unity_test")

db = Chroma(
    persist_directory=DB_DIR,
    embedding_function=embeddings
)
retriever = db.as_retriever(search_kwargs={"k": 3})

llm = ChatGroq(model="openai/gpt-oss-20b")

system_prompt = (
    "You are an assistant answering questions about game development. "
    "Use the following retrieved context to answer the question. "
    "If you don't know the answer, say that you don't know.\n\n"
    "Context: {context}"
)
prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{input}"),
])

question_answer_chain = create_stuff_documents_chain(llm, prompt)
rag_chain = create_retrieval_chain(retriever, question_answer_chain)

# Define the data format we expect from users
class QuestionRequest(BaseModel):
    question: str

# Create the API endpoint
@app.post("/ask")
async def ask_question(request: QuestionRequest):
    response = rag_chain.invoke({"input": request.question})

    sources = [
        {
            "metadata": doc.metadata,
            "content": doc.page_content
        }
        for doc in response["context"]
    ]

    return {
        "answer": response["answer"],
        "sources": sources
    }


