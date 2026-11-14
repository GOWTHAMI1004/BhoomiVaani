import {
  LandListing,
  LandStats,
  AIChatResponse,
  CollaborativeInvestigation,
  ConversationLanguage,
  ClaimCheckResponse,
  DocumentAnalysisResponse,
  SampleDocumentItem,
  Language,
  ModelsHealth
} from '../types';

const API_BASE = '/api';
const BACKEND_STARTUP_GUIDANCE = 'Start the API and frontend together from the repository root with `python start.py`, or run FastAPI on port 8000.';

async function responseError(response: Response, action: string): Promise<Error> {
  const body = await response.text().catch(() => '');
  if (
    response.status === 500
    && response.headers.get('content-type')?.includes('text/plain')
    && !body.trim()
  ) {
    return new Error(`FastAPI is unreachable through the Vite proxy (HTTP 500). ${BACKEND_STARTUP_GUIDANCE}`);
  }
  if (body) {
    try {
      const parsed = JSON.parse(body);
      if (typeof parsed.detail === 'string') return new Error(parsed.detail);
    } catch {
      if (/http proxy error|econnrefused|connect econnrefused/i.test(body)) {
        return new Error(`FastAPI is unreachable through the Vite proxy (HTTP ${response.status}). ${BACKEND_STARTUP_GUIDANCE}`);
      }
      return new Error(`${action} (HTTP ${response.status}): ${body.slice(0, 240)}`);
    }
  }
  return new Error(`${action} (HTTP ${response.status})`);
}

function requestError(error: unknown, action: string): Error {
  if (error instanceof Error && ['TimeoutError', 'AbortError'].includes(error.name)) {
    return new Error(`${action} timed out. Check the backend/provider status and retry.`);
  }
  if (error instanceof TypeError) {
    return new Error(`Could not reach the FastAPI backend. ${BACKEND_STARTUP_GUIDANCE}`);
  }
  return error instanceof Error ? error : new Error(action);
}

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
    try {
      const res = await fetch(`${API_BASE}/lands?${query.toString()}`, {
        signal: AbortSignal.timeout(8_000)
      });
      if (!res.ok) throw await responseError(res, 'Failed to fetch land listings');
      return await res.json();
    } catch (error) {
      throw requestError(error, 'Land listing request');
    }
  },

  async getLandById(id: string): Promise<LandListing> {
    const res = await fetch(`${API_BASE}/lands/${id}`);
    if (!res.ok) throw new Error(`Failed to fetch land ${id}: ${res.statusText}`);
    return res.json();
  },

  async getStats(): Promise<LandStats> {
    try {
      const res = await fetch(`${API_BASE}/lands/stats`, { signal: AbortSignal.timeout(8_000) });
      if (!res.ok) throw await responseError(res, 'Failed to fetch land statistics');
      return await res.json();
    } catch (error) {
      throw requestError(error, 'Land statistics request');
    }
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

  async investigate(
    query: string,
    conversationLanguage: ConversationLanguage,
    selectedLandId?: string,
    conversationHistory: { role: 'user' | 'assistant'; content: string }[] = [],
    documentAnalyses: DocumentAnalysisResponse[] = []
  ): Promise<CollaborativeInvestigation> {
    try {
      const res = await fetch(`${API_BASE}/investigate/collaborate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query,
          conversation_language: conversationLanguage,
          selected_land_id: selectedLandId || undefined,
          conversation_history: conversationHistory,
          document_analyses: documentAnalyses
        }),
        signal: AbortSignal.timeout(90_000)
      });
      if (!res.ok) throw await responseError(res, 'Investigation failed');
      return await res.json();
    } catch (error) {
      throw requestError(error, 'Investigation request');
    }
  },

  async downloadInvestigationReport(
    conversationHistory: { role: 'user' | 'assistant'; content: string }[],
    selectedLandId: string | undefined,
    documentAnalyses: DocumentAnalysisResponse[]
  ): Promise<void> {
    try {
      const res = await fetch(`${API_BASE}/investigate/report`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          conversation_history: conversationHistory,
          selected_land_id: selectedLandId,
          document_analyses: documentAnalyses
        }),
        signal: AbortSignal.timeout(30_000)
      });
      if (!res.ok) throw await responseError(res, 'Report generation failed');
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = 'BhoomiVaani_Land_Buying_Report.pdf';
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      window.setTimeout(() => window.URL.revokeObjectURL(url), 1_000);
    } catch (error) {
      throw requestError(error, 'Report generation request');
    }
  },

  async getModelsStatus(): Promise<ModelsHealth> {
    try {
      const res = await fetch(`${API_BASE}/investigate/models/status`, {
        signal: AbortSignal.timeout(8_000)
      });
      if (!res.ok) throw await responseError(res, 'Could not load AI provider status');
      return await res.json();
    } catch (error) {
      throw requestError(error, 'Provider status check');
    }
  },

  async transcribeAudio(audioBlob: Blob): Promise<{ transcript: string; detected_language: string; ai_mode: string; is_live: boolean }> {
    const formData = new FormData();
    formData.append('file', audioBlob, 'recording.wav');
    formData.append('language', 'auto');

    try {
      const res = await fetch(`${API_BASE}/ai/transcribe`, {
        method: 'POST',
        body: formData,
        signal: AbortSignal.timeout(130_000)
      });
      if (!res.ok) throw await responseError(res, 'Prisma STT failed');
      return await res.json();
    } catch (error) {
      throw requestError(error, 'Prisma transcription request');
    }
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
    try {
      const res = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(8_000) });
      if (!res.ok) throw await responseError(res, 'Backend health check failed');
      return await res.json();
    } catch (error) {
      throw requestError(error, 'Backend health request');
    }
  }
};
