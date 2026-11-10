
import os
from typing import Literal

from api import app
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_groq import ChatGroq
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

# Load expensive components once at application startup
print("Loading database and LLM...")

embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2"
)

DB_DIR = os.getenv("CHROMA_DB_DIR", "./chroma_unity_test")

db = Chroma(
    persist_directory=DB_DIR,
    embedding_function=embeddings,
)

llm = ChatGroq(model="openai/gpt-oss-20b")

system_prompt = (
    "You are a technical assistant specializing in Unity, Godot, "
    "and Unreal Engine documentation. "
    "Answer using only the retrieved documentation context. "
    "Do not invent methods, properties, class names, or APIs. "
    "Do not mix APIs from different game engines or versions. "
    "If the context does not contain enough information, "
    "explicitly say what is unknown. "
    "Prefer concise, accurate explanations over exhaustive lists. "
    "When an engine is selected, answer specifically for that engine.\n\n"
    "Retrieved documentation:\n{context}"
)

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{input}"),
])

question_answer_chain = create_stuff_documents_chain(
    llm, prompt
)


class QuestionRequest(BaseModel):
    question: str = Field(min_length=1)
    engine: Literal["auto", "unity", "godot", "unreal"] = "auto"


def build_retriever(engine: str):
    search_kwargs = {"k": 3}

    if engine != "auto":
        search_kwargs["filter"] = {
            "source_type": engine
        }

    return db.as_retriever(
        search_kwargs=search_kwargs
    )


@app.post("/ask")
async def ask_question(request: QuestionRequest):
    retriever = build_retriever(request.engine)

    rag_chain = create_retrieval_chain(
        retriever,
        question_answer_chain,
    )

    response = rag_chain.invoke({
        "input": request.question
    })

    sources = [
        {
            "metadata": doc.metadata,
            "content": doc.page_content,
        }
        for doc in response["context"]
    ]

    return {
        "answer": response["answer"],
        "sources": sources,
    }
