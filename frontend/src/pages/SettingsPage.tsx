import React from 'react';
import { 
  Settings, 
  Cpu, 
  Database, 
  ShieldCheck, 
  Key, 
  Languages, 
  Info,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';
import { Language } from '../types';
import { getTranslation } from '../translations/i18n';

interface SettingsPageProps {
  language: Language;
  setLanguage: (lang: Language) => void;
  mockMode: boolean;
  autoPlayAudio: boolean;
  setAutoPlayAudio: (val: boolean) => void;
}

export const SettingsPage: React.FC<SettingsPageProps> = ({
  language,
  setLanguage,
  mockMode,
  autoPlayAudio,
  setAutoPlayAudio
}) => {
  const t = getTranslation(language);

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="bg-white rounded-3xl p-6 md:p-8 border border-ivory-border shadow-soft flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-10 h-10 rounded-xl bg-forest-900 text-gold flex items-center justify-center font-bold shadow-sm">
            <Settings className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-black text-forest-950 font-serif">
              BhoomiVaani System & AI Configuration
            </h1>
            <p className="text-xs text-gray-500">
              Manage speech services, external reasoning configuration, and language preferences.
            </p>
          </div>
        </div>

        <span className={`px-3 py-1 rounded-full text-xs font-mono font-bold border ${
          mockMode 
            ? 'bg-amber-100 text-amber-900 border-amber-300' 
            : 'bg-emerald-100 text-emerald-900 border-emerald-300'
        }`}>
          {mockMode ? 'MOCK MODE — LIVE PROVIDERS DISABLED' : 'PROVIDER STATUS FROM BACKEND'}
        </span>
      </div>

      {/* Gnani AI Pipeline Architecture */}
      <div className="bg-white rounded-3xl p-6 md:p-8 border border-ivory-border shadow-soft space-y-4">
        <h2 className="text-base font-bold text-forest-950 font-serif flex items-center gap-2">
          <Cpu className="w-5 h-5 text-forest-800" />
          <span>Speech and reasoning providers</span>
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          {/* Prisma v2.5 STT */}
          <div className="p-4 rounded-2xl bg-ivory-dark/40 border border-ivory-border space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-bold text-gray-800 text-sm">Prisma v3.0</span>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-forest-100 text-forest-900 font-bold">STT</span>
            </div>
            <p className="text-gray-600 leading-relaxed">
              Short microphone recordings are transcribed by Gnani Prisma v3.0. The backend reads the key from GNANI_API_KEY and does not fabricate transcripts.
            </p>
            <div className="text-[11px] font-mono text-gray-500 pt-1">
              Endpoint: <span className="text-forest-900">https://api.vachana.ai/stt/v3</span>
            </div>
          </div>

          {/* External reasoning provider */}
          <div className="p-4 rounded-2xl bg-ivory-dark/40 border border-ivory-border space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-bold text-gray-800 text-sm">External reasoning model</span>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-gold/20 text-gold-dark font-bold">REASONING</span>
            </div>
            <p className="text-gray-600 leading-relaxed">
              No provider has been selected yet. Reasoning requests show a clear error until an external LLM and its API contract are provided; no mock answer is returned.
            </p>
            <div className="text-[11px] font-mono text-gray-500 pt-1">
              Configure after provider selection using the REASONING_* environment variables.
            </div>
          </div>

          {/* Timbre v2.5 TTS */}
          <div className="p-4 rounded-2xl bg-ivory-dark/40 border border-ivory-border space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-bold text-gray-800 text-sm">Timbre v2.5</span>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-forest-100 text-forest-900 font-bold">TTS</span>
            </div>
            <p className="text-gray-600 leading-relaxed">
              Gnani Timbre v2.5 speech synthesis when credentials are configured. Mock mode returns no fabricated audio.
            </p>
            <div className="text-[11px] font-mono text-gray-500 pt-1">
              Voices: <span className="text-forest-900">Language-specific catalog voices</span>
            </div>
          </div>
        </div>
      </div>

      {/* Preferences & Toggles */}
      <div className="bg-white rounded-3xl p-6 md:p-8 border border-ivory-border shadow-soft space-y-5">
        <h2 className="text-base font-bold text-forest-950 font-serif flex items-center gap-2">
          <Languages className="w-5 h-5 text-forest-800" />
          <span>Language & Audio Preferences</span>
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          {/* Active Language */}
          <div className="p-4 rounded-2xl border border-gray-200 flex items-center justify-between">
            <div>
              <div className="font-bold text-gray-800">Interface Language</div>
              <div className="text-gray-500 mt-0.5">Conversation language is selected independently in the investigation studio</div>
            </div>
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value as Language)}
              aria-label="Select interface language"
              className="px-3 py-1.5 rounded-xl border border-gray-200 text-xs font-bold text-forest-900 bg-ivory-dark focus:outline-none"
            >
              <option value="te">తెలుగు (Telugu)</option>
              <option value="hi">हिन्दी (Hindi)</option>
              <option value="en">English (India)</option>
            </select>
          </div>

          {/* Autoplay Voice */}
          <div className="p-4 rounded-2xl border border-gray-200 flex items-center justify-between">
            <div>
              <div className="font-bold text-gray-800">Auto-Play Voice Responses</div>
              <div className="text-gray-500 mt-0.5">Play Timbre audio immediately when AI answers</div>
            </div>
            <button
              onClick={() => setAutoPlayAudio(!autoPlayAudio)}
              className={`w-12 h-6 rounded-full transition-colors relative ${
                autoPlayAudio ? 'bg-forest-900' : 'bg-gray-300'
              }`}
            >
              <span
                className={`w-5 h-5 rounded-full bg-white absolute top-0.5 transition-transform ${
                  autoPlayAudio ? 'left-6.5' : 'left-0.5'
                }`}
              />
            </button>
          </div>
        </div>
      </div>

      {/* Synthetic Dataset Transparency */}
      <div className="bg-white rounded-3xl p-6 md:p-8 border border-ivory-border shadow-soft space-y-3">
        <h2 className="text-base font-bold text-forest-950 font-serif flex items-center gap-2">
          <Database className="w-5 h-5 text-forest-800" />
          <span>Synthetic Database Disclosure</span>
        </h2>
        <div className="p-4 rounded-2xl bg-amber-50 border border-amber-200 text-xs text-amber-900 space-y-2">
          <p className="leading-relaxed">
            <strong>Prototype Compliance Note:</strong> BhoomiVaani utilizes exactly 6 synthetic property listings situated in Chevella, Vikarabad, Shadnagar, Keesara, Yadadri, and Narsapur.
          </p>
          <ul className="list-disc list-inside space-y-1 text-amber-800">
            <li>5 demo listings have no risk entry in the example dataset; none has been officially title-verified.</li>
            <li>1 disputed scenario (Plot 4, Keesara, SY-104/MOCK) demonstrates mortgage and inheritance risk indicators; it is not a real parcel.</li>
            <li>All infrastructure references are synthetic examples and have not been independently checked against government records.</li>
          </ul>
        </div>
      </div>
    </div>
  );
};
