#!/usr/bin/env python3
"""
Seed Milvus with sample image embeddings for testing.

This script:
1. Connects to Milvus
2. Creates the image_embeddings collection if it doesn't exist
3. Inserts sample embeddings with placeholder image URLs

Run from the ml container:
    python /app/scripts/seed_milvus.py
"""

import os
import sys
import numpy as np
from pymilvus import (
    connections,
    Collection,
    CollectionSchema,
    FieldSchema,
    DataType,
    utility,
)

MILVUS_HOST = os.getenv("MILVUS_HOST", "milvus")
MILVUS_PORT = os.getenv("MILVUS_PORT", "19530")
COLLECTION_NAME = "image_embeddings"
EMBEDDING_DIM = 512


SAMPLE_IMAGES = [
    "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=400",
    "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=400",
    "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400",
    "https://images.unsplash.com/photo-1493246507139-91e8fad9978e?w=400",
    "https://images.unsplash.com/photo-1518837695005-2083093ee35b?w=400",
    "https://images.unsplash.com/photo-1519681393784-d120267933ba?w=400",
    "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400",
    "https://images.unsplash.com/photo-1454496522488-7a8e488e8606?w=400",
    "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=400",
    "https://images.unsplash.com/photo-1486728297118-82a07bc48a28?w=400",
    "https://images.unsplash.com/photo-1505144808419-1957a94ca61e?w=400",
    "https://images.unsplash.com/photo-1475924156734-496f6cac6ec1?w=400",
    "https://images.unsplash.com/photo-1501854140801-50d01698950b?w=400",
    "https://images.unsplash.com/photo-1469474968028-56623f02e42e?w=400",
    "https://images.unsplash.com/photo-1426604966848-d7adac402bff?w=400",
    "https://images.unsplash.com/photo-1472214103451-9374bd1c798e?w=400",
    "https://images.unsplash.com/photo-1465056836041-7f43ac27dcb5?w=400",
    "https://images.unsplash.com/photo-1433086966358-54859d0ed716?w=400",
    "https://images.unsplash.com/photo-1504198453319-5ce911bafcde?w=400",
    "https://images.unsplash.com/photo-1470252649378-9c29740c9fa8?w=400",
]


def create_collection():
    """Create the image embeddings collection."""
    if utility.has_collection(COLLECTION_NAME):
        print(f"Collection '{COLLECTION_NAME}' already exists")
        return Collection(COLLECTION_NAME)

    print(f"Creating collection '{COLLECTION_NAME}'...")

    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="image_url", dtype=DataType.VARCHAR, max_length=512),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=EMBEDDING_DIM),
    ]

    schema = CollectionSchema(
        fields=fields,
        description="Image embeddings for visual search"
    )

    collection = Collection(name=COLLECTION_NAME, schema=schema)

    index_params = {
        "metric_type": "L2",
        "index_type": "IVF_FLAT",
        "params": {"nlist": 128},
    }
    collection.create_index(field_name="embedding", index_params=index_params)

    print(f"Collection '{COLLECTION_NAME}' created successfully")
    return collection


def generate_sample_embeddings(n: int) -> np.ndarray:
    """Generate random embeddings for testing."""
    np.random.seed(42)
    embeddings = np.random.randn(n, EMBEDDING_DIM).astype(np.float32)
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    return embeddings / norms


def seed_data(collection: Collection, image_urls: list[str]):
    """Insert sample data into the collection."""
    n = len(image_urls)
    embeddings = generate_sample_embeddings(n)

    print(f"Inserting {n} sample images...")

    data = [
        image_urls,
        embeddings.tolist(),
    ]

    collection.insert(data)
    collection.flush()

    print(f"Inserted {n} images successfully")


def main():
    print(f"Connecting to Milvus at {MILVUS_HOST}:{MILVUS_PORT}...")

    connections.connect(
        alias="default",
        host=MILVUS_HOST,
        port=MILVUS_PORT,
    )

    print("Connected to Milvus")

    collection = create_collection()

    collection.load()
    current_count = collection.num_entities

    if current_count > 0:
        print(f"Collection already has {current_count} entities")
        response = input("Do you want to add more sample data? [y/N]: ")
        if response.lower() != "y":
            print("Skipping seed data insertion")
            return

    seed_data(collection, SAMPLE_IMAGES)

    collection.load()
    final_count = collection.num_entities
    print(f"Collection now has {final_count} entities")

    print("Seed complete!")


if __name__ == "__main__":
    main()
