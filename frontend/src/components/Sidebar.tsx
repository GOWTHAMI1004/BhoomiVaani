import React from 'react';
import { 
  Compass, 
  FileSearch, 
  ShieldCheck, 
  Scale, 
  TrendingUp, 
  Bookmark, 
  Settings, 
  Sparkles,
  AlertCircle
} from 'lucide-react';
import { Language } from '../types';
import { getTranslation } from '../translations/i18n';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  language: Language;
  comparisonCount: number;
  savedCount: number;
  mockMode: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  setActiveTab,
  language,
  comparisonCount,
  savedCount,
  mockMode
}) => {
  const t = getTranslation(language);

  const navItems = [
    { id: 'dashboard', label: t.dashboard, icon: Compass },
    { id: 'documents', label: t.docAnalyzer, icon: FileSearch },
    { id: 'claims', label: t.brokerChecker, icon: ShieldCheck },
    { id: 'compare', label: t.compare, icon: Scale, badge: comparisonCount },
    { id: 'growth', label: t.growthInsights, icon: TrendingUp },
    { id: 'saved', label: t.savedProperties, icon: Bookmark, badge: savedCount },
    { id: 'settings', label: t.settings, icon: Settings },
  ];

  return (
    <aside className="w-64 bg-forest-950 text-white flex flex-col h-screen sticky top-0 border-r border-forest-900 shadow-xl select-none z-30">
      {/* Brand Header */}
      <div className="p-6 border-b border-forest-900/80 flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-gold-accent to-gold-dark flex items-center justify-center text-forest-950 font-black shadow-gold-glow">
          <Sparkles className="w-6 h-6 text-forest-950" />
        </div>
        <div>
          <div className="flex items-center gap-1.5">
            <h1 className="text-xl font-bold tracking-tight text-white font-serif">{t.appTitle}</h1>
            <span className="text-[10px] bg-gold/20 text-gold-light border border-gold/40 px-1.5 py-0.5 rounded font-mono font-medium">AI 2.5</span>
          </div>
          <p className="text-[11px] text-gray-300 font-medium tracking-wide truncate max-w-[150px]">
            {t.tagline}
          </p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-5 space-y-1.5 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center justify-between px-3.5 py-3 rounded-xl text-sm font-medium transition-all duration-200 ${
                isActive
                  ? 'bg-forest-800 text-gold-light shadow-md shadow-black/20 border-l-4 border-gold'
                  : 'text-gray-300 hover:bg-forest-900/60 hover:text-white'
              }`}
            >
              <div className="flex items-center gap-3">
                <Icon className={`w-5 h-5 ${isActive ? 'text-gold' : 'text-gray-400'}`} />
                <span>{item.label}</span>
              </div>
              {item.badge !== undefined && item.badge > 0 && (
                <span className="px-2 py-0.5 text-xs font-bold rounded-full bg-gold text-forest-950">
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* AI Stack Status Box */}
      <div className="p-4 mx-3 mb-4 rounded-xl bg-forest-900/70 border border-forest-800 text-xs">
        <div className="flex items-center justify-between mb-2">
          <span className="text-gray-300 font-semibold uppercase tracking-wider text-[10px]">AI Pipeline</span>
          <span className={`px-1.5 py-0.5 rounded text-[10px] font-mono font-bold ${mockMode ? 'bg-amber-900/60 text-amber-300 border border-amber-600/40' : 'bg-emerald-900/60 text-emerald-300'}`}>
            {mockMode ? 'MOCK AI' : 'LIVE GNANI'}
          </span>
        </div>
        <div className="space-y-1 text-gray-400 text-[11px]">
          <div className="flex justify-between">
            <span>STT:</span>
            <span className="text-gray-200 font-mono">Prisma v2.5</span>
          </div>
          <div className="flex justify-between">
            <span>Reasoning:</span>
            <span className="text-gray-200 font-mono">Evon 30B</span>
          </div>
          <div className="flex justify-between">
            <span>TTS:</span>
            <span className="text-gray-200 font-mono">Timbre v2.5</span>
          </div>
        </div>

        <div className="mt-2.5 pt-2 border-t border-forest-800 flex items-center gap-1.5 text-[10px] text-amber-200/80">
          <AlertCircle className="w-3.5 h-3.5 text-amber-400 shrink-0" />
          <span>Fictional demo data</span>
        </div>
      </div>
    </aside>
  );
};
