
from unittest.mock import MagicMock, patch

import ingest_unity


def test_ingest_new_document(tmp_path):
    # Create a temporary Unity documentation file
    document_file = tmp_path / "Rigidbody2D.txt"
    document_file.write_text(
        "Rigidbody2D controls 2D physics in Unity.",
        encoding="utf-8"
    )

    # Create a fake Chroma database
    fake_db = MagicMock()

    # Simulate a document that doesn't exist in Chroma
    fake_db.get.return_value = {
        "ids": [],
        "metadatas": []
    }

    # Replace real dependencies with fake ones
    with patch.object(ingest_unity, "DATA_DIR", tmp_path), \
         patch.object(ingest_unity, "HuggingFaceEmbeddings"), \
         patch.object(ingest_unity, "Chroma", return_value=fake_db):

        ingest_unity.ingest_documents()

    # Verify that new chunks were added to Chroma
    fake_db.add_documents.assert_called_once()

    # Verify that no old chunks were deleted
    fake_db.delete.assert_not_called()

    # Inspect the documents sent to Chroma
    documents = fake_db.add_documents.call_args.kwargs["documents"]

    assert len(documents) > 0
    assert "Rigidbody2D" in documents[0].page_content

def test_ingest_unchanged_document(tmp_path):
    # Create a temporary documentation file
    content = "Rigidbody2D controls 2D physics in Unity."

    document_file = tmp_path / "Rigidbody2D.txt"
    document_file.write_text(content, encoding="utf-8")

    # Calculate the hash of the existing document
    from utils import calculate_hash
    existing_hash = calculate_hash(content)

    # Create a fake Chroma database
    fake_db = MagicMock()

    # Simulate a document already stored with the same hash
    fake_db.get.return_value = {
        "ids": ["unity-Rigidbody2D-0"],
        "metadatas": [
            {
                "source": document_file.as_posix(),
                "content_hash": existing_hash
            }
        ]
    }

    with patch.object(ingest_unity, "DATA_DIR", tmp_path), \
         patch.object(ingest_unity, "HuggingFaceEmbeddings"), \
         patch.object(ingest_unity, "Chroma", return_value=fake_db):

        ingest_unity.ingest_documents()

    # No new chunks should be added
    fake_db.add_documents.assert_not_called()

    # No existing chunks should be deleted
    fake_db.delete.assert_not_called()


def test_ingest_updated_document(tmp_path):
    from utils import calculate_hash

    # Create a local file containing updated documentation
    new_content = "Rigidbody2D now supports updated physics features."

    document_file = tmp_path / "Rigidbody2D.txt"
    document_file.write_text(new_content, encoding="utf-8")

    # Simulate an older version already stored in Chroma
    old_content = "Rigidbody2D controls 2D physics."
    old_hash = calculate_hash(old_content)

    fake_db = MagicMock()

    fake_db.get.return_value = {
        "ids": ["unity-Rigidbody2D-0"],
        "metadatas": [
            {
                "source": document_file.as_posix(),
                "content_hash": old_hash
            }
        ]
    }

    # Replace real dependencies with mocks
    with patch.object(ingest_unity, "DATA_DIR", tmp_path), \
         patch.object(ingest_unity, "HuggingFaceEmbeddings"), \
         patch.object(ingest_unity, "Chroma", return_value=fake_db):

        ingest_unity.ingest_documents()

    # Verify outdated chunks were deleted
    fake_db.delete.assert_called_once_with(
        ids=["unity-Rigidbody2D-0"]
    )

    # Verify updated chunks were added
    fake_db.add_documents.assert_called_once()

    documents = fake_db.add_documents.call_args.kwargs["documents"]

    assert "updated physics features" in documents[0].page_content

    # Verify the new hash is stored in the chunk metadata
    assert documents[0].metadata["content_hash"] == calculate_hash(
        new_content
    )


