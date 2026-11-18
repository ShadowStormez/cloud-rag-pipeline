
from unittest.mock import MagicMock, patch
import ingestion_engine
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
    fake_embeddings = MagicMock()
    fake_embeddings.embed_documents.return_value = [[0.1, 0.2, 0.3]]

    # Simulate a document that doesn't exist in Chroma
    fake_db.get.return_value = {
        "ids": [],
        "metadatas": []
    }

    with patch.object(ingest_unity, "DATA_DIR", tmp_path), \
     patch.object(
         ingestion_engine,
         "HuggingFaceEmbeddings",
         return_value=fake_embeddings
     ), \
     patch.object(ingestion_engine, "Chroma", return_value=fake_db):

        ingest_unity.ingest_documents()

    # Check that embeddings were generated
    fake_embeddings.embed_documents.assert_called_once()

    # Check that chunks were added to Chroma
    fake_db._collection.add.assert_called_once()

    # No old chunks should be deleted
    fake_db._collection.delete.assert_not_called()

    # Inspect the data sent to Chroma
    stored_data = fake_db._collection.add.call_args.kwargs

    assert "Rigidbody2D" in stored_data["documents"][0]
    assert stored_data["embeddings"] == [[0.1, 0.2, 0.3]]

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

    fake_embeddings = MagicMock()

    with patch.object(ingest_unity, "DATA_DIR", tmp_path), \
     patch.object(
         ingestion_engine,
         "HuggingFaceEmbeddings",
         return_value=fake_embeddings
     ), \
     patch.object(ingestion_engine, "Chroma", return_value=fake_db):

        ingest_unity.ingest_documents()

    # No embeddings should be generated
    fake_embeddings.embed_documents.assert_not_called()

    # No new chunks should be inserted
    fake_db._collection.add.assert_not_called()

    # No existing chunks should be deleted
    fake_db._collection.delete.assert_not_called()


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

   
    # Create a fake embedding model
    fake_embeddings = MagicMock()
    fake_embeddings.embed_documents.return_value = [[0.1, 0.2, 0.3]]

    # Track the order of operations
    operations = []

    fake_embeddings.embed_documents.side_effect = (
        lambda texts: (
            operations.append("embed"),
            [[0.1, 0.2, 0.3]]
        )[1]
    )

    fake_db._collection.delete.side_effect = (
        lambda **kwargs: operations.append("delete")
    )

    fake_db._collection.add.side_effect = (
        lambda **kwargs: operations.append("add")
    )

    with patch.object(ingest_unity, "DATA_DIR", tmp_path), \
     patch.object(
         ingestion_engine,
         "HuggingFaceEmbeddings",
         return_value=fake_embeddings
     ), \
     patch.object(ingestion_engine, "Chroma", return_value=fake_db):

        ingest_unity.ingest_documents()

    # Verify the correct operation order
    assert operations == ["embed", "delete", "add"]

    # Verify outdated chunks were deleted
    fake_db._collection.delete.assert_called_once_with(
        ids=["unity-Rigidbody2D-0"]
    )

    # Verify updated chunks were added
    fake_db._collection.add.assert_called_once()

    stored_data = fake_db._collection.add.call_args.kwargs

    assert "updated physics features" in stored_data["documents"][0]
    assert stored_data["embeddings"] == [[0.1, 0.2, 0.3]]

    # Verify the updated hash is stored
    assert stored_data["metadatas"][0]["content_hash"] == calculate_hash(
        new_content
    )


