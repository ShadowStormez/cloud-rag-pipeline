from collections import defaultdict, deque
from urllib.parse import urlparse


def documentation_topic(url: str, engine: str) -> str:
    """Identify a broad documentation topic from its URL."""
    path_parts = [
        part
        for part in urlparse(url).path.strip("/").split("/")
        if part
    ]

    if engine == "unity":
        for section in ("manual", "script-reference", "ScriptReference", "Manual"):
            if section in path_parts:
                index = path_parts.index(section)
                remaining = path_parts[index + 1:]
                return remaining[0] if remaining else "general"

    elif engine == "godot":
        if "classes" in path_parts:
            return "class-reference"

        if "tutorials" in path_parts:
            index = path_parts.index("tutorials")
            remaining = path_parts[index + 1:]

            if not remaining or remaining[0] == "index.html":
                return "tutorials"

            return remaining[0]

    else:
        raise ValueError(f"Unsupported engine: {engine}")

    return "general"


def select_diverse_urls(
    urls: list[str],
    engine: str,
    max_pages: int,
) -> list[str]:
    """Select URLs round-robin across documentation topics."""

    if max_pages < 1:
        raise ValueError("max_pages must be at least 1")

    if engine not in ("unity", "godot"):
        raise ValueError(f"Unsupported engine: {engine}")

    grouped = defaultdict(deque)

    for url in dict.fromkeys(urls):
        topic = documentation_topic(url, engine)
        grouped[topic].append(url)

    selected = []

    while grouped and len(selected) < max_pages:
        for topic in list(grouped):
            if len(selected) >= max_pages:
                break

            selected.append(grouped[topic].popleft())

            if not grouped[topic]:
                del grouped[topic]

    return selected