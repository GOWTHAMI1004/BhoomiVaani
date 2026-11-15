export type Language = 'te' | 'hi' | 'en';
export type ConversationLanguage = 'te' | 'hi' | 'en' | 'ta' | 'kn' | 'ml' | 'mr' | 'bn' | 'gu' | 'pa';
export type InvestigationCharacter = 'bhoomi' | 'nyaya' | 'infra' | 'amma';
export type CharacterState = 'idle' | 'listening' | 'thinking' | 'speaking';

export interface Coordinates {
  lat: number;
  lng: number;
}

export type ProvenanceClassification =
  | 'USER_PROVIDED'
  | 'BROKER_PROVIDED'
  | 'EXTERNAL_SOURCE'
  | 'OFFICIALLY_VERIFIED'
  | 'AI_ESTIMATED'
  | 'SYNTHETIC_DEMONSTRATION'
  | 'UNKNOWN';

export interface DataProvenance {
  classification: ProvenanceClassification;
  source_label: string;
  source_url?: string | null;
  last_updated?: string | null;
  evidence_references: string[];
}

export type LandSearchSource = 'demo' | 'live';
export interface LandSearchFilters {
  district?: string;
  min_acres?: number;
  max_acres?: number;
  max_budget_lakhs?: number;
  land_type?: string;
  legal_status?: string;
  search?: string;
}
export type ProviderAvailability =
  | 'CONFIGURED_AVAILABLE'
  | 'CONFIGURED_UNAVAILABLE'
  | 'NOT_CONFIGURED'
  | 'DEMONSTRATION_DATA_ONLY';
export type VerificationStatus =
  | 'NOT_VERIFIED'
  | 'SOURCE_RECORDED'
  | 'INDEPENDENTLY_VERIFIED'
  | 'NOT_APPLICABLE';
export type CoordinatePrecision = 'PARCEL' | 'ADDRESS' | 'LOCALITY' | 'APPROXIMATE' | 'UNKNOWN';
export type PermissionStatus = 'ALLOWED' | 'REQUIRES_ATTRIBUTION' | 'NOT_CONFIRMED' | 'NOT_ALLOWED';

export interface ProviderUsageMetadata {
  display_permission: PermissionStatus;
  retention_permission: PermissionStatus;
  retention_ttl_seconds?: number | null;
  terms_reference?: string | null;
}

export interface NormalizedProviderRecord<T = Record<string, unknown>> {
  provider_name: string;
  provider_record_id: string;
  data: T;
  source_url?: string | null;
  retrieval_timestamp: string;
  provenance_classification: ProvenanceClassification;
  verification_status: VerificationStatus;
  coordinate_precision: CoordinatePrecision;
  attribution_requirements: string[];
  permitted_usage: ProviderUsageMetadata;
}

export interface ProviderStatus {
  provider_type: string;
  provider_name?: string | null;
  availability: ProviderAvailability;
  credentials_configured: boolean;
  message: string;
}

export interface LandProvidersStatus {
  providers: Record<string, ProviderStatus>;
  demonstration_record_count: number;
}

export interface LegalRiskItem {
  risk_type: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  description: string;
  recommended_action: string;
}

export interface InfrastructureEvidence {
  claim: string;
  status: 'Officially announced' | 'Proposed' | 'Under construction' | 'Operational' | 'Unverified claim';
  evidence_source: string;
  distance_km: number;
  confidence: 'High' | 'Medium' | 'Low';
}

export interface LandListing {
  id: string;
  title: string;
  location: string;
  district: string;
  survey_number: string;
  acres: number;
  price_per_acre_lakhs: number;
  total_price_lakhs: number;
  land_type: string;
  legal_status: string;
  legal_risks: LegalRiskItem[];
  upcoming_projects: string[];
  infrastructure_evidence: InfrastructureEvidence[];
  growth_score: number;
  image_url: string;
  description: string;
  coordinates: Coordinates;
  record_provenance?: DataProvenance;
  field_provenance?: Record<string, DataProvenance>;
}

