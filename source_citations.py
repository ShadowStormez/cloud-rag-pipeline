"""Select documents explicitly referenced by a RAG answer."""

import re


def select_cited_sources(answer, documents):
    """
    Return (clean_answer, cited_documents).

    Expected final line:
        Sources used: [1], [3]

    Deduplicate cited documents by source URL when available.
    """
    if not isinstance(answer, str):
        return answer, []

    match = re.search(
        r"(?im)^Sources used:\s*([^\n]*)\s*$",
        answer,
    )

    # Prefer the final citation summary. If it is missing,
    # recover only explicit parenthesized source references.
    if match:
        cited_numbers = [
            int(number)
            for number in re.findall(r"\[(\d+)\]", match.group(1))
        ]
    else:
        cited_numbers = [
            int(number)
            for number in re.findall(
                r"(?:\(\s*Source\s*|\bSource\s*:\s*)\[(\d+)\]\)?",
                answer,
                flags=re.IGNORECASE,
            )
        ]

    if not cited_numbers:
        return answer, []

    selected = []
    seen_indices = set()
    seen_urls = set()

    for number in cited_numbers:
        index = number - 1

        if not (0 <= index < len(documents)):
            continue

        if index in seen_indices:
            continue

        seen_indices.add(index)
        document = documents[index]

        metadata = getattr(document, "metadata", None)
        source_url = (
            metadata.get("source_url")
            if isinstance(metadata, dict)
            else None
        )

        if source_url:
            if source_url in seen_urls:
                continue
            seen_urls.add(source_url)

        selected.append(document)

    clean_answer = (
        answer[:match.start()] + answer[match.end():]
        if match else answer
    ).strip()

    # Remove explicit parenthesized references outside code blocks.

    # Remove standalone source labels outside fenced code blocks.
    # The frontend displays citations using the sources array.
    cleaned_lines = []
    inside_code_block = False

    for line in clean_answer.splitlines():
        if line.lstrip().startswith("```"):
            inside_code_block = not inside_code_block
            cleaned_lines.append(line)
            continue

        if inside_code_block:
            cleaned_lines.append(line)
            continue

        if not inside_code_block and re.match(
            r"^\s*Source:\s*\[\d+\](?:\s*\([^\n]*\))?\s*$",
            line,
            flags=re.IGNORECASE,
        ):
            continue

        line = re.sub(
            r"\(Source\s*\[\d+\]\)",
            "",
            line,
            flags=re.IGNORECASE,
        )

        # Remove model-generated numeric citation markers.
        line = re.sub(r"【[0-9]+】", "", line)
        cleaned_lines.append(line)

    clean_answer = "\n".join(cleaned_lines).strip()

    return clean_answer, selected
