from urllib.parse import urljoin, urlsplit, urlunsplit
import xml.etree.ElementTree as ET
import requests
from urllib.robotparser import RobotFileParser
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from collections import deque
from bs4 import BeautifulSoup
import time
from pathlib import Path
from crawl_progress import load_crawl_progress, save_crawl_progress

ALLOWED_HOSTS = {
    "unity": {
        "docs.unity.com",
        "docs.unity3d.com",
    },
    "godot": {
        "docs.godotengine.org",
    },
    "unreal": {
        "dev.epicgames.com",
    },
}

ALLOWED_PATH_PREFIXES = {
    "unity": (
        "/en-us/engine/6000.0/script-reference",
        "/en-us/engine/6000.0/manual",
        "/6000.0/Documentation/ScriptReference/",
        "/6000.0/Documentation/Manual/",
    ),
    "godot": (
        "/en/stable/",
    ),
    "unreal": (
        "/documentation/en-us/unreal-engine/",
    ),
}


def normalize_url(url: str, base_url: str | None = None) -> str:
    """Resolve a URL and remove fragments and query parameters."""

    if base_url:
        url = urljoin(base_url, url)

    parsed = urlsplit(url)

    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Unsupported URL scheme")

    return urlunsplit((
        parsed.scheme.lower(),
        parsed.netloc.lower(),
        parsed.path,
        "",
        "",
    ))


def is_allowed_documentation_url(
    url: str,
    engine: str,
) -> bool:
    """Check whether a URL belongs to an approved documentation area."""

    if engine not in ALLOWED_HOSTS:
        raise ValueError(f"Unsupported engine: {engine}")

    try:
        normalized = normalize_url(url)
    except ValueError:
        return False

    parsed = urlsplit(normalized)

    if parsed.scheme != "https":
        return False

    if parsed.hostname not in ALLOWED_HOSTS[engine]:
        return False

    if parsed.port not in (None, 443):
        return False

    return any(
        parsed.path.startswith(prefix)
        for prefix in ALLOWED_PATH_PREFIXES[engine]
    )




def parse_sitemap(xml_content: str) -> tuple[list[str], list[str]]:
    """
    Parse a sitemap XML document.

    Returns:
        (page_urls, nested_sitemap_urls)
    """

    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as exc:
        raise ValueError("Invalid sitemap XML") from exc

    root_type = root.tag.rsplit("}", 1)[-1]

    page_urls = []
    sitemap_urls = []

    if root_type == "urlset":
        for element in root:
            if element.tag.rsplit("}", 1)[-1] != "url":
                continue

            for child in element:
                if child.tag.rsplit("}", 1)[-1] == "loc":
                    if child.text and child.text.strip():
                        page_urls.append(child.text.strip())
                    break

    elif root_type == "sitemapindex":
        for element in root:
            if element.tag.rsplit("}", 1)[-1] != "sitemap":
                continue

            for child in element:
                if child.tag.rsplit("}", 1)[-1] == "loc":
                    if child.text and child.text.strip():
                        sitemap_urls.append(child.text.strip())
                    break

    else:
        raise ValueError("Unsupported sitemap XML format")

    return page_urls, sitemap_urls

USER_AGENT = "LudexDocumentationCrawler/1.0"


def create_crawler_session() -> requests.Session:
    """Create a session with bounded retries."""

    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT

    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        respect_retry_after_header=True,
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)

    session.mount("https://", adapter)

    return session

def download_limited(
    url: str,
    session: requests.Session,
    max_bytes: int,
) -> bytes:
    """Download a response without exceeding the configured size limit."""

    with session.get(
        url,
        timeout=(5, 20),
        allow_redirects=False,
        stream=True,
    ) as response:
        response.raise_for_status()

        if response.is_redirect:
            raise ValueError("Redirects are not supported")

        content_length = response.headers.get("Content-Length")

        if content_length is not None:
            if int(content_length) > max_bytes:
                raise ValueError("Download exceeds size limit")

        chunks = []
        total_bytes = 0

        for chunk in response.iter_content(chunk_size=8192):
            if not chunk:
                continue

            total_bytes += len(chunk)

            if total_bytes > max_bytes:
                raise ValueError("Download exceeds size limit")

            chunks.append(chunk)

        return b"".join(chunks)

