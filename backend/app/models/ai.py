from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, field_validator
from app.models.document import DocumentAnalysisResponse

class ConversationMessage(BaseModel):
    role: str # 'user' or 'assistant'
    content: str

class AIChatRequest(BaseModel):
    query: str
    language: str = "en" # 'te', 'hi', 'en'
    conversation_history: List[ConversationMessage] = Field(default_factory=list)
    selected_land_id: Optional[str] = None

    @field_validator("query")
    @classmethod
    def query_must_contain_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Query must contain non-whitespace text.")
        return value

    @field_validator("language")
    @classmethod
    def normalize_language(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not normalized:
            raise ValueError("Language cannot be empty.")
        if "-" in normalized:
            normalized = normalized.split("-", 1)[0]
        return normalized

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
    audio_error: Optional[str] = None
    ai_mode: str = "UNCONFIGURED"

class SpeakRequest(BaseModel):
    text: str = Field(min_length=1, max_length=600)
    language: str = "en"
    character: Literal["bhoomi", "nyaya", "infra", "amma"] = "bhoomi"
    voice: Optional[str] = None
    speed: float = Field(default=1.0, ge=0.85, le=1.15)

class SpeakResponse(BaseModel):
    audio_base64: str
    format: str = "audio/wav"
    language: str
    character: str = "bhoomi"
    voice_used: str = "Nalini"
    ai_mode: str = "GNANI_TIMBRE_V2.5"
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
    evidence_type: str = "SYNTHETIC_DEMONSTRATION_DATA"
    audio_error: Optional[str] = None
    sentiment: str = "neutral" # 'welcoming', 'analytical', 'alarmed', 'protective'
    animation_cue: str = "speak" # 'speak', 'explain', 'alert', 'comfort'

class CollaborativeInvestigationRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    conversation_language: str = "en" # 'te', 'hi', 'en', 'ta', etc.
    selected_land_id: Optional[str] = None
    conversation_history: List[ConversationMessage] = Field(default_factory=list)
    document_analyses: List[DocumentAnalysisResponse] = Field(default_factory=list, max_length=10)

    @field_validator("query")
    @classmethod
    def query_must_contain_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Question must contain non-whitespace text.")
        return value

    @field_validator("conversation_language")
    @classmethod
    def normalize_conversation_language(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not normalized:
            raise ValueError("Conversation language cannot be empty.")
        if "-" in normalized:
            normalized = normalized.split("-", 1)[0]
        return normalized


class InvestigationReportRequest(BaseModel):
    conversation_history: List[ConversationMessage] = Field(default_factory=list)
    selected_land_id: Optional[str] = None
    document_analyses: List[DocumentAnalysisResponse] = Field(default_factory=list, max_length=10)


class CollaborativeInvestigationResponse(BaseModel):
    user_query: str
    conversation_language: str
    matched_land_ids: List[str] = Field(default_factory=list)
    dialogue_sequence: List[CharacterSpeechItem] = Field(default_factory=list)
    model_used: str
    provider: str # External reasoning provider name, or UNCONFIGURED
    is_live: bool = False
    overall_risk_level: str = "NOT_ASSESSED" # 'NOT_ASSESSED' or 'SYNTHETIC_FLAGS_PRESENT'
    investigation_report: Optional[Dict[str, Any]] = None

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
    available_conversation_languages: List[str] = Field(default_factory=list)
