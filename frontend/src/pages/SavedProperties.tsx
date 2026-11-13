import React from 'react';
import { Bookmark, Compass } from 'lucide-react';
import { LandListing, Language } from '../types';
import { getTranslation } from '../translations/i18n';
import { PropertyCard } from '../components/PropertyCard';

interface SavedPropertiesProps {
  lands: LandListing[];
  savedIds: string[];
  comparisonIds: string[];
  aiMatchedLandIds: string[];
  onToggleCompare: (id: string) => void;
  onToggleSave: (id: string) => void;
  onViewDetails: (land: LandListing) => void;
  onDownloadReport: (id: string, surveyNo: string) => void;
  onNavigateToExplore: () => void;
  language: Language;
}

export const SavedProperties: React.FC<SavedPropertiesProps> = ({
  lands,
  savedIds,
  comparisonIds,
  aiMatchedLandIds,
  onToggleCompare,
  onToggleSave,
  onViewDetails,
  onDownloadReport,
  onNavigateToExplore,
  language
}) => {
  const t = getTranslation(language);
  const savedLands = lands.filter(l => savedIds.includes(l.id));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-3xl p-6 md:p-8 border border-ivory-border shadow-soft flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-10 h-10 rounded-xl bg-forest-900 text-gold flex items-center justify-center font-bold shadow-sm">
            <Bookmark className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-black text-forest-950 font-serif">
              Saved Property Watchlist
            </h1>
            <p className="text-xs text-gray-500">
              Easily review and track shortlisted agricultural land records.
            </p>
          </div>
        </div>
        <span className="text-xs font-bold px-3 py-1 bg-ivory-dark border border-ivory-border text-forest-950 rounded-xl">
          {savedLands.length} Bookmarked
        </span>
      </div>

      {savedLands.length === 0 ? (
        <div className="bg-white rounded-3xl p-12 text-center border border-ivory-border shadow-soft space-y-4">
          <Bookmark className="w-12 h-12 text-gray-400 mx-auto" />
          <h3 className="font-bold text-gray-800 text-base font-serif">Your watchlist is currently empty</h3>
          <p className="text-xs text-gray-500 max-w-sm mx-auto">
            Click the bookmark icon on any property card from the Explore Land dashboard to save it here for fast reference.
          </p>
          <button
            onClick={onNavigateToExplore}
            className="px-5 py-2.5 rounded-xl bg-forest-900 text-white text-xs font-bold hover:bg-forest-800 transition-colors inline-flex items-center gap-2 shadow-sm"
          >
            <Compass className="w-4 h-4 text-gold" />
            <span>Explore Land Listings</span>
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {savedLands.map((land) => (
            <PropertyCard
              key={land.id}
              land={land}
              language={language}
              isAiMatched={aiMatchedLandIds.includes(land.id)}
              isInComparison={comparisonIds.includes(land.id)}
              isSaved={true}
              onToggleCompare={onToggleCompare}
              onToggleSave={onToggleSave}
              onViewDetails={onViewDetails}
              onDownloadReport={onDownloadReport}
            />
          ))}
        </div>
      )}
    </div>
  );
};
