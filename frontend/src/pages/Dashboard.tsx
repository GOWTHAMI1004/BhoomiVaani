import React, { useState, useMemo } from 'react';
import { 
  Search, 
  Filter, 
  SlidersHorizontal, 
  RotateCcw, 
  CheckCircle, 
  AlertTriangle,
  Building,
  Info
} from 'lucide-react';
import { LandListing, LandStats, Language } from '../types';
import { getTranslation } from '../translations/i18n';
import { PropertyCard } from '../components/PropertyCard';
import { StatsBar } from '../components/StatsBar';

interface DashboardProps {
  lands: LandListing[];
  stats: LandStats | null;
  language: Language;
  aiMatchedLandIds: string[];
  comparisonIds: string[];
  savedIds: string[];
  onToggleCompare: (id: string) => void;
  onToggleSave: (id: string) => void;
  onViewDetails: (land: LandListing) => void;
  onDownloadReport: (id: string, surveyNo: string) => void;
  selectedDistrict: string;
  setSelectedDistrict: (district: string) => void;
}

export const Dashboard: React.FC<DashboardProps> = ({
  lands,
  stats,
  language,
  aiMatchedLandIds,
  comparisonIds,
  savedIds,
  onToggleCompare,
  onToggleSave,
  onViewDetails,
  onDownloadReport,
  selectedDistrict,
  setSelectedDistrict
}) => {
  const t = getTranslation(language);

  // Search & Filter state
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedLandType, setSelectedLandType] = useState('');
  const [selectedLegalStatus, setSelectedLegalStatus] = useState('');
  const [maxBudget, setMaxBudget] = useState<number>(700); // in Lakhs
  const [minAcres, setMinAcres] = useState<number>(0);

  // Filter options from lands
  const landTypes = useMemo(() => {
    return Array.from(new Set(lands.map(l => l.land_type)));
  }, [lands]);

  // Filtered lands
  const filteredLands = useMemo(() => {
    return lands.filter(land => {
      // District filter
      if (selectedDistrict && !land.district.toLowerCase().includes(selectedDistrict.toLowerCase())) {
        return false;
      }
      // Search query
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matches = (
          land.title.toLowerCase().includes(q) ||
          land.location.toLowerCase().includes(q) ||
          land.district.toLowerCase().includes(q) ||
          land.survey_number.toLowerCase().includes(q) ||
          land.description.toLowerCase().includes(q)
        );
        if (!matches) return false;
      }
      // Land Type filter
      if (selectedLandType && land.land_type !== selectedLandType) {
        return false;
      }
      // Legal status filter
      if (selectedLegalStatus) {
        if (selectedLegalStatus === 'clean' && land.legal_risks.length > 0) {
          return false;
        }
        if (selectedLegalStatus === 'disputed' && !land.legal_status.toLowerCase().includes('disputed')) {
          return false;
        }
      }
      // Budget filter
      if (land.total_price_lakhs > maxBudget) {
        return false;
      }
      // Acres filter
      if (land.acres < minAcres) {
        return false;
      }
      return true;
    });
  }, [lands, selectedDistrict, searchQuery, selectedLandType, selectedLegalStatus, maxBudget, minAcres]);

  const resetFilters = () => {
    setSearchQuery('');
    setSelectedDistrict('');
    setSelectedLandType('');
    setSelectedLegalStatus('');
    setMaxBudget(700);
    setMinAcres(0);
  };

  return (
    <div className="space-y-6">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-forest-950 via-forest-900 to-forest-800 rounded-3xl p-6 md:p-8 text-white shadow-elevated relative overflow-hidden">
        <div className="absolute right-0 top-0 bottom-0 w-1/3 bg-[radial-gradient(circle_at_top_right,rgba(217,119,6,0.25),transparent_70%)] pointer-events-none" />
        
        <div className="max-w-2xl relative z-10">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-gold/20 text-gold-light border border-gold/40 text-xs font-semibold mb-3">
            <span>Voice-First Land Intelligence</span>
          </div>
          <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight font-serif mb-2">
            {t.welcomeTitle}
          </h1>
          <p className="text-gray-300 text-xs md:text-sm leading-relaxed">
            {t.welcomeSubtitle}
          </p>
        </div>
      </div>

      {/* Stats Bar */}
      <StatsBar stats={stats} language={language} />

      {/* Filter and Search Bar */}
      <div className="bg-white rounded-2xl p-4 border border-ivory-border shadow-soft space-y-4">
        <div className="flex flex-col md:flex-row gap-3">
          {/* Search Input */}
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-gray-400 absolute left-3.5 top-3.5" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={t.searchPlaceholder}
              className="w-full pl-9 pr-4 py-2.5 rounded-xl border border-gray-200 text-xs focus:outline-none focus:ring-2 focus:ring-forest-800 focus:border-transparent bg-ivory-dark/30 placeholder-gray-400"
            />
          </div>

          {/* Land Type Filter */}
          <select
            value={selectedLandType}
            onChange={(e) => setSelectedLandType(e.target.value)}
            aria-label="Filter by land type"
            className="px-3.5 py-2.5 rounded-xl border border-gray-200 text-xs font-medium text-gray-700 bg-white focus:outline-none focus:ring-2 focus:ring-forest-800 cursor-pointer"
          >
            <option value="">{t.filterLandType}</option>
            {landTypes.map(lt => (
              <option key={lt} value={lt}>{lt}</option>
            ))}
          </select>

          {/* Legal Status Filter */}
          <select
            value={selectedLegalStatus}
            onChange={(e) => setSelectedLegalStatus(e.target.value)}
            aria-label="Filter by legal status"
            className="px-3.5 py-2.5 rounded-xl border border-gray-200 text-xs font-medium text-gray-700 bg-white focus:outline-none focus:ring-2 focus:ring-forest-800 cursor-pointer"
          >
            <option value="">{t.filterLegalStatus}: {t.filterAll}</option>
            <option value="clean">{t.filterClean}</option>
            <option value="disputed">{t.filterDisputed}</option>
          </select>

          {/* Reset button */}
          {(searchQuery || selectedLandType || selectedLegalStatus || selectedDistrict || maxBudget < 700 || minAcres > 0) && (
            <button
              onClick={resetFilters}
              className="flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-rose-700 hover:bg-rose-50 rounded-xl transition-colors shrink-0"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Reset</span>
            </button>
          )}
        </div>

        {/* Sliders row */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2 border-t border-gray-100 text-xs">
          <div>
            <div className="flex justify-between text-gray-600 mb-1">
              <span>{t.maxBudget}:</span>
              <span className="font-bold text-forest-950 font-serif">Up to ₹{maxBudget} Lakhs</span>
            </div>
            <input
              type="range"
              min={100}
              max={700}
              step={20}
              value={maxBudget}
              onChange={(e) => setMaxBudget(Number(e.target.value))}
              aria-label="Filter by maximum budget in lakhs"
              className="w-full accent-forest-900 cursor-pointer"
            />
          </div>

          <div>
            <div className="flex justify-between text-gray-600 mb-1">
              <span>Minimum Extent:</span>
              <span className="font-bold text-forest-950 font-serif">{minAcres} Acres</span>
            </div>
            <input
              type="range"
              min={0}
              max={15}
              step={1}
              value={minAcres}
              onChange={(e) => setMinAcres(Number(e.target.value))}
              aria-label="Filter by minimum acres"
              className="w-full accent-forest-900 cursor-pointer"
            />
          </div>
        </div>
      </div>

      {/* Property Cards Grid */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-bold text-forest-950 font-serif flex items-center gap-2">
            <span>Synthetic Demo Land Holdings · No Official Verification</span>
            <span className="text-xs bg-forest-100 text-forest-900 font-mono px-2 py-0.5 rounded-full font-bold">
              {filteredLands.length} available
            </span>
          </h2>
          <span className="text-xs text-gray-500 font-medium">
            AI highlights active when voice query matches
          </span>
        </div>

        {filteredLands.length === 0 ? (
          <div className="bg-white rounded-3xl p-12 text-center border border-ivory-border shadow-soft space-y-3">
            <Info className="w-10 h-10 text-gray-400 mx-auto" />
            <h3 className="font-bold text-gray-800 text-sm">No properties match your filter criteria</h3>
            <p className="text-xs text-gray-500 max-w-sm mx-auto">
              Try adjusting the budget slider, clearing the search query, or selecting all districts.
            </p>
            <button
              onClick={resetFilters}
              className="px-4 py-2 rounded-xl bg-forest-900 text-white text-xs font-bold hover:bg-forest-800 transition-colors"
            >
              Reset Filters
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredLands.map((land) => (
              <PropertyCard
                key={land.id}
                land={land}
                language={language}
                isAiMatched={aiMatchedLandIds.includes(land.id)}
                isInComparison={comparisonIds.includes(land.id)}
                isSaved={savedIds.includes(land.id)}
                onToggleCompare={onToggleCompare}
                onToggleSave={onToggleSave}
                onViewDetails={onViewDetails}
                onDownloadReport={onDownloadReport}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
