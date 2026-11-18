import pytest
from unittest.mock import Mock, MagicMock
from unittest.mock import patch
from documentation_discovery import (
    discover_from_sitemaps,
    parse_sitemap,
    load_robots,
    fetch_sitemap,
    fetch_documentation_page,
    is_allowed_documentation_url,
    normalize_url,
    extract_documentation_links,
    USER_AGENT,
    crawl_documentation_links,
)

@pytest.mark.parametrize(
    "engine,url",
    [
        (
            "unity",
            "https://docs.unity3d.com/6000.0/Documentation/"
            "ScriptReference/Rigidbody.html",
        ),
        (
            "godot",
            "https://docs.godotengine.org/en/stable/"
            "classes/class_node2d.html",
        ),
        (
            "unreal",
            "https://dev.epicgames.com/documentation/en-us/"
            "unreal-engine/actors-in-unreal-engine",
        ),
    ],
)
def test_official_documentation_urls_are_allowed(engine, url):
    assert is_allowed_documentation_url(url, engine)

def mock_streaming_response(content: str):
    response = MagicMock()

    response.is_redirect = False
    response.headers = {}
    response.iter_content.return_value = [
        content.encode("utf-8")
    ]

    # Make the context manager return this exact response.
    response.__enter__.return_value = response
    response.__exit__.return_value = False

    return response


@pytest.mark.parametrize(
    "engine,url",
    [
        ("unity", "https://example.com/documentation"),
        ("godot", "https://docs.unity3d.com/"),
        ("unreal", "https://evil.example.com/"),
        ("unity", "http://docs.unity3d.com/6000.0/Documentation/Manual/"),
        ("godot", "javascript:alert(1)"),
        (
            "unreal",
            "https://dev.epicgames.com.evil.com/"
            "documentation/en-us/unreal-engine/",
        ),
    ],
)
def test_unapproved_urls_are_rejected(engine, url):
    assert not is_allowed_documentation_url(url, engine)


def test_normalize_url_removes_fragment_and_query():
    url = "https://docs.godotengine.org/en/stable/classes/class_node2d.html?x=1#methods"

    assert normalize_url(url) == (
        "https://docs.godotengine.org/en/stable/"
        "classes/class_node2d.html"
    )


def test_normalize_relative_url():
    assert normalize_url(
        "../class_node2d.html",
        "https://docs.godotengine.org/en/stable/classes/example/",
    ) == (
        "https://docs.godotengine.org/en/stable/"
        "classes/class_node2d.html"
    )


def test_unsupported_engine_raises_error():
    with pytest.raises(ValueError, match="Unsupported engine"):
        is_allowed_documentation_url(
            "https://example.com",
            "unknown",
        )

def test_parse_standard_sitemap():
    xml = """
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        <url>
            <loc>https://example.com/page-one</loc>
        </url>
        <url>
            <loc>https://example.com/page-two</loc>
        </url>
    </urlset>
    """

    pages, nested = parse_sitemap(xml)

    assert pages == [
        "https://example.com/page-one",
        "https://example.com/page-two",
    ]
    assert nested == []


def test_parse_sitemap_index():
    xml = """
    <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        <sitemap>
            <loc>https://example.com/sitemap-1.xml</loc>
        </sitemap>
        <sitemap>
            <loc>https://example.com/sitemap-2.xml</loc>
        </sitemap>
    </sitemapindex>
    """

    pages, nested = parse_sitemap(xml)

    assert pages == []
    assert nested == [
        "https://example.com/sitemap-1.xml",
        "https://example.com/sitemap-2.xml",
    ]


def test_parse_invalid_sitemap():
    with pytest.raises(ValueError):
        parse_sitemap("<invalid>")


def test_load_robots_parses_rules():
    session = Mock()

    session.get.return_value = mock_streaming_response(
        """
User-agent: LudexDocumentationCrawler
Disallow: /private/
Allow: /public/
"""
    )

    robots = load_robots(
        "https://docs.godotengine.org",
        session,
    )

    assert robots.can_fetch(
        "LudexDocumentationCrawler/1.0",
        "https://docs.godotengine.org/public/page.html",
    )

    assert not robots.can_fetch(
        "LudexDocumentationCrawler/1.0",
        "https://docs.godotengine.org/private/page.html",
    )

    session.get.assert_called_once_with(
        "https://docs.godotengine.org/robots.txt",
        timeout=(5, 20),
        allow_redirects=False,
        stream=True,
    )


