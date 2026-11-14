import os
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BASE_DIR.parent
DATA_DIR = BASE_DIR / "data"
LANDS_FILE = DATA_DIR / "lands.json"
SAMPLE_DOCS_DIR = DATA_DIR / "sample_documents"

# Load .env file from root or backend directory if present
load_dotenv(ROOT_DIR / ".env")
load_dotenv(BASE_DIR / ".env")

class Settings(BaseModel):
    # Gnani AI API configuration
    gnani_api_key: str = os.getenv("GNANI_API_KEY", "")
    prisma_api_url: str = os.getenv("PRISMA_API_URL", "https://api.vachana.ai/stt/v3")
    timbre_api_url: str = os.getenv("TIMBRE_API_URL", "https://api.vachana.ai/api/v1/tts/inference")

    # Evon must be deployed behind the documented vLLM-compatible API.
    reasoning_provider: str = os.getenv("REASONING_PROVIDER", "GNANI_EVON")
    evon_api_base_url: str = os.getenv("EVON_API_BASE_URL", "").rstrip("/")
    evon_model: str = os.getenv("EVON_MODEL", "")

    # Mode & Language defaults
    mock_mode: bool = os.getenv("MOCK_MODE", "false").lower() in ("true", "1", "yes")
    default_conversation_language: str = os.getenv("DEFAULT_CONVERSATION_LANGUAGE", "en") # 'te', 'hi', 'en', 'ta', etc.
    default_interface_language: str = os.getenv("DEFAULT_INTERFACE_LANGUAGE", "en")
    default_language: str = os.getenv("DEFAULT_LANGUAGE", "en")

    # Server settings
    backend_host: str = os.getenv("BACKEND_HOST", "0.0.0.0")
    backend_port: int = int(os.getenv("BACKEND_PORT", "8000"))
    cors_origins: list[str] = [
        origin.strip() 
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000").split(",")
        if origin.strip()
    ]
    max_upload_size_mb: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10"))
    api_timeout_seconds: float = float(os.getenv("AI_REQUEST_TIMEOUT_SECONDS", "60"))
    prisma_timeout_seconds: float = float(os.getenv("PRISMA_REQUEST_TIMEOUT_SECONDS", "120"))

settings = Settings()