def fetch_sitemap(
    url: str,
    session: requests.Session,
    robots: RobotFileParser,
    engine: str,
) -> str:
    """Download a sitemap with URL, robots, and size restrictions."""

    if not is_allowed_sitemap_url(url, engine):
        raise ValueError(f"Unapproved sitemap URL: {url}")

    if not robots.can_fetch(USER_AGENT, url):
        raise PermissionError(
            f"robots.txt does not permit fetching: {url}"
        )

    content = download_limited(
        url,
        session,
        max_bytes=10 * 1024 * 1024,
    )

    return content.decode("utf-8-sig")

def load_robots(
    base_url: str,
    session: requests.Session,
) -> RobotFileParser:
    """Retrieve robots.txt with a bounded download."""

    parsed = urlsplit(base_url)

    if parsed.scheme != "https":
        raise ValueError("Only HTTPS websites are supported")

    if (
        parsed.hostname not in set().union(*ALLOWED_HOSTS.values())
        or parsed.port not in (None, 443)
        or parsed.username
        or parsed.password
    ):
        raise ValueError("Unapproved documentation host")

    robots_url = urlunsplit((
        "https",
        parsed.hostname,
        "/robots.txt",
        "",
        "",
    ))

    content = download_limited(
        robots_url,
        session,
        max_bytes=1024 * 1024,
    )

    robots = RobotFileParser()
    robots.set_url(robots_url)
    robots.parse(content.decode("utf-8-sig").splitlines())

    return robots

def is_allowed_sitemap_url(url: str, engine: str) -> bool:
    """Allow sitemap requests only on the engine's official host."""

    if engine not in ALLOWED_HOSTS:
        raise ValueError(f"Unsupported engine: {engine}")

    try:
        parsed = urlsplit(normalize_url(url))

        return (
            parsed.scheme == "https"
            and parsed.hostname in ALLOWED_HOSTS[engine]
            and parsed.port in (None, 443)
            and not parsed.username
            and not parsed.password
            and parsed.path.lower().endswith((".xml", ".xml.gz"))
        )
    except ValueError:
        return False


def discover_from_sitemaps(
    sitemap_url: str,
    engine: str,
    session: requests.Session,
    robots: RobotFileParser,
    max_pages: int = 100,
    max_sitemaps: int = 10,
    progress_file: Path | None = None,
) -> list[str]:
    """Discover documentation URLs from bounded sitemap traversal."""

    if max_pages < 1 or max_sitemaps < 1:
        raise ValueError("Discovery limits must be positive")

    if not is_allowed_sitemap_url(sitemap_url, engine):
        raise ValueError(f"Unapproved sitemap URL: {sitemap_url}")

    saved = load_crawl_progress(progress_file) if progress_file else None

    if saved:
        pending = deque(saved["pending_sitemaps"])
        visited_sitemaps = set(saved["visited_sitemaps"])
        discovered = list(saved["discovered_urls"])
        seen_pages = set(discovered)
    else:
        pending = deque([sitemap_url])
        visited_sitemaps = set()
        discovered = []
        seen_pages = set()

    while pending and len(visited_sitemaps) < max_sitemaps:
        current = pending.popleft()
        current = normalize_url(current)

        if current in visited_sitemaps:
            continue

        if not is_allowed_sitemap_url(current, engine):
            continue

        try:
            xml_content = fetch_sitemap(
                current,
                session,
                robots,
                engine,
            )

            page_urls, nested_sitemaps = parse_sitemap(xml_content)

        except (requests.RequestException, ValueError, PermissionError):
            if progress_file is not None:
                save_crawl_progress(
                    progress_file,
                    pending_sitemaps=[current, *pending],
                    visited_sitemaps=sorted(visited_sitemaps),
                    discovered_urls=discovered,
                )
            raise

        visited_sitemaps.add(current)

        for url in page_urls:
            try:
                normalized = normalize_url(url)
            except ValueError:
                continue

            if not is_allowed_documentation_url(normalized, engine):
                continue

            if normalized in seen_pages:
                continue

            if not robots.can_fetch(USER_AGENT, normalized):
                continue

            seen_pages.add(normalized)
            discovered.append(normalized)

            if len(discovered) >= max_pages:
                if progress_file is not None:
                    save_crawl_progress(
                        progress_file,
                        pending_sitemaps=[current, *pending],
                        visited_sitemaps=sorted(
                            visited_sitemaps - {current}
                        ),
                        discovered_urls=discovered,
                    )

                return discovered

        for nested_url in nested_sitemaps:
            if is_allowed_sitemap_url(nested_url, engine):
                normalized = normalize_url(nested_url)

                if normalized not in visited_sitemaps:
                    pending.append(normalized)

        if progress_file is not None:
            save_crawl_progress(
                progress_file,
                pending_sitemaps=list(pending),
                visited_sitemaps=sorted(visited_sitemaps),
                discovered_urls=discovered,
            )

    return discovered

