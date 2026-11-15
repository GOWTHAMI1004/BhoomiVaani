import os
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BASE_DIR.parent
DATA_DIR = BASE_DIR / "data"
LANDS_FILE = DATA_DIR / "lands.json"
SAMPLE_DOCS_DIR = DATA_DIR / "sample_documents"
DEFAULT_BHOOMI_INTRO_VIDEO = ROOT_DIR / "AI_land_advisor_speaking_to_f5c2f339.mp4"
_configured_intro_video = os.getenv("BHOOMI_INTRO_VIDEO_PATH", "").strip()
# Migrate the known stale Flow filename automatically when the requested source
# asset is present. Other explicitly configured avatar paths remain supported.
if (
    Path(_configured_intro_video).name == "AI_assistant_speaking_to_camera_176b211d.mp4"
    and DEFAULT_BHOOMI_INTRO_VIDEO.is_file()
):
    _configured_intro_video = str(DEFAULT_BHOOMI_INTRO_VIDEO)

# Load .env file from root or backend directory if present
load_dotenv(ROOT_DIR / ".env")
load_dotenv(BASE_DIR / ".env")

class Settings(BaseModel):
    # Gnani AI API configuration
    gnani_api_key: str = os.getenv("GNANI_API_KEY", "")
    prisma_api_url: str = os.getenv("PRISMA_API_URL", "https://api.vachana.ai/stt/v3")
    timbre_api_url: str = os.getenv("TIMBRE_API_URL", "https://api.vachana.ai/api/v1/tts/inference")

    # User-provided Google Flow source clip; served read-only as Bhoomi's introduction.
    bhoomi_intro_video_path: str = _configured_intro_video or str(DEFAULT_BHOOMI_INTRO_VIDEO)
    # A separately hosted MuseTalk (or compatible) GPU service can be configured later.
    lipsync_api_url: str = os.getenv("LIPSYNC_API_URL", "").strip()
    lipsync_api_key: str = os.getenv("LIPSYNC_API_KEY", "")
    ffmpeg_path: str = os.getenv("FFMPEG_PATH", "ffmpeg").strip() or "ffmpeg"
    bhoomi_voice_embedding_path: str = os.getenv(
        "BHOOMI_VOICE_EMBEDDING_PATH",
        str(Path(os.getenv("LOCALAPPDATA") or (Path.home() / ".local" / "share")) / "BhoomiVaani" / "bhoomi-voice-embedding.json"),
    )

    # Provider details are intentionally generic until an external LLM is selected.
    reasoning_provider: str = os.getenv("REASONING_PROVIDER", "").strip()
    reasoning_api_key: str = os.getenv("REASONING_API_KEY", "")
    reasoning_api_base_url: str = os.getenv("REASONING_API_BASE_URL", "").strip()
    reasoning_model: str = os.getenv("REASONING_MODEL", "").strip()

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

    # Land data providers are configured independently. Only local submissions are
    # implemented; selecting any external provider reports unavailable until an
    # explicitly reviewed adapter is added.
    land_listing_provider: str = os.getenv("LAND_LISTING_PROVIDER", "USER_SUBMITTED").strip()
    land_listing_api_key: str = os.getenv("LAND_LISTING_API_KEY", "")
    land_record_provider: str = os.getenv("LAND_RECORD_PROVIDER", "").strip()
    land_record_api_key: str = os.getenv("LAND_RECORD_API_KEY", "")
    land_geocoding_provider: str = os.getenv("LAND_GEOCODING_PROVIDER", "").strip()
    land_geocoding_api_key: str = os.getenv("LAND_GEOCODING_API_KEY", "")
    land_nearby_places_provider: str = os.getenv("LAND_NEARBY_PLACES_PROVIDER", "").strip()
    land_nearby_places_api_key: str = os.getenv("LAND_NEARBY_PLACES_API_KEY", "")
    land_use_provider: str = os.getenv("LAND_USE_PROVIDER", "").strip()
    land_use_api_key: str = os.getenv("LAND_USE_API_KEY", "")
    user_submitted_listings_enabled: bool = os.getenv(
        "USER_SUBMITTED_LISTINGS_ENABLED", "true"
    ).lower() in ("true", "1", "yes")
    user_submitted_lands_file: Path = Path(
        os.getenv("USER_SUBMITTED_LANDS_FILE", "").strip()
        or str(DATA_DIR / "user_submitted_lands.json")
    )

settings = Settings()
