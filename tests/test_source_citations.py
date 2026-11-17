from source_citations import select_cited_sources


def test_selects_only_referenced_documents():
    documents = ["Unity Input", "Unrelated XR", "Unity KeyCode"]
    answer = (
        "Use Input.GetKeyDown(KeyCode.Space).\n"
        "Sources used: [1], [3]"
    )

    clean_answer, sources = select_cited_sources(answer, documents)

    assert clean_answer == "Use Input.GetKeyDown(KeyCode.Space)."
    assert sources == ["Unity Input", "Unity KeyCode"]


def test_does_not_accept_invalid_document_numbers():
    documents = ["Unity Input", "Unity KeyCode"]
    answer = "Example answer.\nSources used: [2], [99]"

    clean_answer, sources = select_cited_sources(answer, documents)

    assert clean_answer == "Example answer."
    assert sources == ["Unity KeyCode"]


def test_does_not_invent_citations_when_none_are_reported():
    documents = ["Unity Input", "Unrelated XR"]
    answer = "A valid explanation without source references."

    clean_answer, sources = select_cited_sources(answer, documents)

    assert clean_answer == answer
    assert sources == []


def test_deduplicates_documents_with_same_source_url():
    from langchain_core.documents import Document

    url = "https://docs.godotengine.org/en/stable/classes/class_area2d.html"

    documents = [
        Document(
            page_content="Area2D monitoring settings",
            metadata={"source_url": url},
        ),
        Document(
            page_content="Area2D signals",
            metadata={"source_url": url},
        ),
        Document(
            page_content="CharacterBody2D movement",
            metadata={
                "source_url": "https://docs.godotengine.org/en/stable/classes/class_characterbody2d.html"
            },
        ),
    ]

    answer = (
        "Use Area2D signals and configure monitoring.\n"
        "Sources used: [1], [2], [3]"
    )

    clean_answer, sources = select_cited_sources(answer, documents)

    assert clean_answer == "Use Area2D signals and configure monitoring."
    assert sources == [documents[0], documents[2]]


def test_removes_inline_source_labels_without_changing_code():
    from langchain_core.documents import Document

    documents = [
        Document(
            page_content="Area2D body_entered signal",
            metadata={
                "source_url": "https://docs.godotengine.org/en/stable/classes/class_area2d.html"
            },
        ),
        Document(
            page_content="Area2D monitoring property",
            metadata={
                "source_url": "https://docs.godotengine.org/en/stable/classes/class_area2d.html"
            },
        ),
    ]

    answer = (
        "Enable monitoring.\n"
        "Source: [2]\n\n"
        "```gdscript\n"
        "body_entered.connect(_on_body_entered)\n"
        "```\n"
        "Source: [1] (signal description)\n\n"
        "Sources used: [1], [2]"
    )

    clean_answer, sources = select_cited_sources(answer, documents)

    assert "Source: [1]" not in clean_answer
    assert "Source: [2]" not in clean_answer
    assert "Sources used:" not in clean_answer
    assert "body_entered.connect(_on_body_entered)" in clean_answer
    assert sources == [documents[0]]


def test_removes_bracket_citations_outside_code_blocks():
    from langchain_core.documents import Document

    documents = [
        Document(
            page_content="Area2D body_entered documentation",
            metadata={
                "source_url": "https://docs.godotengine.org/en/stable/classes/class_area2d.html"
            },
        ),
    ]

    answer = (
        "Use the body_entered signal【1】.\n"
        "Enable monitoring【4】.\n\n"
        "```gdscript\n"
        'print("Player entered")\n'
        "```\n\n"
        "Sources used: [1]"
    )

    clean_answer, sources = select_cited_sources(answer, documents)

    assert "【1】" not in clean_answer
    assert "【4】" not in clean_answer
    assert "Use the body_entered signal." in clean_answer
    assert 'print("Player entered")' in clean_answer
    assert sources == [documents[0]]


def test_recovers_parenthesized_citations_without_summary():
    from langchain_core.documents import Document

    documents = [
        Document(
            page_content="Area2D body_entered signal",
            metadata={
                "source_url": "https://docs.godotengine.org/en/stable/classes/class_area2d.html"
            },
        ),
        Document(
            page_content="Unrelated documentation",
            metadata={
                "source_url": "https://docs.godotengine.org/en/stable/classes/class_node.html"
            },
        ),
        Document(
            page_content="More unrelated documentation",
            metadata={
                "source_url": "https://docs.godotengine.org/en/stable/classes/class_object.html"
            },
        ),
        Document(
            page_content="Area2D monitoring property",
            metadata={
                "source_url": "https://docs.godotengine.org/en/stable/classes/class_area2d.html"
            },
        ),
    ]

    answer = (
        "Use the body_entered signal.\n"
        "(Source\u00a0[1])\n"
        "Enable monitoring.\n"
        "(Source [4])"
    )

    clean_answer, sources = select_cited_sources(answer, documents)

    assert "(Source" not in clean_answer
    assert "Use the body_entered signal." in clean_answer
    assert "Enable monitoring." in clean_answer
    assert sources == [documents[0]]


def test_recovers_standalone_source_labels_without_summary():
    from langchain_core.documents import Document

    documents = [
        Document(
            page_content=f"Godot documentation chunk {i}",
            metadata={
                "source_url": (
                    "https://docs.godotengine.org/en/stable/"
                    "classes/class_area2d.html"
                )
            },
        )
        for i in range(6)
    ]

    answer = (
        "Use the body_entered signal.\n"
        "Source: [1]\n\n"
        "Enable monitoring.\n"
        "Source: [4]\n\n"
        "Configure collision masks.\n"
        "Source: [6] (overlap rules)"
    )

    clean_answer, sources = select_cited_sources(answer, documents)

    assert "Source: [" not in clean_answer
    assert "Use the body_entered signal." in clean_answer
    assert "Enable monitoring." in clean_answer
    assert "Configure collision masks." in clean_answer
    assert sources == [documents[0]]


def test_preserves_citation_like_text_inside_code_blocks():
    from langchain_core.documents import Document

    documents = [
        Document(
            page_content="Godot Area2D documentation",
            metadata={
                "source_url": "https://docs.godotengine.org/en/stable/classes/class_area2d.html"
            },
        ),
    ]

    answer = (
        "Connect the signal.\n\n"
        "```gdscript\n"
        'print("(Source [1])")\n'
        'print("【1】")\n'
        "```\n\n"
        "Sources used: [1]"
    )

    clean_answer, sources = select_cited_sources(answer, documents)

    assert 'print("(Source [1])")' in clean_answer
    assert 'print("【1】")' in clean_answer
    assert sources == [documents[0]]
