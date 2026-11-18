import argparse
import json
from pathlib import Path

from automatic_docs import download_documentation_batch
from documentation_discovery import (
    create_crawler_session,
    load_robots,
)


DISCOVERY_DIR = Path("data/discovery")
OUTPUT_DIR = Path("data/automatic")
ENGINE_BASE_URLS = {
    "unity": "https://docs.unity.com",
    "godot": "https://docs.godotengine.org",
    "unreal": "https://dev.epicgames.com",
}


def main():
    parser = argparse.ArgumentParser(
        description="Download documentation from saved discovery results."
    )

    parser.add_argument(
        "--engine",
        choices=list(ENGINE_BASE_URLS),
        required=True,
    )

    parser.add_argument(
        "--max-pages",
        type=int,
        default=5,
    )

    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay in seconds between documentation requests.",
    )

    parser.add_argument(
    "--refresh",
    action="store_true",
    help="Re-download existing documentation files.",
)

    args = parser.parse_args()

    if args.delay < 0:
        parser.error("--delay must not be negative")

    if args.max_pages < 1:
        parser.error("--max-pages must be at least 1")

    checkpoint = DISCOVERY_DIR / f"{args.engine}_progress.json"

    data = json.loads(checkpoint.read_text(encoding="utf-8"))
    urls = data["discovered_urls"]

    if args.engine == "godot":
        priority = {
            "classes": 0,
            "tutorials": 1,
            "engine_details": 2,
            "getting_started": 3,
        }

        def godot_priority(url):
            from urllib.parse import urlparse

            parts = urlparse(url).path.strip("/").split("/")
            category = parts[2] if len(parts) > 2 else ""

            return (priority.get(category, 4), url)

        urls = sorted(urls, key=godot_priority)

    print(f"Discovered URLs available: {len(urls)}")
    print(f"Maximum pages this run: {args.max_pages}")

    with create_crawler_session() as session:
        robots = load_robots(ENGINE_BASE_URLS[args.engine], session)

        download_documentation_batch(
            urls=urls,
            engine=args.engine,
            session=session,
            robots=robots,
            output_dir=OUTPUT_DIR / args.engine,
            max_pages=args.max_pages,
            delay_seconds=args.delay,
            refresh=args.refresh,
        )


if __name__ == "__main__":
    main()