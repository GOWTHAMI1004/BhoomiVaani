import React, { useState } from 'react';
import { 
  ShieldCheck, 
  Search, 
  CheckCircle, 
  AlertTriangle, 
  XCircle, 
  HelpCircle, 
  ArrowRight, 
  Sparkles,
  Milestone,
  Info
} from 'lucide-react';
import { LandListing, ClaimCheckResponse, Language } from '../types';
import { getTranslation } from '../translations/i18n';
import { api } from '../services/api';

interface ClaimCheckerProps {
  lands: LandListing[];
  language: Language;
}

export const ClaimChecker: React.FC<ClaimCheckerProps> = ({ lands, language }) => {
  const t = getTranslation(language);

  const [statement, setStatement] = useState('');
  const [selectedLandId, setSelectedLandId] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<ClaimCheckResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState('');

  const sampleStatements = [
    {
      label: 'Metro Rail in Chevella',
      text: 'A metro station will be built just 2 km from this Chevella land next year.',
      landId: 'bv-hyd-01'
    },
    {
      label: 'Regional Ring Road (RRR)',
      text: 'The Regional Ring Road (RRR) is officially announced to pass 4 km from this location.',
      landId: 'bv-hyd-01'
    },
    {
      label: 'Guaranteed Doubling in 18 Months',
      text: 'Land price is guaranteed to double within 18 months, completely risk free.',
      landId: 'bv-hyd-03'
    },
    {
      label: 'Medak International Airport Claim',
      text: 'A new greenfield international airport will be inaugurated in Medak within 24 months.',
      landId: 'bv-hyd-06'
    }
  ];

  const handleCheck = async (stmtToCheck?: string, landIdToCheck?: string) => {
    const text = stmtToCheck !== undefined ? stmtToCheck : statement;
    const landId = landIdToCheck !== undefined ? landIdToCheck : selectedLandId;

    if (!text.trim()) return;

    setErrorMessage('');
    setResult(null);
    setIsLoading(true);
    try {
      const res = await api.checkClaim(text, landId || undefined, language);
      setResult(res);
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : 'Claim review failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    const s = status.toUpperCase();
    if (s.includes('VERIFIED') && !s.includes('UNVERIFIED')) {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">
          <CheckCircle className="w-4 h-4 text-emerald-600" />
          <span>{status}</span>
        </span>
      );
    }
    if (s.includes('PROPOSED')) {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-800 border border-amber-300">
          <HelpCircle className="w-4 h-4 text-amber-600" />
          <span>PROPOSED (PLANNING PHASE)</span>
        </span>
      );
    }
    if (s.includes('CONTRADICTED')) {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-rose-100 text-rose-800 border border-rose-300">
          <XCircle className="w-4 h-4 text-rose-600" />
          <span>CONTRADICTED BY EVIDENCE</span>
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-orange-100 text-orange-900 border border-orange-300">
        <AlertTriangle className="w-4 h-4 text-orange-600" />
        <span>UNVERIFIED MARKETING CLAIM</span>
      </span>
    );
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Page Title Header */}
      <div className="bg-white rounded-3xl p-6 md:p-8 border border-ivory-border shadow-soft space-y-3">
        <div className="flex items-center gap-2.5">
          <div className="w-10 h-10 rounded-xl bg-forest-900 text-gold flex items-center justify-center font-bold shadow-sm">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-black text-forest-950 font-serif">
              Broker Infrastructure & Claim Checker
            </h1>
            <p className="text-xs text-gray-500">
              Compare a broker statement with synthetic demo entries. No government portals or official archives are queried.
            </p>
          </div>
        </div>

        {errorMessage && (
          <div className="mt-4 p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-900 text-xs flex items-center justify-between gap-3" role="alert">
            <span>{errorMessage}</span>
            <button type="button" className="font-bold underline" onClick={() => void handleCheck()}>
              Retry
            </button>
          </div>
        )}

        {/* Input Form */}
        <div className="pt-4 space-y-3">
          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1.5">
              Enter Broker's Statement or Marketing Claim:
            </label>
            <textarea
              rows={3}
              value={statement}
              onChange={(e) => setStatement(e.target.value)}
              placeholder='e.g. "A metro station will be built just 2 km from this land next year..."'
              className="w-full p-3.5 rounded-2xl border border-gray-200 text-xs text-gray-900 focus:outline-none focus:ring-2 focus:ring-forest-800 focus:border-transparent bg-ivory-dark/20 placeholder-gray-400"
            />
          </div>

          <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-1">
            <div className="w-full sm:w-auto flex items-center gap-2">
              <span className="text-xs text-gray-500 font-medium">Associate with Listing:</span>
              <select
                value={selectedLandId}
                onChange={(e) => setSelectedLandId(e.target.value)}
                aria-label="Associate statement with listing"
                className="text-xs font-medium bg-ivory-dark/60 border border-ivory-border px-3 py-2 rounded-xl text-gray-700 focus:outline-none"
              >
                <option value="">General / Across Telangana</option>
                {lands.map((l) => (
                  <option key={l.id} value={l.id}>
                    {l.title} ({l.location})
                  </option>
                ))}
              </select>
            </div>

            <button
              onClick={() => handleCheck()}
              disabled={isLoading || !statement.trim()}
              className="w-full sm:w-auto px-6 py-2.5 rounded-xl bg-forest-900 text-white hover:bg-forest-800 disabled:opacity-40 disabled:cursor-not-allowed text-xs font-bold flex items-center justify-center gap-2 shadow-sm transition-all"
            >
              {isLoading ? (
                <>
                  <Sparkles className="w-4 h-4 animate-spin text-gold" />
                  <span>Comparing with synthetic demo records...</span>
                </>
              ) : (
                <>
                  <span>Review Demo Evidence</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </div>

        {/* 1-Click Sample Claim Pills */}
        <div className="pt-3 border-t border-gray-100">
          <div className="text-[11px] font-bold text-gray-500 uppercase tracking-wider mb-2">
            Try Common Broker Pitches (1-Click Test):
          </div>
          <div className="flex flex-wrap gap-2">
            {sampleStatements.map((sample, idx) => (
              <button
                key={idx}
                onClick={() => {
                  setStatement(sample.text);
                  setSelectedLandId(sample.landId);
                  handleCheck(sample.text, sample.landId);
                }}
                className="text-left text-xs px-3 py-1.5 rounded-xl bg-ivory-dark border border-ivory-border hover:border-gold hover:bg-gold-light/10 text-gray-700 transition-all font-medium"
              >
                "{sample.label}"
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Verification Results Panel */}
      {result && (
        <div className="bg-white rounded-3xl p-6 md:p-8 border border-ivory-border shadow-elevated space-y-5 animate-in fade-in duration-300">
          {/* Header Status */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-gray-100 pb-4">
            <div>
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-gray-400">
                Demo Review Status
              </span>
              <div className="mt-1">
                {getStatusBadge(result.verification_status)}
              </div>
            </div>

            <div className="text-left sm:text-right">
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-gray-400">
                Confidence Level
              </span>
              <div className="text-sm font-bold text-gray-800 font-serif">
                {result.confidence_level} Confidence
              </div>
            </div>
          </div>

          {/* Statement Analyzed */}
          <div className="p-3.5 bg-ivory-dark/40 rounded-2xl border border-ivory-border text-xs">
            <span className="text-gray-500 font-bold uppercase text-[10px]">Broker's Statement Analyzed:</span>
            <p className="text-gray-900 font-medium italic mt-0.5">"{result.statement}"</p>
          </div>

          {/* Available Evidence */}
          <div>
            <h4 className="text-xs uppercase tracking-wider font-bold text-gray-500 mb-1.5 flex items-center gap-1.5">
              <Milestone className="w-4 h-4 text-forest-800" />
              <span>Available Synthetic Demo Entries:</span>
            </h4>
            <p className="text-xs text-gray-800 bg-gray-50 p-3.5 rounded-xl border border-gray-200/80 leading-relaxed font-mono">
              {result.available_evidence}
            </p>
          </div>

          {/* Detailed Explanation */}
          <div>
            <h4 className="text-xs uppercase tracking-wider font-bold text-gray-500 mb-1.5">
              Reasoning & Reality Check:
            </h4>
            <p className="text-xs md:text-sm text-gray-800 leading-relaxed">
              {result.explanation}
            </p>
          </div>

          {/* Missing Information */}
          <div className="bg-amber-50/70 border border-amber-200/80 p-4 rounded-2xl text-xs space-y-1">
            <span className="font-bold text-amber-950 flex items-center gap-1">
              <HelpCircle className="w-4 h-4 text-amber-700" />
              <span>Missing Documentary Corroboration:</span>
            </span>
            <p className="text-amber-900 leading-relaxed">
              {result.missing_information}
            </p>
          </div>

          {/* Caution Note */}
          <div className="bg-forest-50/80 border border-forest-200 p-4 rounded-2xl text-xs space-y-1">
            <span className="font-bold text-forest-950 flex items-center gap-1">
              <Info className="w-4 h-4 text-forest-800" />
              <span>Buyer Due Diligence Advisory:</span>
            </span>
            <p className="text-forest-900 leading-relaxed">
              {result.caution_note}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
