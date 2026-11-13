export type Language = 'te' | 'hi' | 'en';

export interface Coordinates {
  lat: number;
  lng: number;
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
}

export interface LandStats {
  total_properties: number;
  clean_document_examples: number;
  risk_flagged_properties: number;
  average_growth_score: number;
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
  ai_mode: string;
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
