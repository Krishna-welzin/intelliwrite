import os
import warnings
from dotenv import load_dotenv
from pathlib import Path

# Load .env from project root
env_path = Path(__file__).resolve().parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)


SUPPORTED_MODELS = {
    "gemini-flash": "models/gemini-flash-latest",
    "gemini-pro": "models/gemini-pro-latest",
    "gemini-1.5-flash": "models/gemini-flash-latest",
    "gemini-1.5-pro": "models/gemini-pro-latest",
}


def _normalize_gemini_model(model_name: str) -> str:
    """Map deprecated Gemini model IDs to currently supported ones."""
    if not model_name:
        return "models/gemini-flash-latest"

    normalized = model_name.strip()
    normalized_lower = normalized.lower()

    if normalized_lower.startswith("models/gemini"):
        return normalized

    replacement = SUPPORTED_MODELS.get(normalized_lower)
    if replacement:
        return replacement

    # If it's not a known gemini model, default to gemini-flash
    if not normalized_lower.startswith("models/"):
         # Check if it's just the name without prefix
         if normalized_lower in SUPPORTED_MODELS:
             return SUPPORTED_MODELS[normalized_lower]
             
    warnings.warn(
        f"Model '{model_name}' is not a recognized Gemini model. "
        f"Defaulting to 'models/gemini-flash-latest'.",
        RuntimeWarning,
    )
    return "models/gemini-flash-latest"


class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
    COLLECTION_NAME = os.getenv("COLLECTION_NAME", "aeo_knowledge_base")
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/aeo_blog_db")

    # Gemini configuration (single provider)
    # Prioritize keys that are known to be Gemini keys in this project
    GEMINI_API_KEY = (
        os.getenv("GEMINI_API_KEY") or 
        os.getenv("GOOGLE_API_KEY") or 
        os.getenv("PLANNER_API_KEY") or 
        os.getenv("WRITER_API_KEY") or 
        os.getenv("API")
    )
    MODEL_NAME = _normalize_gemini_model(os.getenv("MODEL_NAME", "models/gemini-flash-latest"))

    DEFAULT_LLM_PROVIDER = "google"
    DEFAULT_LLM_MODEL = MODEL_NAME
    DEFAULT_LLM_API_KEY = GEMINI_API_KEY

    # Agent-specific Configurations (all use Gemini now)
    RESEARCHER_PROVIDER = DEFAULT_LLM_PROVIDER
    RESEARCHER_MODEL = _normalize_gemini_model(os.getenv("RESEARCHER_MODEL", DEFAULT_LLM_MODEL))
    RESEARCHER_API_KEY = DEFAULT_LLM_API_KEY

    PLANNER_PROVIDER = DEFAULT_LLM_PROVIDER
    PLANNER_MODEL = _normalize_gemini_model(os.getenv("PLANNER_MODEL", DEFAULT_LLM_MODEL))
    PLANNER_API_KEY = DEFAULT_LLM_API_KEY

    WRITER_PROVIDER = DEFAULT_LLM_PROVIDER
    WRITER_MODEL = _normalize_gemini_model(os.getenv("WRITER_MODEL", DEFAULT_LLM_MODEL))
    WRITER_API_KEY = DEFAULT_LLM_API_KEY

    OPTIMIZER_PROVIDER = DEFAULT_LLM_PROVIDER
    OPTIMIZER_MODEL = _normalize_gemini_model(os.getenv("OPTIMIZER_MODEL", DEFAULT_LLM_MODEL))
    OPTIMIZER_API_KEY = DEFAULT_LLM_API_KEY

    QA_PROVIDER = DEFAULT_LLM_PROVIDER
    QA_MODEL = _normalize_gemini_model(os.getenv("QA_MODEL", DEFAULT_LLM_MODEL))
    QA_API_KEY = DEFAULT_LLM_API_KEY
