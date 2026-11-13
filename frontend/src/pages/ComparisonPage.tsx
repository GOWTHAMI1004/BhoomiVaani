import React from 'react';
import { 
  Scale, 
  X, 
  ShieldCheck, 
  AlertTriangle, 
  TrendingUp, 
  FileDown, 
  Plus, 
  MapPin, 
  ExternalLink 
} from 'lucide-react';
import { LandListing, Language } from '../types';
import { getTranslation } from '../translations/i18n';

interface ComparisonPageProps {
  lands: LandListing[];
  comparisonIds: string[];
  onToggleCompare: (id: string) => void;
  onViewDetails: (land: LandListing) => void;
  onDownloadReport: (id: string, surveyNo: string) => void;
  language: Language;
}

export const ComparisonPage: React.FC<ComparisonPageProps> = ({
  lands,
  comparisonIds,
  onToggleCompare,
  onViewDetails,
  onDownloadReport,
  language
}) => {
  const t = getTranslation(language);

  const selectedLands = lands.filter(l => comparisonIds.includes(l.id));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-3xl p-6 md:p-8 border border-ivory-border shadow-soft flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="w-10 h-10 rounded-xl bg-forest-900 text-gold flex items-center justify-center font-bold shadow-sm">
              <Scale className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-black text-forest-950 font-serif">
                Side-by-Side Property Comparison Matrix
              </h1>
              <p className="text-xs text-gray-500">
                Compare price, legal status, and verified infrastructure across up to 3 shortlisted parcels.
              </p>
            </div>
          </div>
        </div>

        {/* Quick add dropdown */}
        {comparisonIds.length < 3 && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500 font-medium">Add Property:</span>
            <select
              onChange={(e) => {
                if (e.target.value) {
                  onToggleCompare(e.target.value);
                  e.target.value = '';
                }
              }}
              defaultValue=""
              aria-label="Add property to comparison matrix"
              className="text-xs font-semibold bg-ivory-dark/60 border border-ivory-border px-3 py-2 rounded-xl text-forest-950 focus:outline-none"
            >
              <option value="" disabled>Choose property...</option>
              {lands
                .filter(l => !comparisonIds.includes(l.id))
                .map(l => (
                  <option key={l.id} value={l.id}>
                    {l.title} ({l.survey_number})
                  </option>
                ))}
            </select>
          </div>
        )}
      </div>

      {selectedLands.length === 0 ? (
        <div className="bg-white rounded-3xl p-12 text-center border border-ivory-border shadow-soft space-y-4">
          <Scale className="w-12 h-12 text-gray-400 mx-auto" />
          <h3 className="font-bold text-gray-800 text-base font-serif">No properties selected for comparison</h3>
          <p className="text-xs text-gray-500 max-w-md mx-auto">
            Click the "Compare" button on any property card from the Explore Land dashboard to view a detailed side-by-side comparison matrix.
          </p>
          <div className="flex justify-center gap-2 pt-2">
            {lands.slice(0, 2).map(l => (
              <button
                key={l.id}
                onClick={() => onToggleCompare(l.id)}
                className="px-3 py-1.5 rounded-xl border border-ivory-border bg-ivory-dark text-xs font-semibold text-forest-950 hover:border-gold"
              >
                + Compare {l.title.split(' ')[0]}
              </button>
            ))}
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-3xl border border-ivory-border shadow-elevated overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50/70">
                <th className="p-4 w-44 font-bold text-gray-500 uppercase tracking-wider text-[11px]">
                  Property Specification
                </th>
                {selectedLands.map(land => (
                  <th key={land.id} className="p-4 min-w-[260px] max-w-[320px]">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <span className="text-[10px] font-mono font-bold bg-gold text-forest-950 px-2 py-0.5 rounded">
                          {land.survey_number}
                        </span>
                        <h4 className="font-bold text-sm text-forest-950 mt-1 line-clamp-1 font-serif">
                          {land.title}
                        </h4>
                      </div>
                      <button
                        onClick={() => onToggleCompare(land.id)}
                        title="Remove from comparison"
                        aria-label="Remove from comparison"
                        className="p-1 rounded-full text-gray-400 hover:text-rose-600 hover:bg-rose-50"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {/* Image Row */}
              <tr>
                <td className="p-4 font-semibold text-gray-500 bg-gray-50/30">Preview</td>
                {selectedLands.map(land => (
                  <td key={land.id} className="p-4">
                    <img
                      src={land.image_url}
                      alt={land.title}
                      className="w-full h-32 object-cover rounded-xl"
                    />
                  </td>
                ))}
              </tr>

              {/* Location & District */}
              <tr>
                <td className="p-4 font-semibold text-gray-500 bg-gray-50/30">Location & District</td>
                {selectedLands.map(land => (
                  <td key={land.id} className="p-4 text-gray-800 font-medium">
                    <div className="flex items-center gap-1">
                      <MapPin className="w-3.5 h-3.5 text-forest-700 shrink-0" />
                      <span>{land.location}, {land.district}</span>
                    </div>
                  </td>
                ))}
              </tr>

              {/* Extent (Acres) */}
              <tr>
                <td className="p-4 font-semibold text-gray-500 bg-gray-50/30">Total Extent</td>
                {selectedLands.map(land => (
                  <td key={land.id} className="p-4 font-bold text-forest-950 text-sm">
                    {land.acres} Acres
                  </td>
                ))}
              </tr>

              {/* Rate per Acre */}
              <tr>
                <td className="p-4 font-semibold text-gray-500 bg-gray-50/30">Price per Acre</td>
                {selectedLands.map(land => (
                  <td key={land.id} className="p-4 text-gray-800 font-bold">
                    ₹{land.price_per_acre_lakhs} Lakhs
                  </td>
                ))}
              </tr>

              {/* Total Consideration */}
              <tr>
                <td className="p-4 font-semibold text-gray-500 bg-gray-50/30">Total Consideration</td>
                {selectedLands.map(land => (
                  <td key={land.id} className="p-4 font-black text-forest-950 text-base font-serif">
                    ₹{land.total_price_lakhs} Lakhs
                  </td>
                ))}
              </tr>

              {/* Legal Title Status */}
              <tr>
                <td className="p-4 font-semibold text-gray-500 bg-gray-50/30">Legal Title Status</td>
                {selectedLands.map(land => {
                  const isClean = land.legal_status.toLowerCase().includes('clean');
                  return (
                    <td key={land.id} className="p-4">
                      <div className={`p-2 rounded-xl border flex items-start gap-1.5 ${
                        isClean ? 'bg-emerald-50 border-emerald-200 text-emerald-900' : 'bg-rose-50 border-rose-200 text-rose-900'
                      }`}>
                        {isClean ? <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" /> : <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />}
                        <span className="font-bold text-xs">{land.legal_status}</span>
                      </div>
                    </td>
                  );
                })}
              </tr>

              {/* Legal Risks Identified */}
              <tr>
                <td className="p-4 font-semibold text-gray-500 bg-gray-50/30">Active Encumbrances / Risks</td>
                {selectedLands.map(land => (
                  <td key={land.id} className="p-4 text-xs">
                    {land.legal_risks.length > 0 ? (
                      <div className="space-y-1.5">
                        {land.legal_risks.map((r, idx) => (
                          <div key={idx} className="bg-rose-100/60 p-2 rounded-lg text-rose-950 text-[11px]">
                            <strong>[{r.severity}]</strong> {r.risk_type}
                          </div>
                        ))}
                      </div>
                    ) : (
                      <span className="text-emerald-700 font-medium">NIL registered encumbrances</span>
                    )}
                  </td>
                ))}
              </tr>

              {/* Growth Score */}
              <tr>
                <td className="p-4 font-semibold text-gray-500 bg-gray-50/30">AI Growth Score</td>
                {selectedLands.map(land => (
                  <td key={land.id} className="p-4">
                    <div className="flex items-center gap-1 font-bold text-amber-700 font-serif text-base">
                      <TrendingUp className="w-4 h-4" />
                      <span>{land.growth_score} / 100</span>
                    </div>
                  </td>
                ))}
              </tr>

              {/* Key Infrastructure */}
              <tr>
                <td className="p-4 font-semibold text-gray-500 bg-gray-50/30">Infrastructure Evidence</td>
                {selectedLands.map(land => (
                  <td key={land.id} className="p-4 space-y-1">
                    {land.infrastructure_evidence.map((inf, idx) => (
                      <div key={idx} className="text-[11px] text-gray-700">
                        • {inf.claim} (<span className="font-semibold">{inf.status}</span>)
                      </div>
                    ))}
                  </td>
                ))}
              </tr>

              {/* Actions */}
              <tr>
                <td className="p-4 font-semibold text-gray-500 bg-gray-50/30">Actions</td>
                {selectedLands.map(land => (
                  <td key={land.id} className="p-4 space-y-2">
                    <button
                      onClick={() => onViewDetails(land)}
                      className="w-full flex items-center justify-center gap-1 py-2 px-3 rounded-xl bg-forest-900 text-white font-bold hover:bg-forest-800 text-xs transition-colors"
                    >
                      <span>Examine Dossier</span>
                      <ExternalLink className="w-3.5 h-3.5" />
                    </button>

                    <button
                      onClick={() => onDownloadReport(land.id, land.survey_number)}
                      className="w-full flex items-center justify-center gap-1 py-1.5 px-3 rounded-xl border border-gray-200 text-gray-700 hover:bg-gray-50 text-xs font-semibold transition-colors"
                    >
                      <FileDown className="w-3.5 h-3.5 text-forest-700" />
                      <span>Download PDF</span>
                    </button>
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