def test_fetch_sitemap_rejects_disallowed_url():
    session = Mock()

    robots = Mock()
    robots.can_fetch.return_value = False

    with pytest.raises(PermissionError):
        fetch_sitemap(
            "https://docs.godotengine.org/sitemap.xml",
            session,
            robots,
            engine="godot",
        )

    session.get.assert_not_called()


def test_fetch_sitemap_accepts_allowed_url():
    session = Mock()
    session.get.return_value = mock_streaming_response(
        "<urlset></urlset>"
    )

    robots = Mock()
    robots.can_fetch.return_value = True

    result = fetch_sitemap(
        "https://docs.godotengine.org/sitemap.xml",
        session,
        robots,
        engine="godot",
    )

    assert result == "<urlset></urlset>"

    session.get.assert_called_once_with(
        "https://docs.godotengine.org/sitemap.xml",
        timeout=(5, 20),
        allow_redirects=False,
        stream=True,
    )

def test_discover_from_nested_sitemaps():
    base = "https://docs.godotengine.org"

    sitemap_index = """
    <sitemapindex>
        <sitemap>
            <loc>https://docs.godotengine.org/part1.xml</loc>
        </sitemap>
        <sitemap>
            <loc>https://docs.godotengine.org/part2.xml</loc>
        </sitemap>
    </sitemapindex>
    """

    sitemap_one = """
    <urlset>
        <url>
            <loc>https://docs.godotengine.org/en/stable/classes/class_node2d.html</loc>
        </url>
        <url>
            <loc>https://docs.godotengine.org/en/stable/classes/class_rigidbody2d.html</loc>
        </url>
    </urlset>
    """

    sitemap_two = """
    <urlset>
        <url>
            <loc>https://docs.godotengine.org/en/stable/classes/class_node2d.html</loc>
        </url>
        <url>
            <loc>https://example.com/unrelated.html</loc>
        </url>
    </urlset>
    """

    sitemap_contents = {
        f"{base}/sitemap.xml": sitemap_index,
        f"{base}/part1.xml": sitemap_one,
        f"{base}/part2.xml": sitemap_two,
    }

    session = Mock()

    def mock_get(url, **kwargs):
        return mock_streaming_response(sitemap_contents[url])

    session.get.side_effect = mock_get

    robots = Mock()
    robots.can_fetch.return_value = True

    discovered = discover_from_sitemaps(
        sitemap_url=f"{base}/sitemap.xml",
        engine="godot",
        session=session,
        robots=robots,
        max_pages=2,
        max_sitemaps=3,
    )

    assert discovered == [
        f"{base}/en/stable/classes/class_node2d.html",
        f"{base}/en/stable/classes/class_rigidbody2d.html",
    ]

    assert session.get.call_count == 2

def test_discover_all_nested_sitemaps():
    base = "https://docs.godotengine.org"

    sitemap_contents = {
        f"{base}/sitemap.xml": f"""
            <sitemapindex>
                <sitemap><loc>{base}/part1.xml</loc></sitemap>
                <sitemap><loc>{base}/part2.xml</loc></sitemap>
            </sitemapindex>
        """,
        f"{base}/part1.xml": f"""
            <urlset>
                <url>
                    <loc>{base}/en/stable/classes/class_node2d.html</loc>
                </url>
            </urlset>
        """,
        f"{base}/part2.xml": f"""
            <urlset>
                <url>
                    <loc>{base}/en/stable/classes/class_node3d.html</loc>
                </url>
            </urlset>
        """,
    }

    session = Mock()

    def mock_get(url, **kwargs):
        return mock_streaming_response(sitemap_contents[url])

    session.get.side_effect = mock_get

    robots = Mock()
    robots.can_fetch.return_value = True

    discovered = discover_from_sitemaps(
        sitemap_url=f"{base}/sitemap.xml",
        engine="godot",
        session=session,
        robots=robots,
        max_pages=100,
        max_sitemaps=3,
    )

    assert discovered == [
        f"{base}/en/stable/classes/class_node2d.html",
        f"{base}/en/stable/classes/class_node3d.html",
    ]

    assert session.get.call_count == 3

