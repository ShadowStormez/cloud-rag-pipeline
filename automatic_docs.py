from pathlib import Path
from urllib.parse import urlsplit
import hashlib
import json
import time
import requests

from documentation_discovery import (
    create_crawler_session,
    load_robots,
    crawl_documentation_links,
    fetch_documentation_page,
    USER_AGENT,
)

from fetch_engine_docs import extract_documentation


def filename_for_url(url: str) -> str:
    """Generate a stable, unique filename for a documentation URL."""

    path = urlsplit(url).path.rstrip("/")
    name = Path(path).stem or "index"

    # Avoid filename collisions across different documentation paths.
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]

    return f"{name}-{digest}.txt"

def clean_documentation_text(text: str) -> str:
    """Remove documentation permalink symbols."""

    return text.replace("\uf0c1", "").replace("🔗", "")

def download_documentation_batch(
    urls: list[str],
    engine: str,
    session,
    robots,
    output_dir: Path,
    max_pages: int = 5,
    delay_seconds: float = 1.0,
    refresh: bool = True,
    retry_failed: bool = False,
) -> int:
    """Download and save a small batch of documentation pages."""

    if max_pages < 1:
        raise ValueError("max_pages must be at least 1")

    if delay_seconds < 0:
        raise ValueError("delay_seconds cannot be negative")
    
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = output_dir / "sources.json"

    if manifest_path.exists():
        sources = json.loads(
            manifest_path.read_text(encoding="utf-8")
        )
    else:
        sources = {}

    def save_manifest():
                temporary_path = manifest_path.with_suffix(".json.tmp")

                temporary_path.write_text(
                    json.dumps(sources, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )

                temporary_path.replace(manifest_path)

    failed_path = output_dir / "failed_urls.json"

    if failed_path.exists():
        failed_urls = set(
            json.loads(failed_path.read_text(encoding="utf-8"))
        )
    else:
        failed_urls = set()

    def save_failed_urls():
        temporary_path = failed_path.with_suffix(".json.tmp")

        temporary_path.write_text(
            json.dumps(sorted(failed_urls), indent=2) + "\n",
            encoding="utf-8",
        )

        temporary_path.replace(failed_path)

    changed = 0

    pending_urls = []

    for url in dict.fromkeys(urls):
        filename = filename_for_url(url)
        output_file = output_dir / filename

        already_downloaded = (
            sources.get(filename) == url
            and output_file.is_file()
        )

        if refresh or (
            not already_downloaded
            and (retry_failed or url not in failed_urls)
        ):
            pending_urls.append(url)

    for index, url in enumerate(pending_urls[:max_pages]):
        if index > 0:
            time.sleep(delay_seconds)
        print(f"\nProcessing: {url}")

        try:
            html = fetch_documentation_page(
                url,
                engine,
                session,
                robots,
            )

            text = clean_documentation_text(
                extract_documentation(html)
            )

            filename = filename_for_url(url)
            output_file = output_dir / filename

            if (
                output_file.exists()
                and output_file.read_text(encoding="utf-8") == text
            ):
                print("Unchanged. Skipping file update.")
            else:
                output_file.write_text(
                    text,
                    encoding="utf-8",
                )
                changed += 1
                print(f"Saved: {output_file}")

            sources[filename] = url
            save_manifest()

            if url in failed_urls:
                failed_urls.remove(url)
                save_failed_urls()

        except (
            requests.RequestException,
            ValueError,
            PermissionError,
            OSError,
        ) as exc:
            failed_urls.add(url)
            save_failed_urls()

            print(f"Skipped: {url}")
            print(f"Reason: {exc}")

    print(f"\nDownloaded or updated: {changed} pages")

    return changed