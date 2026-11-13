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
    evon_api_url: str = os.getenv("EVON_API_URL", "https://api.vachana.ai/v1/chat/completions")
    timbre_api_url: str = os.getenv("TIMBRE_API_URL", "https://api.vachana.ai/api/v1/tts/inference")

    # Reasoning Model Provider Architecture ('GNANI_EVON', 'QWEN3_OLLAMA', 'MOCK_DEV_ADAPTER')
    reasoning_provider: str = os.getenv("REASONING_PROVIDER", "MOCK_DEV_ADAPTER")
    ollama_api_url: str = os.getenv("OLLAMA_API_URL", "http://localhost:11434/v1/chat/completions")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "qwen3:8b")

    # Mode & Language defaults
    mock_mode: bool = os.getenv("MOCK_MODE", "true").lower() in ("true", "1", "yes")
    default_conversation_language: str = os.getenv("DEFAULT_CONVERSATION_LANGUAGE", "te") # 'te', 'hi', 'en', 'ta', etc.
    default_interface_language: str = os.getenv("DEFAULT_INTERFACE_LANGUAGE", "en")
    default_language: str = os.getenv("DEFAULT_LANGUAGE", "te")

    # Server settings
    backend_host: str = os.getenv("BACKEND_HOST", "0.0.0.0")
    backend_port: int = int(os.getenv("BACKEND_PORT", "8000"))
    cors_origins: list[str] = [
        origin.strip() 
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000").split(",")
        if origin.strip()
    ]
    max_upload_size_mb: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10"))
    api_timeout_seconds: float = 12.0

settings = Settings()
