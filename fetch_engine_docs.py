
from pathlib import Path
import json
import requests
from bs4 import BeautifulSoup
from bs4 import NavigableString
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import re

from utils import calculate_hash


DOCUMENTATION_PAGES = {
    "godot": {
        "Node2D": (
            "https://docs.godotengine.org/en/stable/"
            "classes/class_node2d.html"
        ),
        "RigidBody2D": (
            "https://docs.godotengine.org/en/stable/"
            "classes/class_rigidbody2d.html"
        ),
    },
    "unreal": {
        "Actor": (
            "https://dev.epicgames.com/documentation/en-us/"
            "unreal-engine/actors-in-unreal-engine"
        ),
        "Components": (
            "https://dev.epicgames.com/documentation/en-us/"
            "unreal-engine/components-in-unreal-engine"
        ),
    },
}


def extract_documentation(html: str) -> str:
    """Extract readable documentation text from an HTML page."""

    soup = BeautifulSoup(html, "html.parser")

    for element in soup(
        ["script", "style", "nav", "footer", "header"]
    ):
        element.decompose()

    main_content = (
        soup.find("article")
        or soup.find("main")
        or soup.find(attrs={"role": "main"})
    )

    if main_content is None:
        raise ValueError(
            "Documentation content not found. "
            "The page structure may have changed."
        )

    # Remove documentation heading permalink icons.
    for anchor in main_content.select("a.headerlink"):
        anchor.decompose()

    # Remove Godot's navigation and user-contributed notes.
    for element in main_content.select("#godot-giscus"):
        element.decompose()

    for element in main_content.find_all(
        ["p", "div", "section", "h1", "h2", "h3", "h4", "li", "tr", "pre"]
    ):
        element.insert_before("\n")
        element.insert_after("\n")

    text = main_content.get_text(separator=" ", strip=False)

    text = "\n".join(
    re.sub(r"[^\S\n]+", " ", line).strip()
    for line in text.splitlines()
    if line.strip()
)

    if len(text) < 100:
        raise ValueError(
            "Extracted documentation is unexpectedly short."
        )

    return text


def create_session() -> requests.Session:
    """Create an HTTP session with retry handling."""

    session = requests.Session()

    retry_strategy = Retry(
        total=4,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)

    session.headers.update({
        "User-Agent": "CloudRAGPipeline/1.0"
    })

    return session


def fetch_documentation(
    engine: str,
    name: str,
    url: str,
    session: requests.Session,
) -> bool:
    """Fetch a documentation page and save it if changed."""

    response = session.get(url, timeout=30)
    response.raise_for_status()

    text = extract_documentation(response.text)

    output_dir = Path("data") / engine
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"{name}.txt"

    if output_file.exists():
        old_text = output_file.read_text(encoding="utf-8")

        if calculate_hash(old_text) == calculate_hash(text):
            print(f"Unchanged: {engine}/{name}")
            return False

    output_file.write_text(text, encoding="utf-8")

    print(f"Updated: {engine}/{name}")
    return True

def fetch_engine(engine: str) -> int:
    """Fetch configured pages and preserve their source URLs."""

    if engine not in DOCUMENTATION_PAGES:
        raise ValueError(f"Unsupported engine: {engine}")

    changed = 0

    output_dir = Path("data") / engine
    output_dir.mkdir(parents=True, exist_ok=True)

    sources = {}

    with create_session() as session:
        for name, url in DOCUMENTATION_PAGES[engine].items():
            sources[f"{name}.txt"] = url

            if fetch_documentation(engine, name, url, session):
                changed += 1

    manifest_path = output_dir / "sources.json"
    manifest_content = json.dumps(
        sources,
        indent=2,
        sort_keys=True,
    ) + "\n"

    if (
        not manifest_path.exists()
        or manifest_path.read_text(encoding="utf-8")
        != manifest_content
    ):
        manifest_path.write_text(
            manifest_content,
            encoding="utf-8",
        )
        print(f"Updated source manifest: {manifest_path}")

    print(f"{engine}: {changed} changed pages")
    return changed
if __name__ == "__main__":
    for engine_name in DOCUMENTATION_PAGES:
        fetch_engine(engine_name)
