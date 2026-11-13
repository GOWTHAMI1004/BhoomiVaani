import React from 'react';
import { Layers, ShieldCheck, AlertTriangle, TrendingUp } from 'lucide-react';
import { LandStats, Language } from '../types';
import { getTranslation } from '../translations/i18n';

interface StatsBarProps {
  stats: LandStats | null;
  language: Language;
}

export const StatsBar: React.FC<StatsBarProps> = ({ stats, language }) => {
  const t = getTranslation(language);

  if (!stats) return null;

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {/* Total properties */}
      <div className="bg-white rounded-2xl p-4 border border-ivory-border shadow-soft flex items-center gap-3.5">
        <div className="w-12 h-12 rounded-xl bg-forest-50 border border-forest-100 flex items-center justify-center text-forest-800 shrink-0">
          <Layers className="w-6 h-6" />
        </div>
        <div>
          <div className="text-2xl font-black text-forest-950 font-serif">{stats.total_properties}</div>
          <div className="text-xs text-gray-500 font-medium">{t.totalProperties}</div>
        </div>
      </div>

      {/* Clean Title */}
      <div className="bg-white rounded-2xl p-4 border border-ivory-border shadow-soft flex items-center gap-3.5">
        <div className="w-12 h-12 rounded-xl bg-emerald-50 border border-emerald-100 flex items-center justify-center text-emerald-700 shrink-0">
          <ShieldCheck className="w-6 h-6" />
        </div>
        <div>
          <div className="text-2xl font-black text-emerald-800 font-serif">{stats.clean_document_examples}</div>
          <div className="text-xs text-gray-500 font-medium">{t.cleanDocuments}</div>
        </div>
      </div>

      {/* Disputed / Risk */}
      <div className="bg-white rounded-2xl p-4 border border-ivory-border shadow-soft flex items-center gap-3.5">
        <div className="w-12 h-12 rounded-xl bg-rose-50 border border-rose-100 flex items-center justify-center text-rose-700 shrink-0">
          <AlertTriangle className="w-6 h-6" />
        </div>
        <div>
          <div className="text-2xl font-black text-rose-700 font-serif">{stats.risk_flagged_properties}</div>
          <div className="text-xs text-gray-500 font-medium">{t.disputedProperties}</div>
        </div>
      </div>

      {/* Average Growth */}
      <div className="bg-white rounded-2xl p-4 border border-ivory-border shadow-soft flex items-center gap-3.5">
        <div className="w-12 h-12 rounded-xl bg-amber-50 border border-amber-100 flex items-center justify-center text-amber-700 shrink-0">
          <TrendingUp className="w-6 h-6" />
        </div>
        <div>
          <div className="text-2xl font-black text-amber-800 font-serif">{stats.average_growth_score}<span className="text-xs text-gray-400 font-sans font-normal">/100</span></div>
          <div className="text-xs text-gray-500 font-medium">{t.avgGrowthScore}</div>
        </div>
      </div>
    </div>
  );
};
