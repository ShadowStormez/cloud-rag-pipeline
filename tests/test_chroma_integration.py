
from pathlib import Path
from tempfile import TemporaryDirectory

from langchain_community.vectorstores import Chroma
from langchain_core.embeddings import FakeEmbeddings

import ingest_unity


def test_real_chroma_insertion():
    with TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create a temporary documentation directory
        data_dir = temp_path / "unity"
        data_dir.mkdir()

        document_file = data_dir / "Rigidbody2D.txt"
        document_file.write_text(
            "Rigidbody2D controls 2D physics in Unity.",
            encoding="utf-8"
        )

        # Use fake embeddings instead of downloading a model
        embeddings = FakeEmbeddings(size=3)

        # Create a real Chroma database in a temporary directory
        db = Chroma(
            persist_directory=str(temp_path / "chroma"),
            embedding_function=embeddings
        )

        # Use the real ingestion logic with temporary dependencies
        from unittest.mock import patch

        with patch.object(ingest_unity, "DATA_DIR", data_dir), \
             patch.object(
                 ingest_unity,
                 "HuggingFaceEmbeddings",
                 return_value=embeddings
             ), \
             patch.object(
                 ingest_unity,
                 "Chroma",
                 return_value=db
             ):

            ingest_unity.ingest_documents()

        # Verify that Chroma actually stored the document
        stored = db.get()

        assert len(stored["ids"]) > 0
        assert "Rigidbody2D" in stored["documents"][0]
