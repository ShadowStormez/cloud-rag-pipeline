import json
from pathlib import Path

from automatic_docs import download_documentation_batch
from documentation_discovery import (
    create_crawler_session,
    load_robots,
)

output_dir = Path("data/automatic/godot")
manifest_path = output_dir / "sources.json"

sources = json.loads(manifest_path.read_text(encoding="utf-8"))

urls = list(dict.fromkeys(sources.values()))

print(f"Existing Godot documents to refresh: {len(urls)}")

with create_crawler_session() as session:
    robots = load_robots(
        "https://docs.godotengine.org",
        session,
    )

    download_documentation_batch(
        urls=urls,
        engine="godot",
        session=session,
        robots=robots,
        output_dir=output_dir,
        max_pages=len(urls),
        delay_seconds=1.0,
        refresh=True,
    )