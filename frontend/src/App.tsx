import React, { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { VoiceAssistant } from './components/VoiceAssistant';
import { PropertyDetailsModal } from './components/PropertyDetailsModal';
import { GrowthChart } from './components/GrowthChart';
import { Dashboard } from './pages/Dashboard';
import { ClaimChecker } from './pages/ClaimChecker';
import { DocumentAnalyzer } from './pages/DocumentAnalyzer';
import { ComparisonPage } from './pages/ComparisonPage';
import { SavedProperties } from './pages/SavedProperties';
import { SettingsPage } from './pages/SettingsPage';
import { LandListing, LandStats, Language } from './types';
import { api } from './services/api';
import { Sparkles, MessageSquare, X } from 'lucide-react';

export const App: React.FC = () => {
  const [lands, setLands] = useState<LandListing[]>([]);
  const [stats, setStats] = useState<LandStats | null>(null);
  const [activeTab, setActiveTab] = useState<string>('dashboard');
  const [language, setLanguage] = useState<Language>('te');
  const [selectedDistrict, setSelectedDistrict] = useState<string>('');
  const [aiMatchedLandIds, setAiMatchedLandIds] = useState<string[]>([]);
  const [comparisonIds, setComparisonIds] = useState<string[]>([]);
  const [savedIds, setSavedIds] = useState<string[]>(['bv-hyd-01']);
  const [selectedLandModal, setSelectedLandModal] = useState<LandListing | null>(null);
  const [mockMode, setMockMode] = useState<boolean>(true);
  const [autoPlayAudio, setAutoPlayAudio] = useState<boolean>(true);
  const [isMobileVoiceOpen, setIsMobileVoiceOpen] = useState<boolean>(false);

  // Load initial data
  useEffect(() => {
    // Health check
    api.getHealth()
      .then(res => {
        setMockMode(res.mock_mode);
        if (res.default_language && ['te', 'hi', 'en'].includes(res.default_language)) {
          setLanguage(res.default_language as Language);
        }
      })
      .catch(err => console.warn('Health check warning:', err));

    // Load lands
    api.getLands()
      .then(data => setLands(data))
      .catch(err => console.error('Failed to load lands:', err));

    // Load stats
    api.getStats()
      .then(s => setStats(s))
      .catch(err => console.error('Failed to load stats:', err));
  }, []);

  const handleToggleCompare = (id: string) => {
    setComparisonIds(prev => {
      if (prev.includes(id)) {
        return prev.filter(x => x !== id);
      }
      if (prev.length >= 3) {
        alert('You can compare a maximum of 3 properties at a time.');
        return prev;
      }
      return [...prev, id];
    });
  };

  const handleToggleSave = (id: string) => {
    setSavedIds(prev => {
      if (prev.includes(id)) {
        return prev.filter(x => x !== id);
      }
      return [...prev, id];
    });
  };

  const handleDownloadReport = async (landId: string, surveyNo: string) => {
    try {
      await api.downloadReport(landId, surveyNo);
    } catch (err: any) {
      alert(`Could not download report: ${err.message || 'Please check backend server'}`);
    }
  };

  const districts = stats?.districts || ['Ranga Reddy', 'Vikarabad', 'Medchal-Malkajgiri', 'Yadadri Bhuvanagiri', 'Medak'];

  return (
    <div className="flex h-screen overflow-hidden bg-ivory">
      {/* 1. Left Sidebar */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        language={language}
        comparisonCount={comparisonIds.length}
        savedCount={savedIds.length}
        mockMode={mockMode}
      />

      {/* 2. Main Center Content Workspace */}
      <div className="flex-1 flex flex-col h-screen overflow-hidden">
        {/* Top Header */}
        <Header
          language={language}
          setLanguage={setLanguage}
          selectedDistrict={selectedDistrict}
          setSelectedDistrict={setSelectedDistrict}
          districts={districts}
          autoPlayAudio={autoPlayAudio}
          setAutoPlayAudio={setAutoPlayAudio}
        />

        {/* Dynamic Page Workspace Body */}
        <main className="flex-1 overflow-y-auto p-4 md:p-6 lg:p-8">
          {activeTab === 'dashboard' && (
            <Dashboard
              lands={lands}
              stats={stats}
              language={language}
              aiMatchedLandIds={aiMatchedLandIds}
              comparisonIds={comparisonIds}
              savedIds={savedIds}
              onToggleCompare={handleToggleCompare}
              onToggleSave={handleToggleSave}
              onViewDetails={(land) => setSelectedLandModal(land)}
              onDownloadReport={handleDownloadReport}
              selectedDistrict={selectedDistrict}
              setSelectedDistrict={setSelectedDistrict}
            />
          )}

          {activeTab === 'claims' && (
            <ClaimChecker lands={lands} language={language} />
          )}

          {activeTab === 'documents' && (
            <DocumentAnalyzer language={language} />
          )}

          {activeTab === 'compare' && (
            <ComparisonPage
              lands={lands}
              comparisonIds={comparisonIds}
              onToggleCompare={handleToggleCompare}
              onViewDetails={(land) => setSelectedLandModal(land)}
              onDownloadReport={handleDownloadReport}
              language={language}
            />
          )}

          {activeTab === 'growth' && (
            <div className="max-w-4xl mx-auto">
              <GrowthChart lands={lands} language={language} />
            </div>
          )}

          {activeTab === 'saved' && (
            <SavedProperties
              lands={lands}
              savedIds={savedIds}
              comparisonIds={comparisonIds}
              aiMatchedLandIds={aiMatchedLandIds}
              onToggleCompare={handleToggleCompare}
              onToggleSave={handleToggleSave}
              onViewDetails={(land) => setSelectedLandModal(land)}
              onDownloadReport={handleDownloadReport}
              onNavigateToExplore={() => setActiveTab('dashboard')}
              language={language}
            />
          )}

          {activeTab === 'settings' && (
            <SettingsPage
              language={language}
              setLanguage={setLanguage}
              mockMode={mockMode}
              autoPlayAudio={autoPlayAudio}
              setAutoPlayAudio={setAutoPlayAudio}
            />
          )}
        </main>
      </div>

      {/* 3. Right Voice Assistant Panel (Desktop) */}
      <div className="hidden xl:block w-[380px] h-screen p-3.5 bg-ivory-dark/40 border-l border-ivory-border">
        <VoiceAssistant
          language={language}
          setLanguage={setLanguage}
          onMatchedLands={(ids) => {
            setAiMatchedLandIds(ids);
            if (activeTab !== 'dashboard') {
              setActiveTab('dashboard');
            }
          }}
          autoPlayAudio={autoPlayAudio}
          onSelectLandModal={(id) => {
            const match = lands.find(l => l.id === id);
            if (match) setSelectedLandModal(match);
          }}
        />
      </div>

      {/* Mobile Floating Voice Assistant Toggle Button */}
      <button
        onClick={() => setIsMobileVoiceOpen(true)}
        className="xl:hidden fixed bottom-6 right-6 z-40 p-4 rounded-full bg-forest-900 text-gold shadow-forest-glow hover:scale-105 transition-all flex items-center gap-2 border border-gold/40"
      >
        <Sparkles className="w-5 h-5 text-gold" />
        <span className="text-xs font-bold text-white pr-1">Voice AI</span>
      </button>

      {/* Mobile Voice Assistant Modal / Drawer */}
      {isMobileVoiceOpen && (
        <div className="xl:hidden fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-end sm:items-center justify-center p-2 sm:p-4">
          <div className="w-full max-w-lg h-[85vh] bg-white rounded-3xl overflow-hidden relative shadow-2xl">
            <button
              onClick={() => setIsMobileVoiceOpen(false)}
              className="absolute top-4 right-4 z-20 p-2 rounded-full bg-black/40 text-white hover:bg-black/60"
            >
              <X className="w-5 h-5" />
            </button>
            <VoiceAssistant
              language={language}
              setLanguage={setLanguage}
              onMatchedLands={(ids) => {
                setAiMatchedLandIds(ids);
                setIsMobileVoiceOpen(false);
                if (activeTab !== 'dashboard') {
                  setActiveTab('dashboard');
                }
              }}
              autoPlayAudio={autoPlayAudio}
              onSelectLandModal={(id) => {
                const match = lands.find(l => l.id === id);
                if (match) {
                  setSelectedLandModal(match);
                  setIsMobileVoiceOpen(false);
                }
              }}
            />
          </div>
        </div>
      )}

      {/* 4. Property Details Modal */}
      {selectedLandModal && (
        <PropertyDetailsModal
          land={selectedLandModal}
          onClose={() => setSelectedLandModal(null)}
          language={language}
          onDownloadReport={handleDownloadReport}
          isInComparison={comparisonIds.includes(selectedLandModal.id)}
          onToggleCompare={handleToggleCompare}
        />
      )}
    </div>
  );
};
