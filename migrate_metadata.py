import os
import chromadb


def migrate_unity_metadata():
    db_dir = os.getenv("CHROMA_DB_DIR", "./chroma_unity_test")

    client = chromadb.PersistentClient(path=db_dir)
    collection = client.get_collection("langchain")

    records = collection.get(
        where={"source": {"$in": [
            "data/unity/SpriteRenderer.txt",
            "data/unity/Rigidbody2D.txt",
        ]}},
        include=["metadatas"],
    )

    updated_ids = []
    updated_metadata = []

    for chunk_id, metadata in zip(
        records["ids"], records["metadatas"]
    ):
        if metadata.get("source_type") == "unity":
            continue

        updated_ids.append(chunk_id)
        updated_metadata.append({
            **metadata,
            "source_type": "unity",
        })

    if updated_ids:
        collection.update(
            ids=updated_ids,
            metadatas=updated_metadata,
        )

    print(f"Updated {len(updated_ids)} Unity chunks.")


if __name__ == "__main__":
    migrate_unity_metadata()