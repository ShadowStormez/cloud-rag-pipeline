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
