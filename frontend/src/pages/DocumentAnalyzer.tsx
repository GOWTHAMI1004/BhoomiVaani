import React, { useState, useEffect } from 'react';
import { 
  FileSearch, 
  Upload, 
  FileText, 
  AlertTriangle, 
  ShieldCheck, 
  HelpCircle, 
  CheckCircle2, 
  FileCode, 
  Sparkles,
  Info
} from 'lucide-react';
import { DocumentAnalysisResponse, SampleDocumentItem, Language } from '../types';
import { getTranslation } from '../translations/i18n';
import { api } from '../services/api';

interface DocumentAnalyzerProps {
  language: Language;
}

export const DocumentAnalyzer: React.FC<DocumentAnalyzerProps> = ({ language }) => {
  const t = getTranslation(language);

  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<DocumentAnalysisResponse | null>(null);
  const [samples, setSamples] = useState<SampleDocumentItem[]>([]);
  const [loadingSample, setLoadingSample] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Load sample documents on mount
  useEffect(() => {
    api.getSampleDocuments()
      .then(res => setSamples(res))
      .catch(err => console.warn('Failed to load sample docs:', err));
  }, []);

  const handleFileUpload = async (uploadedFile: File) => {
    setFile(uploadedFile);
    setErrorMsg(null);
    setIsUploading(true);
    try {
      const res = await api.analyzeDocument(uploadedFile);
      setAnalysisResult(res);
    } catch (err: any) {
      setErrorMsg(err.message || 'Analysis failed. Please ensure file is a valid PDF or text document.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleSelectSample = async (sampleId: string) => {
    setErrorMsg(null);
    setLoadingSample(true);
    try {
      const res = await api.getSampleDocumentContent(sampleId);
      setAnalysisResult(res.analysis);
      setFile(null);
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : 'Failed to load the sample document.');
    } finally {
      setLoadingSample(false);
    }
  };

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'CRITICAL':
        return 'text-rose-700 bg-rose-50 border-rose-300';
      case 'HIGH':
        return 'text-orange-700 bg-orange-50 border-orange-300';
      case 'MODERATE':
        return 'text-amber-700 bg-amber-50 border-amber-300';
      default:
        return 'text-amber-700 bg-amber-50 border-amber-300';
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Page Header */}
      <div className="bg-white rounded-3xl p-6 md:p-8 border border-ivory-border shadow-soft space-y-3">
        <div className="flex items-center gap-2.5">
          <div className="w-10 h-10 rounded-xl bg-forest-900 text-gold flex items-center justify-center font-bold shadow-sm">
            <FileSearch className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-black text-forest-950 font-serif">
              Document Text Pattern Scanner
            </h1>
            <p className="text-xs text-gray-500">
              Scan uploaded text for selected keywords. This cannot verify authenticity, legal status, ownership, or whether a flagged item is current.
            </p>
          </div>
        </div>

        {/* Upload Zone */}
        <div className="pt-4">
          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault();
              if (e.dataTransfer.files && e.dataTransfer.files[0]) {
                handleFileUpload(e.dataTransfer.files[0]);
              }
            }}
            className="border-2 border-dashed border-gray-300 hover:border-forest-700 rounded-3xl p-8 text-center transition-colors bg-ivory-dark/30 hover:bg-forest-50/20 cursor-pointer"
          >
            <input
              type="file"
              id="doc-upload"
              accept=".pdf,.txt"
              className="hidden"
              onChange={(e) => {
                if (e.target.files && e.target.files[0]) {
                  handleFileUpload(e.target.files[0]);
                }
              }}
            />
            <label htmlFor="doc-upload" className="cursor-pointer space-y-2 block">
              <div className="w-12 h-12 rounded-2xl bg-forest-100 text-forest-900 mx-auto flex items-center justify-center">
                <Upload className="w-6 h-6" />
              </div>
              <div className="text-sm font-bold text-gray-800">
                Click to upload or drag & drop property deed
              </div>
              <div className="text-xs text-gray-400">
                Supports PDF (.pdf) and plain text (.txt) up to 10 MB
              </div>
            </label>
          </div>

          {isUploading && (
            <div className="mt-4 p-4 rounded-2xl bg-forest-50 border border-forest-200 flex items-center gap-3 text-xs text-forest-950">
              <Sparkles className="w-5 h-5 text-gold animate-spin" />
              <div>
                <div className="font-bold">Scanning the text you provided...</div>
                <div className="text-gray-500">This rule-based scan does not query government records or verify document authenticity.</div>
              </div>
            </div>
          )}

          {errorMsg && (
            <div className="mt-4 p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-900 text-xs flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}
        </div>

        {/* 1-Click Synthetic Sample Deeds */}
        <div className="pt-3 border-t border-gray-100">
          <div className="text-[11px] font-bold text-gray-500 uppercase tracking-wider mb-2">
            Instant Demonstration: Test with Synthetic Sample Property Deeds
          </div>
          <div className="flex flex-wrap gap-2.5">
            {samples.map((s) => (
              <button
                key={s.id}
                onClick={() => handleSelectSample(s.id)}
                disabled={loadingSample || isUploading}
                className={`text-xs px-3.5 py-2 rounded-xl border flex items-center gap-2 font-medium transition-all ${
                  s.type.includes('Disputed')
                    ? 'bg-rose-50/60 border-rose-200 text-rose-900 hover:bg-rose-100'
                    : 'bg-emerald-50/60 border-emerald-200 text-emerald-900 hover:bg-emerald-100'
                }`}
              >
                <FileText className="w-4 h-4 shrink-0" />
                <span>{s.title}</span>
                <span className={`text-[10px] font-bold px-1.5 py-0.2 rounded font-mono ${
                  s.type.includes('Disputed') ? 'bg-rose-600 text-white' : 'bg-emerald-700 text-white'
                }`}>
                  {s.type.includes('Disputed') ? 'DEMO WITH FLAGS' : 'SYNTHETIC SAMPLE'}
                </span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Analysis Results Display */}
      {analysisResult && (
        <div className="bg-white rounded-3xl p-6 md:p-8 border border-ivory-border shadow-elevated space-y-6 animate-in fade-in duration-300">
          {/* Header Score & Overall Assessment */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-gray-100 pb-5">
            <div>
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-gray-400">
                Document Examined: {analysisResult.filename}
              </span>
              <div className="flex items-center gap-3 mt-1.5">
                <span className={`px-3 py-1 rounded-full text-xs font-bold border ${getRiskColor(analysisResult.risk_level)}`}>
                  Text Pattern Indicator: {analysisResult.risk_level}
                </span>
                {analysisResult.survey_numbers_found.length > 0 && (
                  <span className="text-xs bg-gray-100 text-gray-700 px-2.5 py-1 rounded-md font-mono">
                    Surveys: {analysisResult.survey_numbers_found.join(', ')}
                  </span>
                )}
              </div>
            </div>

            <div className="flex items-center gap-3 sm:text-right">
              <div>
                <div className="text-[10px] text-gray-500 uppercase tracking-wider font-bold">Rule-Based Pattern Score</div>
                <div className="text-3xl font-black font-serif text-forest-950">
                  {analysisResult.overall_risk_score} <span className="text-xs font-sans text-gray-400 font-normal">/ 100</span>
                </div>
              </div>
            </div>
          </div>

          {/* Document Summary */}
          <div className="p-4 bg-ivory-dark/40 rounded-2xl border border-ivory-border text-xs leading-relaxed text-gray-800">
            <strong>Analysis Executive Summary:</strong> {analysisResult.summary}
          </div>

          {/* Detected Legal Issues List */}
          <div className="space-y-4">
            <h3 className="text-xs uppercase tracking-wider font-bold text-gray-500 flex items-center gap-1.5">
              <span>Text Patterns to Review ({analysisResult.detected_issues.length})</span>
            </h3>

            {analysisResult.detected_issues.map((issue, idx) => (
              <div
                key={idx}
                className="bg-white rounded-2xl p-5 border border-gray-200 shadow-sm space-y-3"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {issue.risk_level === 'CRITICAL' || issue.risk_level === 'HIGH' ? (
                      <AlertTriangle className="w-5 h-5 text-rose-600 shrink-0" />
                    ) : issue.risk_level === 'CLEAR' ? (
                      <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
                    ) : (
                      <HelpCircle className="w-5 h-5 text-amber-600 shrink-0" />
                    )}
                    <h4 className="font-bold text-sm text-gray-900 font-serif">{issue.issue_title}</h4>
                  </div>
                  <span className={`px-2.5 py-0.5 rounded-full font-mono text-[10px] font-bold ${getRiskColor(issue.risk_level)}`}>
                    {issue.risk_level}
                  </span>
                </div>

                {/* Excerpt Snippet */}
                {issue.snippet && (
                  <div className="p-3 bg-gray-50 rounded-xl border border-gray-200 text-xs font-mono text-gray-700 leading-relaxed italic">
                    {issue.snippet}
                  </div>
                )}

                {/* Explanation */}
                <p className="text-xs text-gray-700 leading-relaxed">
                  {issue.explanation}
                </p>

                {/* Questions for Lawyer */}
                {issue.lawyer_questions && issue.lawyer_questions.length > 0 && (
                  <div className="p-3.5 bg-forest-50/70 border border-forest-200/60 rounded-xl text-xs space-y-1.5">
                    <span className="font-bold text-forest-950 flex items-center gap-1">
                      <HelpCircle className="w-3.5 h-3.5 text-forest-800" />
                      <span>Questions to Ask Your Qualified Property Advocate:</span>
                    </span>
                    <ul className="space-y-1 text-forest-900 list-disc list-inside">
                      {issue.lawyer_questions.map((q, qIdx) => (
                        <li key={qIdx}>{q}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Mandatory Statutory Disclaimer */}
          <div className="p-4 bg-amber-50 border border-amber-200 rounded-2xl flex items-start gap-2.5 text-xs text-amber-900">
            <Info className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
            <p className="leading-relaxed">
              <strong>STATUTORY LEGAL DISCLAIMER:</strong> {analysisResult.disclaimer}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
