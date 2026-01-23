import sys
from dotenv import load_dotenv
import os
from pathlib import Path
from uuid import uuid4
import time

# Load .env file
load_dotenv()

# Add parent folder of 'aeo_blog_engine' to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qdrant_client.http.models import PointStruct
from aeo_blog_engine.knowledge.knowledge_base import get_knowledge_base

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

# Map brands to their industries
BRAND_INDUSTRY = {
    "LAYS": "Food",
    "Boat": "Direct-to-consumer brand (D2C)",
    "Creative_Gaga": "Media/Entertainment",
    "Formula_1": "Motorsports",
    "JBL": "Sound",
    "KNK_Design_Studio": "SaaS (B2B software)",
    "LinkedIn": "b2c",
    "Media_Wall_Street": "Business & Development",
    "Minimalist": "Skincare",
    "MIVI": "Sound",
    "Nike": "Apparel & Fashion",
    "Nothing": "Mobile",
    "OUD_ARABIA": "Perfume",
    "Premier_Tickets": "E-commerce platforms",
    "Welzin": "AI/ML"
}

# Change this to the industry you want for the sample KB
TARGET_INDUSTRY = "Sound"

def ingest_sample_kb():
    """
    Reads markdown/text files from docs/, filters by TARGET_INDUSTRY,
    and loads them into a new Qdrant collection 'brand_knowledge_base_sample'.
    """
    vector_db = get_knowledge_base()
    qdrant_client = vector_db.client
    embedder = vector_db.embedder

    # New collection for sample KB
    collection_name = "brand_knowledge_base_sample"

    current_dir = os.path.dirname(os.path.abspath(__file__))
    docs_dir = Path(os.path.join(current_dir, "docs"))

    print(f"Scanning documents for industry '{TARGET_INDUSTRY}' in {docs_dir}")

    for root, _, files in os.walk(docs_dir):
        path_parts = Path(root).relative_to(docs_dir).parts
        brand = path_parts[0] if path_parts else "general"

        # Skip brands not in the target industry
        if BRAND_INDUSTRY.get(brand) != TARGET_INDUSTRY:
            continue

        for file_name in files:
            if not (file_name.endswith(".md") or file_name.endswith(".txt")):
                continue

            file_path = Path(root) / file_name
            try:
                content = file_path.read_text(encoding='utf-8')
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
                continue

            if not content.strip():
                continue

            try:
                # Retry logic for 429 (rate limit)
                max_retries = 5
                retry_delay = 10
                for attempt in range(max_retries):
                    try:
                        embedding = embedder.get_embedding(content)
                        break
                    except Exception as e:
                        if "429" in str(e) and attempt < max_retries - 1:
                            print(f"Rate limit hit for {file_name}. Retrying in {retry_delay}s...")
                            time.sleep(retry_delay)
                            retry_delay *= 2
                        else:
                            raise e

                point = PointStruct(
                    id=str(uuid4()),
                    vector=embedding,
                    payload={
                        "name": file_name,
                        "brand": brand,
                        "file_name": file_name,
                        "source": "profile_md",
                        "industry": TARGET_INDUSTRY,
                        "content": content,
                        "content_preview": content[:200]
                    }
                )

                # Upsert to Qdrant
                qdrant_client.upsert(
                    collection_name=collection_name,
                    points=[point],
                    wait=True
                )

                print(f"✓ Saved {file_name} for brand {brand} to sample KB")

            except Exception as e:
                print(f"Error processing {brand}: {e}")

    print("Sample KB ingestion complete.")


if __name__ == "__main__":
    ingest_sample_kb()
