import React from 'react';
import { 
  MapPin, 
  Languages, 
  Bell, 
  User, 
  Volume2, 
  VolumeX, 
  Sparkles,
  ShieldAlert
} from 'lucide-react';
import { Language } from '../types';
import { getTranslation } from '../translations/i18n';

interface HeaderProps {
  language: Language;
  setLanguage: (lang: Language) => void;
  selectedDistrict: string;
  setSelectedDistrict: (district: string) => void;
  districts: string[];
  autoPlayAudio: boolean;
  setAutoPlayAudio: (val: boolean) => void;
}

export const Header: React.FC<HeaderProps> = ({
  language,
  setLanguage,
  selectedDistrict,
  setSelectedDistrict,
  districts,
  autoPlayAudio,
  setAutoPlayAudio
}) => {
  const t = getTranslation(language);

  return (
    <header className="bg-ivory-light border-b border-ivory-border sticky top-0 z-20 shadow-sm px-6 py-3.5">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* Left: Location & Region Info */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 bg-ivory-dark/70 border border-ivory-border px-3 py-1.5 rounded-xl text-xs font-medium text-gray-700">
            <MapPin className="w-4 h-4 text-forest-700" />
            <select
              value={selectedDistrict}
              onChange={(e) => setSelectedDistrict(e.target.value)}
              aria-label="Filter properties by district"
              className="bg-transparent font-medium text-forest-950 focus:outline-none cursor-pointer"
            >
              <option value="">Telangana (All Districts)</option>
              {districts.map((d) => (
                <option key={d} value={d}>
                  {d} District
                </option>
              ))}
            </select>
          </div>

          <div className="hidden lg:flex items-center gap-1.5 text-xs text-amber-800 bg-amber-50 border border-amber-200/60 px-3 py-1.5 rounded-xl">
            <ShieldAlert className="w-3.5 h-3.5 text-amber-600 shrink-0" />
            <span>{t.disclaimerDemo}</span>
          </div>
        </div>

        {/* Right: Controls & Language Switcher */}
        <div className="flex items-center gap-3">
          {/* Audio Auto-Play Toggle */}
          <button
            onClick={() => setAutoPlayAudio(!autoPlayAudio)}
            title={autoPlayAudio ? 'Voice Auto-Play Enabled' : 'Voice Auto-Play Disabled'}
            className={`p-2 rounded-xl text-xs flex items-center gap-1.5 border transition-all ${
              autoPlayAudio 
                ? 'bg-forest-50 border-forest-200 text-forest-800' 
                : 'bg-gray-100 border-gray-200 text-gray-500'
            }`}
          >
            {autoPlayAudio ? <Volume2 className="w-4 h-4 text-forest-700" /> : <VolumeX className="w-4 h-4" />}
            <span className="hidden sm:inline font-medium">TTS Voice</span>
          </button>

          {/* Language Selector */}
          <div className="flex items-center bg-ivory-dark/80 p-1 rounded-xl border border-ivory-border">
            <Languages className="w-4 h-4 text-forest-800 ml-2 mr-1" />
            <button
              onClick={() => setLanguage('te')}
              className={`px-2.5 py-1 text-xs font-semibold rounded-lg transition-all ${
                language === 'te'
                  ? 'bg-forest-900 text-white shadow-sm'
                  : 'text-gray-600 hover:text-forest-900'
              }`}
            >
              తెలుగు
            </button>
            <button
              onClick={() => setLanguage('hi')}
              className={`px-2.5 py-1 text-xs font-semibold rounded-lg transition-all ${
                language === 'hi'
                  ? 'bg-forest-900 text-white shadow-sm'
                  : 'text-gray-600 hover:text-forest-900'
              }`}
            >
              हिन्दी
            </button>
            <button
              onClick={() => setLanguage('en')}
              className={`px-2.5 py-1 text-xs font-semibold rounded-lg transition-all ${
                language === 'en'
                  ? 'bg-forest-900 text-white shadow-sm'
                  : 'text-gray-600 hover:text-forest-900'
              }`}
            >
              English
            </button>
          </div>

          {/* User profile */}
          <div className="flex items-center gap-2.5 pl-2 border-l border-ivory-border">
            <div className="w-8 h-8 rounded-full bg-forest-900 text-white flex items-center justify-center font-bold text-xs shadow-sm">
              <User className="w-4 h-4" />
            </div>
            <div className="hidden sm:block text-left">
              <div className="text-xs font-bold text-gray-800">Land Buyer</div>
              <div className="text-[10px] text-gray-500">Telangana Zone</div>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