def test_extract_documentation_links_filters_and_deduplicates():
    html = """
    <html>
        <body>
            <a href="/en/stable/classes/class_node2d.html">Node2D</a>
            <a href="/en/stable/classes/class_node2d.html#methods">Node2D methods</a>
            <a href="classes/class_rigidbody2d.html">RigidBody2D</a>
            <a href="https://example.com/unrelated.html">External</a>
            <a href="/en/latest/classes/class_node3d.html">Other version</a>
            <a href="javascript:alert(1)">Invalid</a>
        </body>
    </html>
    """

    links = extract_documentation_links(
        html,
        "https://docs.godotengine.org/en/stable/",
        "godot",
    )

    assert links == [
        "https://docs.godotengine.org/en/stable/classes/class_node2d.html",
        "https://docs.godotengine.org/en/stable/classes/class_rigidbody2d.html",
    ]


def test_extract_documentation_links_handles_empty_html():
    links = extract_documentation_links(
        "<html><body>No links here</body></html>",
        "https://docs.godotengine.org/en/stable/",
        "godot",
    )

    assert links == []

def test_fetch_documentation_page_success():
    session = Mock()
    session.get.return_value = mock_streaming_response(
        "<html><body>Godot documentation</body></html>"
    )

    robots = Mock()
    robots.can_fetch.return_value = True

    url = "https://docs.godotengine.org/en/stable/classes/class_node2d.html"

    html = fetch_documentation_page(
        url,
        "godot",
        session,
        robots,
    )

    assert "Godot documentation" in html
    robots.can_fetch.assert_called_once_with(USER_AGENT, url)

    session.get.assert_called_once_with(
        url,
        timeout=(5, 20),
        allow_redirects=False,
        stream=True,
    )


def test_fetch_documentation_page_rejects_disallowed_url():
    session = Mock()
    robots = Mock()
    robots.can_fetch.return_value = True

    with pytest.raises(ValueError, match="Unapproved documentation URL"):
        fetch_documentation_page(
            "https://example.com/malicious.html",
            "godot",
            session,
            robots,
        )

    session.get.assert_not_called()

def test_crawl_documentation_links_respects_page_limit():
    base = "https://docs.godotengine.org/en/stable/"

    page_one = base + "classes/class_node2d.html"
    page_two = base + "classes/class_rigidbody2d.html"

    homepage_html = f"""
    <html>
        <a href="{page_one}">Node2D</a>
        <a href="{page_two}">RigidBody2D</a>
        <a href="{page_one}#methods">Duplicate Node2D</a>
    </html>
    """

    session = Mock()
    robots = Mock()
    robots.can_fetch.return_value = True

    with patch(
        "documentation_discovery.fetch_documentation_page"
    ) as mock_fetch, patch(
        "documentation_discovery.time.sleep"
    ) as mock_sleep:

        mock_fetch.side_effect = [
            homepage_html,
            "<html>No more links</html>",
        ]

        visited = crawl_documentation_links(
            start_url=base,
            engine="godot",
            session=session,
            robots=robots,
            max_pages=2,
            delay_seconds=0.5,
        )

    assert len(visited) == 2
    assert visited[0] == base
    assert len(set(visited)) == 2

    assert mock_fetch.call_count == 2
    mock_sleep.assert_called_once_with(0.5)

def test_crawl_documentation_links_skips_robots_disallowed_pages():
    base = "https://docs.godotengine.org/en/stable/"
    allowed_url = base + "classes/class_node2d.html"
    blocked_url = base + "private/secret.html"

    homepage_html = f"""
    <html>
        <a href="{allowed_url}">Allowed</a>
        <a href="{blocked_url}">Blocked</a>
    </html>
    """

    session = Mock()
    robots = Mock()

    def can_fetch(user_agent, url):
        return url != blocked_url

    robots.can_fetch.side_effect = can_fetch

    with patch(
        "documentation_discovery.fetch_documentation_page"
    ) as mock_fetch, patch(
        "documentation_discovery.time.sleep"
    ) as mock_sleep:

        mock_fetch.side_effect = [
            homepage_html,
            "<html>No more links</html>",
        ]

        visited = crawl_documentation_links(
            start_url=base,
            engine="godot",
            session=session,
            robots=robots,
            max_pages=3,
            delay_seconds=0.5,
        )

    assert base in visited
    assert allowed_url in visited
    assert blocked_url not in visited

    assert mock_fetch.call_count == 2
    assert all(
        call.args[0] != blocked_url
        for call in mock_fetch.call_args_list
    )

    mock_sleep.assert_called_once_with(0.5)

