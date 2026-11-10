import sys
from unittest.mock import MagicMock, patch

import pytest

# Prevent real embeddings, Chroma, and Groq clients from initializing
# when main.py is imported during test collection.
with (
    patch(
        "langchain_huggingface.HuggingFaceEmbeddings",
        return_value=MagicMock(),
    ),
    patch(
        "langchain_community.vectorstores.Chroma",
        return_value=MagicMock(),
    ),
    patch(
        "langchain_groq.ChatGroq",
        return_value=MagicMock(),
    ),
):
    from main import QuestionRequest, build_retriever


@pytest.mark.parametrize("engine", ["unity", "godot", "unreal"])
def test_engine_filter(engine, monkeypatch):
    mock_db = MagicMock()
    monkeypatch.setattr(sys.modules["main"], "db", mock_db)

    build_retriever(engine)

    mock_db.as_retriever.assert_called_once_with(
        search_kwargs={
            "k": 3,
            "filter": {"source_type": engine},
        }
    )


def test_auto_search_has_no_filter(monkeypatch):
    mock_db = MagicMock()
    monkeypatch.setattr(sys.modules["main"], "db", mock_db)

    build_retriever("auto")

    mock_db.as_retriever.assert_called_once_with(
        search_kwargs={"k": 3}
    )


def test_default_engine_is_auto():
    request = QuestionRequest(question="What is an Actor?")
    assert request.engine == "auto"


def test_invalid_engine_rejected():
    with pytest.raises(ValueError):
        QuestionRequest(
            question="What is an Actor?",
            engine="invalid",
        )