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


@pytest.mark.parametrize("engine", ["unity", "godot"])
def test_engine_filter(engine, monkeypatch):
    mock_db = MagicMock()
    monkeypatch.setattr(sys.modules["main"], "db", mock_db)

    build_retriever(engine)

    mock_db.as_retriever.assert_called_once_with(
        search_kwargs={
            "k": 5,
            "filter": {"source_type": engine},
        }
    )


def test_auto_search_has_no_filter(monkeypatch):
    mock_db = MagicMock()
    monkeypatch.setattr(sys.modules["main"], "db", mock_db)

    build_retriever("auto")

    mock_db.as_retriever.assert_called_once_with(
        search_kwargs={"k": 5}
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

def test_unreal_engine_rejected():
    """Unreal must remain unavailable until permission is granted."""
    with pytest.raises(ValueError):
        QuestionRequest(
            question="How do I create an Actor?",
            engine="unreal",
        )


def test_empty_retrieval_skips_llm_and_returns_no_sources(monkeypatch):
    """Missing documentation must not produce unsupported citations."""
    from main import ask_question

    main_module = sys.modules["main"]
    mock_chain = MagicMock()

    monkeypatch.setattr(
        main_module,
        "retrieve_with_page_context",
        MagicMock(return_value=[]),
    )
    monkeypatch.setattr(
        main_module,
        "question_answer_chain",
        mock_chain,
    )

    response = ask_question(
        QuestionRequest(
            question="How do I implement an unknown feature?",
            engine="unity",
        )
    )

    assert response["sources"] == []
    assert "couldn't find relevant documentation" in response["answer"]
    mock_chain.invoke.assert_not_called()


def test_uncertain_answer_does_not_return_citations(monkeypatch):
    """An unsupported answer must not present retrieved pages as evidence."""
    from langchain_core.documents import Document
    from main import ask_question

    main_module = sys.modules["main"]

    irrelevant_doc = Document(
        page_content="How to configure lightmap baking.",
        metadata={
            "source_type": "unity",
            "source_url": "https://docs.unity.com/example",
        },
    )

    monkeypatch.setattr(
        main_module,
        "retrieve_with_page_context",
        MagicMock(return_value=[irrelevant_doc]),
    )

    mock_chain = MagicMock()
    mock_chain.invoke.return_value = (
        "I don't know based on the available documentation."
    )
    monkeypatch.setattr(
        main_module,
        "question_answer_chain",
        mock_chain,
    )

    result = ask_question(
        QuestionRequest(
            question="How do I bake a chocolate cake?",
            engine="unity",
        )
    )

    assert result["sources"] == []


def test_unity_named_class_retrieves_its_api_documentation(monkeypatch):
    """Explicit Unity class names should prioritize indexed API pages."""
    from langchain_core.documents import Document
    from main import retrieve_with_page_context

    main_module = sys.modules["main"]

    url = (
        "https://docs.unity3d.com/6000.0/"
        "Documentation/ScriptReference/Rigidbody2D.html"
    )

    api_doc = Document(
        page_content="Rigidbody2D.linearVelocity controls movement.",
        metadata={
            "source_type": "unity",
            "source_url": url,
        },
    )

    unrelated_doc = Document(
        page_content="Animator parameters control transitions.",
        metadata={
            "source_type": "unity",
            "source_url": "https://docs.unity.com/animation",
        },
    )

    mock_db = MagicMock()
    mock_db._collection.get.return_value = {
        "ids": ["rigidbody2d-0"]
    }
    mock_db.similarity_search.return_value = [api_doc]

    mock_retriever = MagicMock()
    mock_retriever.invoke.return_value = [unrelated_doc]

    monkeypatch.setattr(main_module, "db", mock_db)
    monkeypatch.setattr(
        main_module,
        "build_retriever",
        MagicMock(return_value=mock_retriever),
    )
    monkeypatch.setattr(
        main_module,
        "expand_neighboring_chunks",
        lambda documents, max_chunks: documents[:max_chunks],
    )

    results = retrieve_with_page_context(
        "unity",
        "Write a Rigidbody2D movement controller.",
    )

    assert results
    assert results[0].metadata["source_url"] == url


def test_neighbor_expansion_preserves_multiple_pages(monkeypatch):
    """One API page must not crowd every other source out of context."""
    from langchain_core.documents import Document
    from main import expand_neighboring_chunks

    main_module = sys.modules["main"]

    physics_url = "https://docs.unity3d.com/physics.html"
    input_url = "https://docs.unity3d.com/input.html"

    records = {}

    for label, url, count in (
        ("physics", physics_url, 12),
        ("input", input_url, 3),
    ):
        records[label] = {
            "ids": [f"{label}-{i}" for i in range(count)],
            "documents": [
                f"{label} content {i}" for i in range(count)
            ],
            "metadatas": [
                {
                    "source": f"data/unity/{label}.txt",
                    "source_type": "unity",
                    "source_url": url,
                }
                for _ in range(count)
            ],
        }

    mock_db = MagicMock()

    def get_records(where, include):
        source = next(
            clause["source"]
            for clause in where["$and"]
            if "source" in clause
        )
        label = "physics" if "physics" in source else "input"
        return records[label]

    mock_db._collection.get.side_effect = get_records
    monkeypatch.setattr(main_module, "db", mock_db)

    documents = [
        Document(
            page_content="physics content 5",
            metadata=records["physics"]["metadatas"][5],
        ),
        Document(
            page_content="input content 1",
            metadata=records["input"]["metadatas"][1],
        ),
    ]

    result = expand_neighboring_chunks(
        documents,
        max_chunks=4,
    )

    urls = {
        doc.metadata["source_url"]
        for doc in result
    }

    assert physics_url in urls
    assert input_url in urls


def test_unity_class_priority_preserves_supporting_pages(monkeypatch):
    """Named APIs should not consume the entire context budget."""
    from langchain_core.documents import Document
    from main import retrieve_with_page_context

    main_module = sys.modules["main"]

    physics_url = (
        "https://docs.unity3d.com/6000.0/"
        "Documentation/ScriptReference/Rigidbody2D.html"
    )
    input_url = (
        "https://docs.unity.com/en-us/engine/6000.0/"
        "manual/input/legacy/class-input-manager"
    )

    physics_docs = [
        Document(
            page_content=f"Rigidbody2D physics definition {i}",
            metadata={
                "source_type": "unity",
                "source_url": physics_url,
            },
        )
        for i in range(12)
    ]

    input_doc = Document(
        page_content="Read horizontal input using Input.GetAxis.",
        metadata={
            "source_type": "unity",
            "source_url": input_url,
        },
    )

    mock_db = MagicMock()
    mock_db._collection.get.return_value = {
        "ids": ["rigidbody2d-0"]
    }
    mock_db.similarity_search.return_value = physics_docs[:5]

    retriever = MagicMock()
    retriever.invoke.return_value = [input_doc]

    monkeypatch.setattr(main_module, "db", mock_db)
    monkeypatch.setattr(
        main_module,
        "build_retriever",
        MagicMock(return_value=retriever),
    )
    monkeypatch.setattr(
        main_module,
        "expand_neighboring_chunks",
        lambda documents, max_chunks: documents[:max_chunks],
    )

    results = retrieve_with_page_context(
        "unity",
        "Write a Rigidbody2D controller using Input.GetAxis.",
        max_chunks=4,
    )

    urls = [doc.metadata["source_url"] for doc in results]

    assert physics_url in urls
    assert input_url in urls
    assert urls[0] == physics_url


def test_unity_canonical_class_url_is_targeted(monkeypatch):
    """Unity classes indexed under canonical URLs must be discoverable."""
    from langchain_core.documents import Document
    from main import retrieve_with_page_context

    main_module = sys.modules["main"]

    canonical_url = (
        "https://docs.unity.com/en-us/engine/6000.0/"
        "script-reference/unityengine/monobehaviour"
    )

    api_doc = Document(
        page_content="MonoBehaviour defines Unity event functions.",
        metadata={
            "source_type": "unity",
            "source_url": canonical_url,
        },
    )

    unrelated_doc = Document(
        page_content="Animation controller settings.",
        metadata={
            "source_type": "unity",
            "source_url": "https://docs.unity.com/animation",
        },
    )

    mock_db = MagicMock()

    def get_records(where, limit):
        urls = [
            condition["source_url"]
            for condition in where["$and"]
            if "source_url" in condition
        ]
        return {
            "ids": ["monobehaviour-0"]
            if canonical_url in urls else []
        }

    mock_db._collection.get.side_effect = get_records
    mock_db.similarity_search.return_value = [api_doc]

    retriever = MagicMock()
    retriever.invoke.return_value = [unrelated_doc]

    monkeypatch.setattr(main_module, "db", mock_db)
    monkeypatch.setattr(
        main_module,
        "build_retriever",
        MagicMock(return_value=retriever),
    )
    monkeypatch.setattr(
        main_module,
        "expand_neighboring_chunks",
        lambda docs, max_chunks: docs[:max_chunks],
    )

    result = retrieve_with_page_context(
        "unity",
        "Explain the MonoBehaviour class.",
        max_chunks=4,
    )

    assert result
    assert result[0].metadata["source_url"] == canonical_url


def test_unity_keyboard_controller_includes_supporting_apis(monkeypatch):
    """Keyboard-driven Rigidbody2D controllers need physics and input evidence."""
    from langchain_core.documents import Document
    from main import retrieve_with_page_context

    main_module = sys.modules["main"]

    def api_url(name):
        if name == "Rigidbody2D":
            return (
                "https://docs.unity3d.com/6000.0/"
                "Documentation/ScriptReference/Rigidbody2D.html"
            )
        return (
            "https://docs.unity.com/en-us/engine/6000.0/"
            f"script-reference/unityengine/{name.lower()}"
        )

    def get_records(where, limit):
        url = next(
            clause["source_url"]
            for clause in where["$and"]
            if "source_url" in clause
        )
        known = {
            api_url("Rigidbody2D"),
            api_url("Input"),
            api_url("KeyCode"),
            api_url("MonoBehaviour"),
        }
        return {"ids": ["existing-0"] if url in known else []}

    def search(query, k, filter):
        url = next(
            clause["source_url"]
            for clause in filter["$and"]
            if "source_url" in clause
        )
        return [
            Document(
                page_content=f"Official API documentation for {url}",
                metadata={
                    "source_type": "unity",
                    "source_url": url,
                },
            )
        ]

    mock_db = MagicMock()
    mock_db._collection.get.side_effect = get_records
    mock_db.similarity_search.side_effect = search

    retriever = MagicMock()
    retriever.invoke.return_value = []

    monkeypatch.setattr(main_module, "db", mock_db)
    monkeypatch.setattr(
        main_module,
        "build_retriever",
        MagicMock(return_value=retriever),
    )
    monkeypatch.setattr(
        main_module,
        "expand_neighboring_chunks",
        lambda docs, max_chunks: docs[:max_chunks],
    )

    results = retrieve_with_page_context(
        "unity",
        "Write a Rigidbody2D controller that moves with keyboard "
        "input and jumps when Space is pressed.",
        max_chunks=10,
    )

    urls = {doc.metadata["source_url"] for doc in results}

    assert api_url("Rigidbody2D") in urls
    assert api_url("Input") in urls
    assert api_url("KeyCode") in urls
    assert api_url("MonoBehaviour") in urls


def test_empty_model_answer_has_no_citations(monkeypatch):
    """An empty LLM response must never be presented with citations."""
    from langchain_core.documents import Document
    from main import ask_question

    main_module = sys.modules["main"]

    document = Document(
        page_content="Rigidbody2D controls 2D physics movement.",
        metadata={
            "source_type": "unity",
            "source_url": (
                "https://docs.unity.com/en-us/engine/6000.0/"
                "script-reference/unityengine/rigidbody2d"
            ),
        },
    )

    monkeypatch.setattr(
        main_module,
        "retrieve_with_page_context",
        MagicMock(return_value=[document]),
    )

    mock_chain = MagicMock()
    mock_chain.invoke.return_value = ""
    monkeypatch.setattr(
        main_module,
        "question_answer_chain",
        mock_chain,
    )

    response = ask_question(
        QuestionRequest(
            question="Explain Rigidbody2D.",
            engine="unity",
        )
    )

    assert response["answer"].strip()
    assert response["sources"] == []
