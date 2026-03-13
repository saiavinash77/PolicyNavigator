import os
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv, dotenv_values

ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=True)

_values = dotenv_values(ENV_PATH)
if "GROQ_API_KEY" not in os.environ and "\ufeffGROQ_API_KEY" in _values:
    os.environ["GROQ_API_KEY"] = _values.get("\ufeffGROQ_API_KEY") or ""

class Settings(BaseModel):
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_model: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    embed_model: str = os.getenv("EMBED_MODEL", "BAAI/bge-small-en-v1.5")
    storage_dir: str = os.getenv("STORAGE_DIR", "storage")
    uploads_dir: str = os.getenv("UPLOADS_DIR", "data/uploads")
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "900"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "150"))
    top_k: int = int(os.getenv("TOP_K", "5"))

settings = Settings()


def refresh_settings() -> None:
    load_dotenv(dotenv_path=ENV_PATH, override=True)
    values = dotenv_values(ENV_PATH)
    if "GROQ_API_KEY" not in os.environ and "\ufeffGROQ_API_KEY" in values:
        os.environ["GROQ_API_KEY"] = values.get("\ufeffGROQ_API_KEY") or ""

    settings.groq_api_key = os.getenv("GROQ_API_KEY", "")
    settings.groq_model = os.getenv("GROQ_MODEL", settings.groq_model)
    settings.embed_model = os.getenv("EMBED_MODEL", settings.embed_model)
    settings.storage_dir = os.getenv("STORAGE_DIR", settings.storage_dir)
    settings.uploads_dir = os.getenv("UPLOADS_DIR", settings.uploads_dir)
    settings.chunk_size = int(os.getenv("CHUNK_SIZE", settings.chunk_size))
    settings.chunk_overlap = int(os.getenv("CHUNK_OVERLAP", settings.chunk_overlap))
    settings.top_k = int(os.getenv("TOP_K", settings.top_k))


SYSTEM_PROMPT = (
    "You are PolicyNavigator, a rigorous policy research assistant. "
    "You help analyze laws and public policy with clear, structured answers. "
    "Be concise and structured. Use bullet points when helpful. "
    "Always cite sources when documents are provided. "
    "If you are unsure or the answer is not in the provided context, say so."
)
