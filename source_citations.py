"""Select documents explicitly referenced by a RAG answer."""

import re


def select_cited_sources(answer, documents):
    """
    Return (clean_answer, cited_documents).

    Expected final line:
        Sources used: [1], [3]
    """
    if not isinstance(answer, str):
        return answer, []

    match = re.search(
        r"(?im)^Sources used:\s*([^\n]*)\s*$",
        answer,
    )

    if not match:
        return answer, []

    cited_numbers = [
        int(number)
        for number in re.findall(r"\[(\d+)\]", match.group(1))
    ]

    selected = []
    seen = set()

    for number in cited_numbers:
        index = number - 1

        if 0 <= index < len(documents) and index not in seen:
            selected.append(documents[index])
            seen.add(index)

    clean_answer = (
        answer[:match.start()] + answer[match.end():]
    ).strip()

    return clean_answer, selected
