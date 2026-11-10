import pytest

from document_processing import prepare_document
from utils import calculate_hash


def test_prepare_document(tmp_path):
    file_path = tmp_path / "SpriteRenderer.txt"
    content = "SpriteRenderer renders 2D sprites in Unity."

    file_path.write_text(content, encoding="utf-8")

    content_hash, chunks = prepare_document(
        file_path,
        source_type="unity",
    )

    assert content_hash == calculate_hash(content)
    assert len(chunks) == 1
    assert chunks[0].page_content == content

    metadata = chunks[0].metadata

    assert metadata["source"] == file_path.as_posix()
    assert metadata["source_type"] == "unity"
    assert metadata["content_hash"] == content_hash


@pytest.mark.parametrize(
    "source_type",
    ["unity", "godot", "unreal"],
)
def test_prepare_document_supports_multiple_sources(
    tmp_path,
    source_type,
):
    file_path = tmp_path / "documentation.txt"
    file_path.write_text(
        "Example documentation content.",
        encoding="utf-8",
    )

    _, chunks = prepare_document(
        file_path,
        source_type=source_type,
    )

    assert chunks[0].metadata["source_type"] == source_type


def test_prepare_document_rejects_invalid_overlap(tmp_path):
    file_path = tmp_path / "documentation.txt"
    file_path.write_text("Example content.", encoding="utf-8")

    with pytest.raises(ValueError):
        prepare_document(
            file_path,
            source_type="unity",
            chunk_size=100,
            chunk_overlap=100,
        )