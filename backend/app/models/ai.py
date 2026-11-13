from typing import List, Optional
from pydantic import BaseModel, Field

class ConversationMessage(BaseModel):
    role: str # 'user' or 'assistant'
    content: str

class AIChatRequest(BaseModel):
    query: str
    language: str = "te" # 'te', 'hi', 'en'
    conversation_history: List[ConversationMessage] = Field(default_factory=list)
    selected_land_id: Optional[str] = None

class AIChatResponse(BaseModel):
    transcript: str
    response: str
    language: str
    matched_land_ids: List[str] = Field(default_factory=list)
    legal_warnings: List[str] = Field(default_factory=list)
    infrastructure_findings: List[str] = Field(default_factory=list)
    growth_insights: List[str] = Field(default_factory=list)
    audio_base64: Optional[str] = None
    audio_available: bool = False
    ai_mode: str = "MOCK AI"

class SpeakRequest(BaseModel):
    text: str
    language: str = "te"
    character: str = "bhoomi" # 'bhoomi', 'nyaya', 'infra', 'amma'
    voice: Optional[str] = None
    speed: float = 1.0

class SpeakResponse(BaseModel):
    audio_base64: str
    format: str = "audio/wav"
    language: str
    character: str = "bhoomi"
    voice_used: str = "Nalini"
    ai_mode: str = "MOCK AI"
    duration_estimate_sec: float = 2.5

class CharacterSpeechItem(BaseModel):
    character: str # 'bhoomi' | 'nyaya' | 'infra' | 'amma'
    character_name: str
    role: str
    text: str
    voice_id: str
    audio_base64: Optional[str] = None
    duration_sec: float = 3.0
    evidence_badge: str
    sentiment: str = "neutral" # 'welcoming', 'analytical', 'alarmed', 'protective'
    animation_cue: str = "speak" # 'speak', 'explain', 'alert', 'comfort'

class CollaborativeInvestigationRequest(BaseModel):
    query: str
    conversation_language: str = "te" # 'te', 'hi', 'en', 'ta', etc.
    selected_land_id: Optional[str] = None

class CollaborativeInvestigationResponse(BaseModel):
    user_query: str
    conversation_language: str
    matched_land_ids: List[str] = Field(default_factory=list)
    dialogue_sequence: List[CharacterSpeechItem] = Field(default_factory=list)
    model_used: str
    provider: str # 'GNANI_EVON', 'QWEN3_OLLAMA', 'MOCK_DEV_ADAPTER'
    is_live: bool = False
    overall_risk_level: str = "MODERATE" # 'LOW', 'MODERATE', 'HIGH', 'CRITICAL'

class ModelStatusItem(BaseModel):
    model_name: str
    provider: str
    role: str # 'STT', 'REASONING', 'TTS'
    connection_status: str # 'CONNECTED', 'OFFLINE', 'MOCK_FALLBACK'
    is_live: bool = False
    endpoint: str
    last_ping_status: str = "OK"
    last_response_time_ms: float = 0.0
    supported_languages: List[str] = Field(default_factory=list)
    note: str = ""

class AIModelsHealthResponse(BaseModel):
    active_reasoning_provider: str
    prisma_stt: ModelStatusItem
    reasoning: ModelStatusItem
    timbre_tts: ModelStatusItem
    all_live: bool = False
    mock_mode: bool = True
