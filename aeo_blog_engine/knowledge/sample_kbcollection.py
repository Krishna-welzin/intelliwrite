from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance
import os
from dotenv import load_dotenv

load_dotenv()

def create_sample_collection():
    client = QdrantClient(
        url=os.getenv("QDRANT_URL", "http://localhost:6333"),
        api_key=os.getenv("QDRANT_API_KEY")
    )

    collection_name = "brand_knowledge_base_sample"

    existing = [c.name for c in client.get_collections().collections]

    if collection_name in existing:
        print("ℹ️ brand_knowledge_base_sample already exists")
        return

    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=1536,        # MUST match Gemini embedding size
            distance=Distance.COSINE
        )
    )

    print("✅ brand_knowledge_base_sample created successfully")


if __name__ == "__main__":
    create_sample_collection()
