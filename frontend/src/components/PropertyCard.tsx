import React from 'react';
import { 
  MapPin, 
  ShieldCheck, 
  AlertTriangle, 
  TrendingUp, 
  FileDown, 
  Scale, 
  Bookmark, 
  Sparkles,
  ExternalLink,
  Milestone
} from 'lucide-react';
import { LandListing, Language } from '../types';
import { getTranslation } from '../translations/i18n';

interface PropertyCardProps {
  land: LandListing;
  language: Language;
  isAiMatched: boolean;
  isInComparison: boolean;
  isSaved: boolean;
  onToggleCompare: (id: string) => void;
  onToggleSave: (id: string) => void;
  onViewDetails: (land: LandListing) => void;
  onDownloadReport: (id: string, surveyNo: string) => void;
}

export const PropertyCard: React.FC<PropertyCardProps> = ({
  land,
  language,
  isAiMatched,
  isInComparison,
  isSaved,
  onToggleCompare,
  onToggleSave,
  onViewDetails,
  onDownloadReport
}) => {
  const t = getTranslation(language);
  const isClean = land.legal_status.toLowerCase().includes('clean');

  return (
    <div
      className={`relative bg-white rounded-2xl overflow-hidden border transition-all duration-300 flex flex-col ${
        isAiMatched
          ? 'border-2 border-gold shadow-gold-glow scale-[1.01] ring-2 ring-forest-500/20'
          : 'border-ivory-border shadow-soft hover:shadow-elevated'
      }`}
    >
      {/* AI Matched Floating Badge */}
      {isAiMatched && (
        <div className="absolute top-3 left-3 z-10 flex items-center gap-1.5 px-3 py-1 rounded-full bg-forest-900/95 text-gold-light text-xs font-bold shadow-lg border border-gold/40 animate-pulse-slow">
          <Sparkles className="w-3.5 h-3.5 text-gold" />
          <span>{t.matchedBadge}</span>
        </div>
      )}

      {/* Bookmark Button */}
      <button
        onClick={() => onToggleSave(land.id)}
        aria-label={isSaved ? "Remove from saved properties" : "Save property"}
        className={`absolute top-3 right-3 z-10 p-2 rounded-xl backdrop-blur-md transition-all ${
          isSaved
            ? 'bg-gold text-forest-950 shadow-md'
            : 'bg-black/40 text-white hover:bg-black/60'
        }`}
      >
        <Bookmark className={`w-4 h-4 ${isSaved ? 'fill-current' : ''}`} />
      </button>

      {/* Property Image & Top Tags */}
      <div className="relative h-48 w-full overflow-hidden bg-gray-100">
        <img
          src={land.image_url}
          alt={land.title}
          className="w-full h-full object-cover transition-transform duration-500 hover:scale-105"
          loading="lazy"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/75 via-transparent to-black/20" />

        {/* Survey Number & District Tag */}
        <div className="absolute bottom-3 left-3 right-3 flex items-end justify-between">
          <div>
            <span className="text-[11px] font-mono font-bold tracking-wider text-gold-light bg-black/60 px-2 py-0.5 rounded backdrop-blur-sm">
              {land.survey_number}
            </span>
            <h3 className="text-white font-bold text-base leading-tight mt-1 line-clamp-1">
              {land.title}
            </h3>
          </div>
          <div className="text-right">
            <span className="text-[11px] font-bold text-white bg-forest-950/80 px-2 py-0.5 rounded">
              {land.acres} Acres
            </span>
          </div>
        </div>
      </div>

      {/* Card Body */}
      <div className="p-4 flex-1 flex flex-col justify-between space-y-3.5">
        {/* Location & Land Type */}
        <div className="flex items-center justify-between text-xs text-gray-500">
          <div className="flex items-center gap-1 text-gray-700 font-medium truncate max-w-[170px]">
            <MapPin className="w-3.5 h-3.5 text-forest-700 shrink-0" />
            <span>{land.location}, {land.district}</span>
          </div>
          <span className="text-[11px] bg-ivory-dark text-forest-900 px-2 py-0.5 rounded-md font-medium border border-ivory-border">
            {land.land_type}
          </span>
        </div>

        {/* Legal Status & Risks */}
        <div className="pt-1">
          <div className={`p-2.5 rounded-xl border flex items-start gap-2 ${
            isClean
              ? 'bg-emerald-50/70 border-emerald-200/60 text-emerald-900'
              : 'bg-rose-50 border-rose-200 text-rose-950'
          }`}>
            {isClean ? (
              <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
            ) : (
              <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
            )}
            <div className="text-xs">
              <div className="font-bold flex items-center gap-1">
                <span>{land.legal_status}</span>
              </div>
              {!isClean && land.legal_risks.length > 0 && (
                <p className="text-[11px] text-rose-800 line-clamp-1 mt-0.5 font-medium">
                  {land.legal_risks[0].risk_type}
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Infrastructure Highlights */}
        {land.infrastructure_evidence.length > 0 && (
          <div className="text-xs bg-gray-50 p-2.5 rounded-xl border border-gray-200/60">
            <div className="flex items-center gap-1.5 text-gray-500 font-medium text-[11px] mb-1">
              <Milestone className="w-3.5 h-3.5 text-forest-700" />
              <span>Key Infrastructure:</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="font-semibold text-gray-800 text-xs truncate max-w-[160px]">
                {land.infrastructure_evidence[0].claim}
              </span>
              <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                land.infrastructure_evidence[0].status === 'Officially announced' || land.infrastructure_evidence[0].status === 'Operational'
                  ? 'bg-emerald-100 text-emerald-800'
                  : land.infrastructure_evidence[0].status === 'Proposed'
                  ? 'bg-amber-100 text-amber-800'
                  : 'bg-rose-100 text-rose-800'
              }`}>
                {land.infrastructure_evidence[0].status}
              </span>
            </div>
          </div>
        )}

        {/* Pricing & Growth Score */}
        <div className="pt-2 border-t border-gray-100 flex items-center justify-between">
          <div>
            <div className="text-xs text-gray-500">{t.perAcre}: <span className="font-bold text-gray-800">₹{land.price_per_acre_lakhs} L</span></div>
            <div className="text-lg font-black text-forest-950 font-serif">
              ₹{land.total_price_lakhs} <span className="text-xs font-sans font-medium text-gray-500">Lakhs</span>
            </div>
          </div>
          <div className="text-right">
            <div className="text-[10px] text-gray-500 uppercase tracking-wider font-semibold">Growth Score</div>
            <div className="flex items-center gap-1 justify-end">
              <TrendingUp className="w-3.5 h-3.5 text-amber-600" />
              <span className="text-base font-black text-amber-700 font-serif">{land.growth_score}</span>
              <span className="text-[10px] text-gray-400">/100</span>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="pt-2 grid grid-cols-2 gap-2">
          <button
            onClick={() => onViewDetails(land)}
            className="flex items-center justify-center gap-1 px-3 py-2 text-xs font-bold rounded-xl bg-forest-900 text-white hover:bg-forest-800 transition-colors shadow-sm"
          >
            <span>{t.viewDetails}</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={() => onToggleCompare(land.id)}
            className={`flex items-center justify-center gap-1 px-3 py-2 text-xs font-semibold rounded-xl border transition-all ${
              isInComparison
                ? 'bg-forest-100 border-forest-300 text-forest-900 font-bold'
                : 'bg-white border-gray-200 text-gray-700 hover:bg-gray-50'
            }`}
          >
            <Scale className="w-3.5 h-3.5" />
            <span>{isInComparison ? t.compared : t.compareBtn}</span>
          </button>
        </div>

        {/* Report Download Shortcut */}
        <button
          onClick={() => onDownloadReport(land.id, land.survey_number)}
          className="w-full flex items-center justify-center gap-1.5 py-1.5 text-[11px] font-medium text-gray-500 hover:text-forest-900 hover:bg-ivory-dark rounded-lg transition-colors border border-dashed border-gray-200"
        >
          <FileDown className="w-3.5 h-3.5 text-forest-700" />
          <span>{t.downloadReport}</span>
        </button>
      </div>
    </div>
  );
};
