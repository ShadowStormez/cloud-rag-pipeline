from crawl_progress import (
    save_crawl_progress,
    load_crawl_progress,
)


def test_save_and_load_crawl_progress(tmp_path):
    progress_file = tmp_path / "crawl_progress.json"

    pending = [
        "https://docs.godotengine.org/part2.xml",
    ]

    visited = [
        "https://docs.godotengine.org/part1.xml",
    ]

    discovered = [
        "https://docs.godotengine.org/en/stable/classes/class_node2d.html",
    ]

    save_crawl_progress(
        progress_file,
        pending_sitemaps=pending,
        visited_sitemaps=visited,
        discovered_urls=discovered,
    )

    restored = load_crawl_progress(progress_file)

    assert restored["pending_sitemaps"] == pending
    assert restored["visited_sitemaps"] == visited
    assert restored["discovered_urls"] == discovered


def test_load_missing_progress_file(tmp_path):
    progress_file = tmp_path / "missing.json"

    assert load_crawl_progress(progress_file) is None