from documentation_selection import select_diverse_urls


def test_select_diverse_unity_documentation():
    base = "https://docs.unity.com/en-us/engine/6000.0/manual"

    urls = [
        f"{base}/physics/rigidbody",
        f"{base}/physics/colliders",
        f"{base}/physics/joints",
        f"{base}/animation/animator",
        f"{base}/animation/clips",
        f"{base}/rendering/materials",
        f"{base}/rendering/shaders",
        f"{base}/audio/audio-sources",
        f"{base}/ui/canvas",
    ]

    selected = select_diverse_urls(
        urls=urls,
        engine="unity",
        max_pages=6,
    )

    assert len(selected) == 6
    assert len(selected) == len(set(selected))
    assert all(url in urls for url in selected)

    # Each topic should receive coverage before any
    # topic receives a second selected page.
    assert any("/physics/" in url for url in selected)
    assert any("/animation/" in url for url in selected)
    assert any("/rendering/" in url for url in selected)
    assert any("/audio/" in url for url in selected)
    assert any("/ui/" in url for url in selected)

def test_select_diverse_godot_documentation():
    base = "https://docs.godotengine.org/en/stable"

    urls = [
        f"{base}/classes/class_node2d.html",
        f"{base}/classes/class_rigidbody2d.html",
        f"{base}/classes/class_animationplayer.html",
        f"{base}/tutorials/physics/index.html",
        f"{base}/tutorials/animation/index.html",
        f"{base}/tutorials/scripting/index.html",
        f"{base}/tutorials/2d/index.html",
    ]

    selected = select_diverse_urls(
        urls=urls,
        engine="godot",
        max_pages=5,
    )

    assert len(selected) == 5
    assert len(selected) == len(set(selected))

    # Class references should not dominate the selection.
    assert any("/classes/" in url for url in selected)
    assert any("/tutorials/physics/" in url for url in selected)
    assert any("/tutorials/animation/" in url for url in selected)
    assert any("/tutorials/scripting/" in url for url in selected)
    assert any("/tutorials/2d/" in url for url in selected)


def test_selection_handles_duplicate_urls():
    urls = [
        "https://docs.godotengine.org/en/stable/tutorials/physics/index.html",
        "https://docs.godotengine.org/en/stable/tutorials/physics/index.html",
        "https://docs.godotengine.org/en/stable/tutorials/animation/index.html",
    ]

    selected = select_diverse_urls(
        urls=urls,
        engine="godot",
        max_pages=10,
    )

    assert len(selected) == 2
    assert len(selected) == len(set(selected))


def test_selection_rejects_invalid_limits():
    import pytest

    with pytest.raises(ValueError):
        select_diverse_urls(
            urls=[],
            engine="godot",
            max_pages=0,
        )


def test_selection_rejects_unsupported_engines():
    import pytest

    with pytest.raises(ValueError):
        select_diverse_urls(
            urls=[],
            engine="unreal",
            max_pages=5,
        )

from documentation_selection import documentation_topic


def test_godot_tutorials_index_topic():
    base = "https://docs.godotengine.org/en/stable"

    assert documentation_topic(
        f"{base}/tutorials/index.html",
        "godot",
    ) == "tutorials"

    assert documentation_topic(
        f"{base}/tutorials/physics/index.html",
        "godot",
    ) == "physics"

    assert documentation_topic(
        f"{base}/tutorials/animation/index.html",
        "godot",
    ) == "animation"