def test_crawl_documentation_links_returns_discovered_urls():
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


def test_sitemap_discovery_saves_progress(tmp_path):
    base = "https://docs.godotengine.org"
    progress_file = tmp_path / "discovery.json"

    sitemap_contents = {
        f"{base}/sitemap.xml": f"""
            <sitemapindex>
                <sitemap><loc>{base}/part1.xml</loc></sitemap>
                <sitemap><loc>{base}/part2.xml</loc></sitemap>
            </sitemapindex>
        """,
        f"{base}/part1.xml": f"""
            <urlset>
                <url>
                    <loc>{base}/en/stable/classes/class_node2d.html</loc>
                </url>
            </urlset>
        """,
        f"{base}/part2.xml": f"""
            <urlset>
                <url>
                    <loc>{base}/en/stable/classes/class_node3d.html</loc>
                </url>
            </urlset>
        """,
    }

    session = Mock()
    session.get.side_effect = lambda url, **kwargs: (
        mock_streaming_response(sitemap_contents[url])
    )

    robots = Mock()
    robots.can_fetch.return_value = True

    first_batch = discover_from_sitemaps(
        sitemap_url=f"{base}/sitemap.xml",
        engine="godot",
        session=session,
        robots=robots,
        max_pages=100,
        max_sitemaps=2,
        progress_file=progress_file,
    )

    assert first_batch == [
        f"{base}/en/stable/classes/class_node2d.html",
    ]

    second_batch = discover_from_sitemaps(
        sitemap_url=f"{base}/sitemap.xml",
        engine="godot",
        session=session,
        robots=robots,
        max_pages=100,
        max_sitemaps=3,
        progress_file=progress_file,
    )

    assert second_batch == [
        f"{base}/en/stable/classes/class_node2d.html",
        f"{base}/en/stable/classes/class_node3d.html",
    ]

    assert session.get.call_count == 3

def test_sitemap_discovery_resumes_after_download_failure(tmp_path):
    import requests

    base = "https://docs.godotengine.org"
    progress_file = tmp_path / "discovery.json"

    sitemap_contents = {
        f"{base}/sitemap.xml": f"""
            <sitemapindex>
                <sitemap><loc>{base}/part1.xml</loc></sitemap>
            </sitemapindex>
        """,
        f"{base}/part1.xml": f"""
            <urlset>
                <url>
                    <loc>{base}/en/stable/classes/class_node2d.html</loc>
                </url>
            </urlset>
        """,
    }

    session = Mock()
    attempts = {"part1": 0}

    def mock_get(url, **kwargs):
        if url.endswith("/part1.xml"):
            attempts["part1"] += 1

            if attempts["part1"] == 1:
                raise requests.ConnectionError("Simulated interruption")

        return mock_streaming_response(sitemap_contents[url])

    session.get.side_effect = mock_get

    robots = Mock()
    robots.can_fetch.return_value = True

    with pytest.raises(requests.ConnectionError):
        discover_from_sitemaps(
            sitemap_url=f"{base}/sitemap.xml",
            engine="godot",
            session=session,
            robots=robots,
            max_sitemaps=10,
            progress_file=progress_file,
        )

    discovered = discover_from_sitemaps(
        sitemap_url=f"{base}/sitemap.xml",
        engine="godot",
        session=session,
        robots=robots,
        max_sitemaps=10,
        progress_file=progress_file,
    )

    assert discovered == [
        f"{base}/en/stable/classes/class_node2d.html",
    ]

    assert attempts["part1"] == 2
    assert session.get.call_count == 3