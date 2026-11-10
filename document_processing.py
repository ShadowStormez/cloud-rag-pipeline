from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from utils import calculate_hash


def prepare_document(
    file_path: Path,
    source_type: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> tuple[str, list[Document]]:
    """Read, hash, and split a documentation file into chunks."""

    if not 0 <= chunk_overlap < chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    content = file_path.read_text(encoding="utf-8")
    content_hash = calculate_hash(content)

    document = Document(
        page_content=content,
        metadata={
            "source": file_path.as_posix(),
            "source_type": source_type,
            "content_hash": content_hash,
        },
    )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    chunks = splitter.split_documents([document])

    return content_hash, chunks