def test_embedding_failure_preserves_old_chunks(tmp_path):
    import pytest
    from utils import calculate_hash

    # Create updated local documentation
    new_content = "Rigidbody2D updated documentation."

    document_file = tmp_path / "Rigidbody2D.txt"
    document_file.write_text(new_content, encoding="utf-8")

    # Simulate an older version in Chroma
    fake_db = MagicMock()
    fake_db.get.return_value = {
        "ids": ["unity-Rigidbody2D-0"],
        "metadatas": [{
            "source": document_file.as_posix(),
            "content_hash": calculate_hash("Old documentation.")
        }]
    }

    # Simulate an embedding model failure
    fake_embeddings = MagicMock()
    fake_embeddings.embed_documents.side_effect = RuntimeError(
        "Embedding generation failed"
    )

    with patch.object(ingest_unity, "DATA_DIR", tmp_path), \
     patch.object(
         ingestion_engine,
         "HuggingFaceEmbeddings",
         return_value=fake_embeddings
     ), \
     patch.object(ingestion_engine, "Chroma", return_value=fake_db):

        # Verify the failure is reported
        with pytest.raises(RuntimeError, match="Embedding generation failed"):
            ingest_unity.ingest_documents()

    # Existing chunks must not be deleted
    fake_db._collection.delete.assert_not_called()

    # No incomplete replacement should be inserted
    fake_db._collection.add.assert_not_called()

def test_metadata_only_update_preserves_embeddings(tmp_path):
    from utils import calculate_hash

    content = "Rigidbody2D controls 2D physics in Unity."
    document_file = tmp_path / "Rigidbody2D.txt"
    document_file.write_text(content, encoding="utf-8")

    source_url = (
        "https://docs.unity3d.com/6000.0/Documentation/"
        "ScriptReference/Rigidbody2D.html"
    )

    fake_db = MagicMock()
    fake_db.get.return_value = {
        "ids": ["unity-Rigidbody2D-0"],
        "metadatas": [
            {
                "source": document_file.as_posix(),
                "source_type": "unity",
                "content_hash": calculate_hash(content),
            }
        ],
    }

    fake_embeddings = MagicMock()

    original_prepare = ingestion_engine.prepare_document

    def prepare_with_url(*args, **kwargs):
        kwargs["source_url"] = source_url
        return original_prepare(*args, **kwargs)

    with patch.object(
        ingestion_engine,
        "prepare_document",
        side_effect=prepare_with_url,
    ), patch.object(
        ingestion_engine,
        "HuggingFaceEmbeddings",
        return_value=fake_embeddings,
    ), patch.object(
        ingestion_engine,
        "Chroma",
        return_value=fake_db,
    ):
        ingestion_engine.ingest_directory(
            data_dir=tmp_path,
            source_type="unity",
        )

    fake_embeddings.embed_documents.assert_not_called()
    fake_db._collection.add.assert_not_called()
    fake_db._collection.delete.assert_not_called()

    fake_db._collection.update.assert_called_once()

    update_args = fake_db._collection.update.call_args.kwargs

    assert update_args["ids"] == ["unity-Rigidbody2D-0"]
    assert update_args["metadatas"][0]["source_url"] == source_url

def test_ingest_document_preserves_source_url(tmp_path):
    import json

    # Create a documentation file
    document_file = tmp_path / "Node2D.txt"
    document_file.write_text(
        "Node2D is a 2D game object in Godot.",
        encoding="utf-8",
    )

    # Create the URL manifest
    official_url = (
        "https://docs.godotengine.org/en/stable/"
        "classes/class_node2d.html"
    )

    manifest = {"Node2D.txt": official_url}

    (tmp_path / "sources.json").write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )

    # Simulate an empty Chroma database
    fake_db = MagicMock()
    fake_db.get.return_value = {
        "ids": [],
        "metadatas": [],
    }

    fake_embeddings = MagicMock()
    fake_embeddings.embed_documents.return_value = [
        [0.1, 0.2, 0.3]
    ]

    with patch.object(
        ingestion_engine,
        "HuggingFaceEmbeddings",
        return_value=fake_embeddings,
    ), patch.object(
        ingestion_engine,
        "Chroma",
        return_value=fake_db,
    ):
        ingestion_engine.ingest_directory(
            data_dir=tmp_path,
            source_type="godot",
        )

    # Verify the metadata actually sent to Chroma
    fake_db._collection.add.assert_called_once()

    stored_data = fake_db._collection.add.call_args.kwargs
    metadata = stored_data["metadatas"][0]

    assert metadata["source_url"] == official_url
    assert metadata["source_type"] == "godot"
    assert metadata["source"] == document_file.as_posix()




