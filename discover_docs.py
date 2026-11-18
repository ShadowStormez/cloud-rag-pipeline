from pathlib import Path
import argparse
from documentation_discovery import (
    create_crawler_session,
    load_robots,
    discover_from_sitemaps,
)


DISCOVERY_DIR = Path("data/discovery")

ENGINE_CONFIG = {
    "unity": {
        "base_url": "https://docs.unity.com",
        "sitemap_url": "https://docs.unity.com/sitemap.xml",
    },
    "godot": {
        "base_url": "https://docs.godotengine.org",
        "sitemap_url": "https://docs.godotengine.org/sitemap.xml",
    },
}

def main():
    parser = argparse.ArgumentParser(
        description="Discover official game engine documentation."
    )

    parser.add_argument(
        "--engine",
        choices=ENGINE_CONFIG.keys(),
        required=True,
        help="Documentation engine to discover.",
    )

    parser.add_argument(
        "--max-sitemaps",
        type=int,
        default=10,
        help="Maximum total sitemaps to process.",
    )

    args = parser.parse_args()

    if args.max_sitemaps < 1:
        parser.error("--max-sitemaps must be positive")

    config = ENGINE_CONFIG[args.engine]

    progress_file = DISCOVERY_DIR / f"{args.engine}_progress.json"

    with create_crawler_session() as session:
        print(f"Loading {args.engine} robots.txt...")

        robots = load_robots(
            config["base_url"],
            session,
        )

        print(f"Discovering {args.engine} documentation...")

        urls = discover_from_sitemaps(
            sitemap_url=config["sitemap_url"],
            engine=args.engine,
            session=session,
            robots=robots,
            max_pages=1_000_000,
            max_sitemaps=args.max_sitemaps,
            progress_file=progress_file,
        )

    print(f"Discovered URLs: {len(urls)}")
    print(f"Progress saved to: {progress_file}")


if __name__ == "__main__":
    main()