import React from 'react';
import { 
  X, 
  MapPin, 
  ShieldCheck, 
  AlertTriangle, 
  FileDown, 
  Milestone, 
  Compass, 
  Scale, 
  CheckCircle2,
  AlertCircle
} from 'lucide-react';
import { LandListing, Language } from '../types';
import { getTranslation } from '../translations/i18n';

interface PropertyDetailsModalProps {
  land: LandListing | null;
  onClose: () => void;
  language: Language;
  onDownloadReport: (id: string, surveyNo: string) => void;
  isInComparison: boolean;
  onToggleCompare: (id: string) => void;
}

export const PropertyDetailsModal: React.FC<PropertyDetailsModalProps> = ({
  land,
  onClose,
  language,
  onDownloadReport,
  isInComparison,
  onToggleCompare
}) => {
  const t = getTranslation(language);

  if (!land) return null;

  const isClean = land.legal_status.toLowerCase().includes('clean');

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div 
        className="bg-white rounded-3xl max-w-3xl w-full max-h-[90vh] overflow-y-auto shadow-2xl border border-ivory-border relative animate-in fade-in zoom-in-95 duration-200"
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
      >
        {/* Close Button */}
        <button
          onClick={onClose}
          aria-label="Close dialog"
          className="absolute top-4 right-4 z-20 p-2.5 rounded-full bg-black/50 text-white hover:bg-black/75 transition-all"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Hero Header with Image */}
        <div className="relative h-64 w-full bg-gray-900">
          <img
            src={land.image_url}
            alt={land.title}
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-forest-950 via-forest-950/40 to-transparent" />

          <div className="absolute bottom-5 left-6 right-6 flex flex-col md:flex-row md:items-end justify-between gap-2">
            <div>
              <div className="flex items-center gap-2 mb-1.5">
                <span className="px-2.5 py-0.5 rounded-md font-mono text-xs font-bold bg-gold text-forest-950">
                  {land.survey_number}
                </span>
                <span className="px-2.5 py-0.5 rounded-md text-xs font-medium bg-white/20 text-white backdrop-blur-sm">
                  {land.land_type}
                </span>
              </div>
              <h2 id="modal-title" className="text-2xl font-black text-white font-serif">{land.title}</h2>
              <div className="flex items-center gap-1.5 text-xs text-gray-300 mt-1">
                <MapPin className="w-4 h-4 text-gold" />
                <span>{land.location}, {land.district} District, Telangana</span>
              </div>
            </div>

            <div className="text-left md:text-right">
              <div className="text-xs text-gray-300 font-medium">Total Consideration</div>
              <div className="text-3xl font-black text-gold-light font-serif">
                ₹{land.total_price_lakhs} <span className="text-sm font-sans font-normal text-white">Lakhs</span>
              </div>
              <div className="text-xs text-gray-400">
                ₹{land.price_per_acre_lakhs} Lakhs / acre ({land.acres} Acres)
              </div>
            </div>
          </div>
        </div>

        {/* Content Body */}
        <div className="p-6 space-y-6">
          {/* Synthetic Demo Disclaimer */}
          <div className="flex items-center gap-2 p-3 bg-amber-50 border border-amber-200 text-amber-900 rounded-xl text-xs">
            <AlertCircle className="w-4 h-4 text-amber-700 shrink-0" />
            <span>
              <strong>Demonstration Dossier:</strong> Synthesized for buyer awareness. Coordinates: {land.coordinates.lat}, {land.coordinates.lng}.
            </span>
          </div>

          {/* Description */}
          <div>
            <h3 className="text-xs uppercase tracking-wider font-bold text-gray-500 mb-2">Property Overview</h3>
            <p className="text-sm text-gray-700 leading-relaxed bg-ivory-dark/40 p-4 rounded-xl border border-ivory-border">
              {land.description}
            </p>
          </div>

          {/* Legal Status & Risks Analysis */}
          <div>
            <h3 className="text-xs uppercase tracking-wider font-bold text-gray-500 mb-2 flex items-center gap-1.5">
              <span>Legal Title & Encumbrance Record</span>
            </h3>

            <div className={`p-4 rounded-2xl border ${
              isClean 
                ? 'bg-emerald-50/80 border-emerald-200 text-emerald-950'
                : 'bg-rose-50 border-rose-200 text-rose-950'
            }`}>
              <div className="flex items-center gap-2 mb-2 font-bold text-sm">
                {isClean ? <ShieldCheck className="w-5 h-5 text-emerald-600" /> : <AlertTriangle className="w-5 h-5 text-rose-600" />}
                <span>{land.legal_status}</span>
              </div>

              {isClean ? (
                <p className="text-xs text-emerald-800 leading-relaxed">
                  Our synthetic Dharani records reflect 30 years of continuous clear ownership, non-prohibited Section 22-A status, and zero registered mortgages or civil court attachments.
                </p>
              ) : (
                <div className="space-y-3 mt-3">
                  {land.legal_risks.map((risk, idx) => (
                    <div key={idx} className="bg-white/90 p-3.5 rounded-xl border border-rose-200 shadow-sm text-xs">
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-bold text-rose-950 text-sm">{risk.risk_type}</span>
                        <span className="px-2 py-0.5 rounded font-mono font-bold text-[10px] bg-rose-600 text-white">
                          {risk.severity}
                        </span>
                      </div>
                      <p className="text-gray-700 mb-2">{risk.description}</p>
                      <div className="bg-rose-100/60 p-2 rounded text-[11px] text-rose-900 font-medium">
                        <strong>Required Action:</strong> {risk.recommended_action}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Infrastructure Evidence Table */}
          <div>
            <h3 className="text-xs uppercase tracking-wider font-bold text-gray-500 mb-2 flex items-center gap-1.5">
              <Milestone className="w-4 h-4 text-forest-800" />
              <span>Infrastructure Claims & Verification Evidence</span>
            </h3>

            <div className="overflow-x-auto border border-gray-200 rounded-xl">
              <table className="w-full text-left text-xs">
                <thead className="bg-gray-50 text-gray-600 border-b border-gray-200">
                  <tr>
                    <th className="p-3 font-semibold">Claimed Project</th>
                    <th className="p-3 font-semibold">Status</th>
                    <th className="p-3 font-semibold">Distance</th>
                    <th className="p-3 font-semibold">Source / Evidentiary Basis</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {land.infrastructure_evidence.map((ev, idx) => (
                    <tr key={idx} className="hover:bg-gray-50/50">
                      <td className="p-3 font-bold text-gray-800">{ev.claim}</td>
                      <td className="p-3">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          ev.status === 'Operational' || ev.status === 'Officially announced'
                            ? 'bg-emerald-100 text-emerald-800'
                            : ev.status === 'Proposed'
                            ? 'bg-amber-100 text-amber-800'
                            : 'bg-rose-100 text-rose-800'
                        }`}>
                          {ev.status}
                        </span>
                      </td>
                      <td className="p-3 text-gray-600">{ev.distance_km} km</td>
                      <td className="p-3 text-gray-500 max-w-xs">{ev.evidence_source}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Buyer Precautions */}
          <div className="bg-forest-50 border border-forest-200 p-4 rounded-2xl text-xs text-forest-950">
            <h4 className="font-bold text-sm text-forest-900 mb-2 flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-forest-700" />
              <span>Standard Buyer Due Diligence Safeguards</span>
            </h4>
            <ul className="space-y-1.5 text-forest-800 list-disc list-inside">
              <li>Request an official Mandal Surveyor F-Line physical boundary demarcation.</li>
              <li>Procure a fresh 30-year Form 15 Encumbrance Certificate directly from the Sub-Registrar.</li>
              <li>Cross-examine Pattadar Passbook with live Dharani database tokens before signing.</li>
              <li>Verify HMDA / DTCP master plan zoning to ensure absence of green belt or waterbody buffer overlays.</li>
            </ul>
          </div>

          {/* Footer Actions */}
          <div className="pt-4 border-t border-gray-100 flex flex-col sm:flex-row items-center justify-between gap-3">
            <button
              onClick={() => onToggleCompare(land.id)}
              className={`w-full sm:w-auto px-4 py-2.5 rounded-xl border text-xs font-semibold flex items-center justify-center gap-2 transition-all ${
                isInComparison
                  ? 'bg-forest-100 border-forest-300 text-forest-900 font-bold'
                  : 'bg-white border-gray-200 text-gray-700 hover:bg-gray-50'
              }`}
            >
              <Scale className="w-4 h-4" />
              <span>{isInComparison ? 'Remove from Comparison' : 'Add to Comparison Matrix'}</span>
            </button>

            <button
              onClick={() => onDownloadReport(land.id, land.survey_number)}
              className="w-full sm:w-auto px-5 py-2.5 rounded-xl bg-forest-900 text-white hover:bg-forest-800 text-xs font-bold flex items-center justify-center gap-2 shadow-md transition-colors"
            >
              <FileDown className="w-4 h-4 text-gold" />
              <span>Download Printable PDF Dossier</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
