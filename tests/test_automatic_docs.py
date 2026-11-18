import json
from unittest.mock import Mock, patch
import requests
from automatic_docs import (
    download_documentation_batch,
    filename_for_url,
)


def test_download_documentation_batch(tmp_path):
    url = (
        "https://docs.godotengine.org/en/stable/"
        "classes/class_node2d.html"
    )

    session = Mock()
    robots = Mock()

    sample_html = """
    <html>
        <main>
            <h1>Node2D</h1>
            <p>
                Node2D is a 2D game object that supports
                positioning, rotation, scaling, and
                transformations in the Godot engine.
                It is commonly used as a parent for
                other 2D nodes in a scene.
            </p>
        </main>
    </html>
    """

    with patch(
        "automatic_docs.fetch_documentation_page",
        return_value=sample_html,
    ) as mock_fetch:

        changed = download_documentation_batch(
            urls=[url],
            engine="godot",
            session=session,
            robots=robots,
            output_dir=tmp_path,
            max_pages=1,
            delay_seconds=0,
        )

    filename = filename_for_url(url)

    assert changed == 1
    assert (tmp_path / filename).exists()

    saved_text = (tmp_path / filename).read_text(
        encoding="utf-8"
    )

    assert "Node2D" in saved_text

    manifest = json.loads(
        (tmp_path / "sources.json").read_text(
            encoding="utf-8"
        )
    )

    assert manifest[filename] == url
    mock_fetch.assert_called_once_with(
        url, "godot", session, robots
    )

def test_download_documentation_batch_skips_unchanged(tmp_path):
    url = (
        "https://docs.godotengine.org/en/stable/"
        "classes/class_node2d.html"
    )

    session = Mock()
    robots = Mock()

    sample_html = """
    <html>
        <main>
            <h1>Node2D</h1>
            <p>
                Node2D provides positioning, rotation,
                scaling, and transformations for 2D game
                objects. It is a fundamental component
                of Godot's scene system and supports
                hierarchical node relationships.
            </p>
        </main>
    </html>
    """

    with patch(
        "automatic_docs.fetch_documentation_page",
        return_value=sample_html,
    ):
        first_result = download_documentation_batch(
            urls=[url],
            engine="godot",
            session=session,
            robots=robots,
            output_dir=tmp_path,
            max_pages=1,
            delay_seconds=0,
        )

        second_result = download_documentation_batch(
            urls=[url],
            engine="godot",
            session=session,
            robots=robots,
            output_dir=tmp_path,
            max_pages=1,
            delay_seconds=0,
        )

    assert first_result == 1
    assert second_result == 0

    filename = filename_for_url(url)
    assert (tmp_path / filename).exists()

def test_download_documentation_batch_respects_delay(tmp_path):
    base = "https://docs.godotengine.org/en/stable/classes/"

    urls = [
        base + "class_node2d.html",
        base + "class_rigidbody2d.html",
        base + "class_node3d.html",
    ]

    sample_html = """
    <html>
        <main>
            <h1>Godot Documentation</h1>
            <p>
                This documentation describes the Godot
                game engine, its nodes, properties,
                methods, scene structure, transformations,
                and other features used in game development.
            </p>
        </main>
    </html>
    """

    session = Mock()
    robots = Mock()

    with (
        patch(
            "automatic_docs.fetch_documentation_page",
            return_value=sample_html,
        ) as mock_fetch,
        patch("automatic_docs.time.sleep") as mock_sleep,
    ):
        changed = download_documentation_batch(
            urls=urls,
            engine="godot",
            session=session,
            robots=robots,
            output_dir=tmp_path,
            max_pages=3,
            delay_seconds=1.0,
        )

    assert changed == 3
    assert mock_fetch.call_count == 3

    # Three downloads require two delays.
    assert mock_sleep.call_count == 2
    mock_sleep.assert_any_call(1.0)

def test_download_continues_after_network_failure(tmp_path):
    base = "https://docs.godotengine.org/en/stable/classes/"

    urls = [
        base + "class_node2d.html",
        base + "class_rigidbody2d.html",
    ]

    sample_html = """
    <html>
        <main>
            <h1>RigidBody2D</h1>
            <p>
                RigidBody2D is a physics body controlled
                by the Godot physics engine. It supports
                collisions, forces, impulses, velocity,
                and interactions with other physics bodies.
            </p>
        </main>
    </html>
    """

    with (
        patch(
            "automatic_docs.fetch_documentation_page",
            side_effect=[
                requests.exceptions.Timeout("Connection timed out"),
                sample_html,
            ],
        ) as mock_fetch,
        patch("automatic_docs.time.sleep"),
    ):
        changed = download_documentation_batch(
            urls=urls,
            engine="godot",
            session=Mock(),
            robots=Mock(),
            output_dir=tmp_path,
            max_pages=2,
            delay_seconds=0,
        )

    assert changed == 1
    assert mock_fetch.call_count == 2

    failed_filename = filename_for_url(urls[0])
    successful_filename = filename_for_url(urls[1])

    assert not (tmp_path / failed_filename).exists()
    assert (tmp_path / successful_filename).exists()

    manifest = json.loads(
        (tmp_path / "sources.json").read_text(encoding="utf-8")
    )

    assert failed_filename not in manifest
    assert manifest[successful_filename] == urls[1]