def extract_documentation_links(
    html: str,
    page_url: str,
    engine: str,
) -> list[str]:
    """Extract approved documentation URLs from an HTML page."""

    soup = BeautifulSoup(html, "html.parser")
    discovered = set()

    for anchor in soup.select("a[href]"):
        href = anchor.get("href")

        if not href:
            continue

        try:
            normalized = normalize_url(
                href,
                base_url=page_url,
            )
        except ValueError:
            continue

        if normalized and is_allowed_documentation_url(
            normalized,
            engine,
        ):
            discovered.add(normalized)

    return sorted(discovered)

def fetch_documentation_page(
    url: str,
    engine: str,
    session: requests.Session,
    robots: RobotFileParser,
) -> str:
    """Download an approved documentation page."""

    if not is_allowed_documentation_url(url, engine):
        raise ValueError(f"Unapproved documentation URL: {url}")

    if not robots.can_fetch(USER_AGENT, url):
        raise PermissionError(
            f"robots.txt does not permit fetching: {url}"
        )

    content = download_limited(
        url,
        session,
        max_bytes=5 * 1024 * 1024,
    )

    return content.decode("utf-8-sig", errors="replace")

def crawl_documentation_links(
    start_url: str,
    engine: str,
    session: requests.Session,
    robots: RobotFileParser,
    max_pages: int = 20,
    delay_seconds: float = 1.0,
    include_discovered: bool = False,
) -> list[str]:
    """Discover documentation URLs using bounded breadth-first crawling."""

    if max_pages < 1:
        raise ValueError("max_pages must be at least 1")

    if delay_seconds < 0:
        raise ValueError("delay_seconds cannot be negative")

    if not is_allowed_documentation_url(start_url, engine):
        raise ValueError(f"Unapproved start URL: {start_url}")

    queue = deque([start_url])
    seen = {start_url}
    visited = []

    while queue and len(visited) < max_pages:
        url = queue.popleft()

        if not robots.can_fetch(USER_AGENT, url):
            continue

        if visited:
            time.sleep(delay_seconds)

        html = fetch_documentation_page(
            url,
            engine,
            session,
            robots,
        )

        visited.append(url)

        for link in extract_documentation_links(
            html,
            url,
            engine,
        ):
            if link not in seen:
                seen.add(link)
                queue.append(link)

    if include_discovered:
        return sorted(
            url for url in seen
            if robots.can_fetch(USER_AGENT, url)
        )

    return visited


    base = "https://docs.godotengine.org/en/stable/"
    page_one = base + "classes/class_node2d.html"
    page_two = base + "classes/class_rigidbody2d.html"
    blocked = base + "private/secret.html"

    html = f"""
    <html>
        <a href="{page_one}">Node2D</a>
        <a href="{page_two}">RigidBody2D</a>
        <a href="{page_one}#methods">Duplicate</a>
        <a href="{blocked}">Blocked</a>
    </html>
    """

    session = Mock()
    robots = Mock()
    robots.can_fetch.side_effect = (
        lambda agent, url: url != blocked
    )

    with patch(
        "documentation_discovery.fetch_documentation_page"
    ) as mock_fetch:
        mock_fetch.return_value = html

        discovered = crawl_documentation_links(
            start_url=base,
            engine="godot",
            session=session,
            robots=robots,
            max_pages=1,
            delay_seconds=0,
            include_discovered=True,
        )

    assert discovered == sorted([
        base,
        page_one,
        page_two,
    ])

    mock_fetch.assert_called_once()