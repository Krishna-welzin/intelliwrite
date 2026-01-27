from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance, PayloadSchemaType
import os
from dotenv import load_dotenv

load_dotenv()

def create_sample_collection():
    client = QdrantClient(
        url=os.getenv("QDRANT_URL", "http://localhost:6333"),
        api_key=os.getenv("QDRANT_API_KEY")
    )

    collection_name = os.getenv("COLLECTION_NAME", "brand_knowledge_base_sample")

    existing = [c.name for c in client.get_collections().collections]

    if collection_name in existing:
        print(f"{collection_name} already exists")
    else:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=1536,        # MUST match Gemini embedding size
                distance=Distance.COSINE
            )
        )
        print(f"{collection_name} created successfully")

    # Ensure indexes
    print(f"Ensuring indexes for {collection_name}...")
    for field in ["brand", "industry", "source"]:
        try:
            client.create_payload_index(
                collection_name=collection_name,
                field_name=field,
                field_schema=PayloadSchemaType.KEYWORD,
            )
            print(f" Created keyword index for '{field}'")
        except Exception as e:
            if "already indexed" in str(e).lower():
                print(f"'{field}' is already indexed")
            else:
                print(f" Error creating index for '{field}': {e}")


if __name__ == "__main__":
    create_sample_collection()
