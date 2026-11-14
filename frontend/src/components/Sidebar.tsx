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
    { id: 'dashboard', label: 'Investigation studio', icon: Compass },
    { id: 'documents', label: t.docAnalyzer, icon: FileSearch },
    { id: 'claims', label: t.brokerChecker, icon: ShieldCheck },
    { id: 'compare', label: t.compare, icon: Scale, badge: comparisonCount },
    { id: 'growth', label: t.growthInsights, icon: TrendingUp },
    { id: 'saved', label: t.savedProperties, icon: Bookmark, badge: savedCount },
    { id: 'settings', label: t.settings, icon: Settings },
  ];

  return (
    <aside className="w-[72px] min-w-[72px] bg-forest-950 text-white flex flex-col h-screen sticky top-0 border-r border-forest-900 shadow-xl select-none z-30">
      {/* Brand Header */}
      <div className="p-4 border-b border-forest-900/80 flex items-center justify-center">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-gold-accent to-gold-dark flex items-center justify-center text-forest-950 font-black shadow-gold-glow">
          <Sparkles className="w-6 h-6 text-forest-950" />
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-2 py-4 space-y-2 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              title={item.label}
              aria-label={item.label}
              className={`relative w-full h-12 flex items-center justify-center rounded-xl text-sm font-medium transition-all duration-200 ${
                isActive
                  ? 'bg-forest-800 text-gold-light shadow-md shadow-black/20 border-l-2 border-gold'
                  : 'text-gray-300 hover:bg-forest-900/60 hover:text-white'
              }`}
            >
              <Icon className={`w-5 h-5 ${isActive ? 'text-gold' : 'text-gray-400'}`} />
              <span className="sr-only">{item.label}</span>
              {item.badge !== undefined && item.badge > 0 && (
                <span className="absolute top-1 right-1 px-1.5 py-0.5 text-[9px] font-bold rounded-full bg-gold text-forest-950">
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* AI Stack Status Box */}
      <div
        className="mx-auto mb-4 w-10 h-10 flex items-center justify-center rounded-xl bg-forest-900/70 border border-forest-800"
        title={mockMode ? 'Synthetic demo data; speech providers are disabled in mock mode' : 'Provider connectivity is shown in the studio'}
        aria-label={mockMode ? 'Synthetic demo data and mock mode' : 'AI provider status'}
      >
        <AlertCircle className={`w-4 h-4 ${mockMode ? 'text-amber-400' : 'text-emerald-400'}`} />
      </div>
    </aside>
  );
};