def test_manifest_survives_interrupted_batch(tmp_path):
    import json
    import requests
    from unittest.mock import Mock, patch

    from automatic_docs import (
        download_documentation_batch,
        filename_for_url,
    )

    urls = [
        "https://docs.godotengine.org/en/stable/classes/class_node2d.html",
        "https://docs.godotengine.org/en/stable/classes/class_node3d.html",
    ]

    sample_html = """
    <html>
        <main>
            <h1>Node2D</h1>
            <p>
                Documentation for a Godot scene node.
                This page describes node properties,
                transformations, and usage examples.
            </p>
        </main>
    </html>
    """

    def simulated_fetch(url, engine, session, robots):
        if url == urls[1]:
            raise KeyboardInterrupt("Simulated interruption")
        return sample_html

    with patch(
        "automatic_docs.fetch_documentation_page",
        side_effect=simulated_fetch,
    ):
        try:
            download_documentation_batch(
                urls=urls,
                engine="godot",
                session=Mock(),
                robots=Mock(),
                output_dir=tmp_path,
                max_pages=2,
                delay_seconds=0,
            )
        except KeyboardInterrupt:
            pass

    manifest_path = tmp_path / "sources.json"

    assert manifest_path.exists()

    sources = json.loads(
        manifest_path.read_text(encoding="utf-8")
    )

    assert sources[filename_for_url(urls[0])] == urls[0]
    assert filename_for_url(urls[1]) not in sources

def test_batch_continues_with_pending_urls(tmp_path):
    from unittest.mock import Mock, patch

    urls = [
        f"https://docs.godotengine.org/en/stable/classes/class_test{i}.html"
        for i in range(3)
    ]

    html = "<main>" + ("Documentation content. " * 10) + "</main>"

    with patch(
        "automatic_docs.fetch_documentation_page",
        return_value=html,
    ) as mock_fetch:
        for _ in range(2):
            download_documentation_batch(
                urls=urls,
                engine="godot",
                session=Mock(),
                robots=Mock(),
                output_dir=tmp_path,
                max_pages=2,
                delay_seconds=0,
                refresh=False,
            )

    fetched_urls = [
        call.args[0]
        for call in mock_fetch.call_args_list
    ]

    assert fetched_urls == urls

def test_failed_url_does_not_block_later_batches(tmp_path):
    from unittest.mock import Mock, patch

    urls = [
        f"https://docs.godotengine.org/en/stable/classes/class_test{i}.html"
        for i in range(3)
    ]

    html = "<main>" + ("Documentation content. " * 10) + "</main>"

    def mock_fetch(url, *args, **kwargs):
        if url in urls[:2]:
            raise requests.exceptions.Timeout("Persistent failure")
        return html

    with patch(
        "automatic_docs.fetch_documentation_page",
        side_effect=mock_fetch,
    ) as mocked_fetch:
        for _ in range(2):
            download_documentation_batch(
                urls=urls,
                engine="godot",
                session=Mock(),
                robots=Mock(),
                output_dir=tmp_path,
                max_pages=2,
                delay_seconds=0,
                refresh=False,
            )

    fetched_urls = [
        call.args[0]
        for call in mocked_fetch.call_args_list
    ]

    assert urls[2] in fetched_urls

def test_retry_failed_url_clears_failure_record(tmp_path):
    from unittest.mock import Mock, patch

    url = (
        "https://docs.godotengine.org/en/stable/"
        "classes/class_node2d.html"
    )

    html = "<main>" + ("Documentation content. " * 10) + "</main>"

    with patch(
        "automatic_docs.fetch_documentation_page",
        side_effect=requests.exceptions.Timeout("Temporary failure"),
    ):
        download_documentation_batch(
            urls=[url],
            engine="godot",
            session=Mock(),
            robots=Mock(),
            output_dir=tmp_path,
            max_pages=1,
            delay_seconds=0,
            refresh=False,
        )

    failed_path = tmp_path / "failed_urls.json"
    assert url in json.loads(failed_path.read_text())

    with patch(
        "automatic_docs.fetch_documentation_page",
        return_value=html,
    ):
        download_documentation_batch(
            urls=[url],
            engine="godot",
            session=Mock(),
            robots=Mock(),
            output_dir=tmp_path,
            max_pages=1,
            delay_seconds=0,
            refresh=False,
            retry_failed=True,
        )

    assert (tmp_path / filename_for_url(url)).exists()
    assert url not in json.loads(failed_path.read_text())