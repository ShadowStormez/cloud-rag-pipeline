
from fastapi.testclient import TestClient

from api import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "game-mechanics-rag-api",
    }

def test_ask_returns_503_when_rag_fails(monkeypatch):
    import sys
    from unittest.mock import MagicMock, patch

    # Avoid loading real embeddings or connecting to Groq.
    with (
        patch(
            "langchain_huggingface.HuggingFaceEmbeddings"
        ),
        patch(
            "langchain_community.vectorstores.Chroma"
        ),
        patch("langchain_groq.ChatGroq"),
    ):
        if "main" in sys.modules:
            main = sys.modules["main"]
        else:
            import main

    # Simulate a failure during RAG execution.
    monkeypatch.setattr(
        main,
        "create_retrieval_chain",
        lambda *args, **kwargs: MagicMock(
            invoke=MagicMock(
                side_effect=RuntimeError("Sensitive internal error")
            )
        ),
    )

    response = client.post(
        "/ask",
        json={
            "question": "How do I create a sprite?",
            "engine": "unity",
        },
    )

    assert response.status_code == 503
    assert response.json() == {
        "detail": (
            "The AI assistant is temporarily unavailable. "
            "Please try again later."
        )
    }

    assert "Sensitive internal error" not in response.text