export interface LandStats {
  total_properties: number;
  clean_document_examples: number;
  risk_flagged_properties: number;
  average_growth_score: number;
  records_without_listed_risks?: number;
  districts: string[];
  land_types: string[];
}

export interface ConversationMessage {
  role: 'user' | 'assistant';
  content: string;
  transcript?: string;
  audio_base64?: string;
  matched_land_ids?: string[];
  legal_warnings?: string[];
  infrastructure_findings?: string[];
  growth_insights?: string[];
  ai_mode?: string;
  timestamp: string;
}

export interface AIChatResponse {
  transcript: string;
  response: string;
  language: string;
  matched_land_ids: string[];
  legal_warnings: string[];
  infrastructure_findings: string[];
  growth_insights: string[];
  audio_base64?: string;
  audio_available: boolean;
  audio_error?: string;
  ai_mode: string;
}

export interface CharacterSpeechItem {
  character: InvestigationCharacter;
  character_name: string;
  role: string;
  text: string;
  voice_id: string;
  audio_base64?: string | null;
  audio_error?: string | null;
  duration_sec: number;
  evidence_badge: string;
  evidence_type: string;
  sentiment: string;
  animation_cue: string;
}

export interface InvestigationReport {
  property: {
    id: string | null;
    name: string;
    location: string;
    district: string;
    survey_reference: string;
    area_acres: number | null;
    asking_price_lakhs: number | null;
    land_type: string;
  };
  ownership_and_title: { status: string; detail: string };
  document_analysis: { status: string; detail: string };
  encumbrance_indicators: Array<{
    risk_type: string;
    severity: string;
    description: string;
    recommended_action: string;
  }>;
  survey_and_boundary: { status: string; detail: string };
  infrastructure: InfrastructureEvidence[];
  potential_risks: LegalRiskItem[];
  broker_claims?: Array<{
    claim: string;
    status: string;
    evidence: string;
    missing_information: string[];
    required_checks: string[];
  }>;
  claim_verification?: { status: string; detail: string };
  missing_documents: string[];
  recommended_next_steps: string[];
  evidence_classification: string;
  confidence: string;
  disclaimer: string;
}

export interface CollaborativeInvestigation {
  user_query: string;
  conversation_language: ConversationLanguage;
  matched_land_ids: string[];
  dialogue_sequence: CharacterSpeechItem[];
  model_used: string;
  provider: string;
  is_live: boolean;
  overall_risk_level: string;
  investigation_report?: InvestigationReport | null;
}

export interface ModelStatusItem {
  model_name: string;
  provider: string;
  role: 'STT' | 'REASONING' | 'TTS';
  connection_status: string;
  is_live: boolean;
  supported_languages: string[];
  note: string;
}

export interface ModelsHealth {
  active_reasoning_provider: string;
  prisma_stt: ModelStatusItem;
  reasoning: ModelStatusItem;
  timbre_tts: ModelStatusItem;
  all_live: boolean;
  mock_mode: boolean;
  available_conversation_languages: ConversationLanguage[];
}

export interface ClaimCheckResponse {
  statement: string;
  land_id?: string;
  verification_status: 'VERIFIED' | 'OFFICIALLY ANNOUNCED / VERIFIED' | 'PROPOSED' | 'UNVERIFIED' | 'CONTRADICTED';
  confidence_level: 'High' | 'Medium' | 'Low';
  matched_claim?: string;
  available_evidence: string;
  explanation: string;
  missing_information: string;
  caution_note: string;
  ai_mode: string;
}

export interface DetectedIssue {
  issue_title: string;
  risk_level: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'CLEAR';
  snippet: string;
  explanation: string;
  lawyer_questions: string[];
}

export interface DocumentAnalysisResponse {
  filename: string;
  total_characters: number;
  overall_risk_score: number;
  risk_level: 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL';
  detected_issues: DetectedIssue[];
  summary: string;
  survey_numbers_found: string[];
  encumbrance_clauses_found: boolean;
  disclaimer: string;
  ai_mode: string;
}

export interface SampleDocumentItem {
  id: string;
  filename: string;
  title: string;
  type: string;
  size_bytes: number;
}
