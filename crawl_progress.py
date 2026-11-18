import json
from pathlib import Path


def save_crawl_progress(
    path: Path,
    pending_sitemaps: list[str],
    visited_sitemaps: list[str],
    discovered_urls: list[str],
) -> None:
    """Persist sitemap discovery progress atomically."""

    progress = {
        "pending_sitemaps": pending_sitemaps,
        "visited_sitemaps": visited_sitemaps,
        "discovered_urls": discovered_urls,
    }

    path.parent.mkdir(parents=True, exist_ok=True)

    temporary_path = path.with_suffix(path.suffix + ".tmp")

    temporary_path.write_text(
        json.dumps(progress, indent=2),
        encoding="utf-8",
    )

    temporary_path.replace(path)


def load_crawl_progress(path: Path) -> dict | None:
    """Load previous progress, if available."""

    if not path.exists():
        return None

    return json.loads(path.read_text(encoding="utf-8"))