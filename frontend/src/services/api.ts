import {
  LandListing,
  LandStats,
  AIChatResponse,
  ClaimCheckResponse,
  DocumentAnalysisResponse,
  SampleDocumentItem,
  Language
} from '../types';

const API_BASE = '/api';

export const api = {
  // Lands API
  async getLands(params?: {
    district?: string;
    min_acres?: number;
    max_acres?: number;
    max_budget_lakhs?: number;
    land_type?: string;
    legal_status?: string;
    search?: string;
  }): Promise<LandListing[]> {
    const query = new URLSearchParams();
    if (params) {
      if (params.district) query.append('district', params.district);
      if (params.min_acres !== undefined) query.append('min_acres', params.min_acres.toString());
      if (params.max_acres !== undefined) query.append('max_acres', params.max_acres.toString());
      if (params.max_budget_lakhs !== undefined) query.append('max_budget_lakhs', params.max_budget_lakhs.toString());
      if (params.land_type) query.append('land_type', params.land_type);
      if (params.legal_status) query.append('legal_status', params.legal_status);
      if (params.search) query.append('search', params.search);
    }
    const res = await fetch(`${API_BASE}/lands?${query.toString()}`);
    if (!res.ok) throw new Error(`Failed to fetch lands: ${res.statusText}`);
    return res.json();
  },

  async getLandById(id: string): Promise<LandListing> {
    const res = await fetch(`${API_BASE}/lands/${id}`);
    if (!res.ok) throw new Error(`Failed to fetch land ${id}: ${res.statusText}`);
    return res.json();
  },

  async getStats(): Promise<LandStats> {
    const res = await fetch(`${API_BASE}/lands/stats`);
    if (!res.ok) throw new Error(`Failed to fetch stats: ${res.statusText}`);
    return res.json();
  },

  async compareLands(land_ids: string[]): Promise<LandListing[]> {
    const res = await fetch(`${API_BASE}/lands/compare`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ land_ids })
    });
    if (!res.ok) throw new Error(`Failed to compare lands: ${res.statusText}`);
    return res.json();
  },

  async downloadReport(landId: string, surveyNo: string): Promise<void> {
    const res = await fetch(`${API_BASE}/lands/${landId}/report`);
    if (!res.ok) throw new Error(`Failed to download report: ${res.statusText}`);
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `BhoomiVaani_Dossier_${landId}_${surveyNo.replace('/', '_')}.pdf`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  },

  // AI Pipeline API
  async chatWithEvon(
    query: string,
    language: Language = 'te',
    conversationHistory: { role: string; content: string }[] = [],
    selectedLandId?: string
  ): Promise<AIChatResponse> {
    const res = await fetch(`${API_BASE}/ai/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query,
        language,
        conversation_history: conversationHistory,
        selected_land_id: selectedLandId
      })
    });
    if (!res.ok) throw new Error(`Evon Chat API error: ${res.statusText}`);
    return res.json();
  },

  async transcribeAudio(audioBlob: Blob, language: string = 'indic-auto'): Promise<{ transcript: string; detected_language: string; ai_mode: string }> {
    const formData = new FormData();
    formData.append('file', audioBlob, 'recording.wav');
    formData.append('language', language);

    const res = await fetch(`${API_BASE}/ai/transcribe`, {
      method: 'POST',
      body: formData
    });
    if (!res.ok) throw new Error(`Prisma STT error: ${res.statusText}`);
    return res.json();
  },

  async speakText(text: string, language: Language = 'te'): Promise<{ audio_base64: string; duration_estimate_sec: number; ai_mode: string }> {
    const res = await fetch(`${API_BASE}/ai/speak`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, language })
    });
    if (!res.ok) throw new Error(`Timbre TTS error: ${res.statusText}`);
    return res.json();
  },

  // Broker Claim Checker API
  async checkClaim(statement: string, landId?: string, language: Language = 'te'): Promise<ClaimCheckResponse> {
    const res = await fetch(`${API_BASE}/claims/check`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ statement, land_id: landId, language })
    });
    if (!res.ok) throw new Error(`Claim checker error: ${res.statusText}`);
    return res.json();
  },

  // Legal Document Analyzer API
  async analyzeDocument(file: File): Promise<DocumentAnalysisResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const res = await fetch(`${API_BASE}/documents/analyze`, {
      method: 'POST',
      body: formData
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Document analysis failed');
    }
    return res.json();
  },

  async getSampleDocuments(): Promise<SampleDocumentItem[]> {
    const res = await fetch(`${API_BASE}/documents/samples`);
    if (!res.ok) throw new Error('Failed to fetch sample documents');
    return res.json();
  },

  async getSampleDocumentContent(sampleId: string): Promise<{ filename: string; content: string; analysis: DocumentAnalysisResponse }> {
    const res = await fetch(`${API_BASE}/documents/samples/${sampleId}`);
    if (!res.ok) throw new Error('Failed to fetch sample content');
    return res.json();
  },

  // Health
  async getHealth(): Promise<any> {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error('Backend health check failed');
    return res.json();
  }
};
