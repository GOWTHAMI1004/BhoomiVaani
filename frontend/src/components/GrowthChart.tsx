import React, { useState } from 'react';
import { 
  ResponsiveContainer, 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  Tooltip, 
  CartesianGrid, 
  Legend 
} from 'recharts';
import { TrendingUp, AlertTriangle, ShieldCheck, Milestone, Info } from 'lucide-react';
import { LandListing, Language } from '../types';
import { getTranslation } from '../translations/i18n';

interface GrowthChartProps {
  lands: LandListing[];
  language: Language;
}

export const GrowthChart: React.FC<GrowthChartProps> = ({ lands, language }) => {
  const t = getTranslation(language);
  const [selectedLandId, setSelectedLandId] = useState<string>(lands[0]?.id || 'bv-hyd-01');
  const [timeframe, setTimeframe] = useState<'3yr' | '5yr'>('3yr');

  const selectedLand = lands.find(l => l.id === selectedLandId) || lands[0];
  if (!selectedLand) return null;

  // Generate synthetic illustrative scenario projections based on growth score and legal risks
  const basePrice = selectedLand.price_per_acre_lakhs;
  const isDisputed = selectedLand.legal_status.toLowerCase().includes('disputed');

  // Baseline simulated appreciation rate (e.g. 10-15% for clean infrastructure lands, -2% to 2% for disputed parcels)
  const conservativeRate = isDisputed ? 0.02 : (selectedLand.growth_score / 100) * 0.10;
  const acceleratedRate = isDisputed ? 0.04 : (selectedLand.growth_score / 100) * 0.16;

  const currentYear = 2024;
  const yearsCount = timeframe === '3yr' ? 3 : 5;

  const projectionData = [];
  for (let i = 0; i <= yearsCount; i++) {
    const yr = currentYear + i;
    const consVal = +(basePrice * Math.pow(1 + conservativeRate, i)).toFixed(1);
    const accelVal = +(basePrice * Math.pow(1 + acceleratedRate, i)).toFixed(1);

    projectionData.push({
      year: i === 0 ? 'Current (2024)' : `Year +${i} (${yr})`,
      conservative: consVal,
      accelerated: accelVal,
      base: basePrice
    });
  }

  return (
    <div className="bg-white rounded-3xl p-6 border border-ivory-border shadow-soft space-y-6">
      {/* Header & Property Selector */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-gray-100 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-amber-50 border border-amber-200 flex items-center justify-center text-amber-700">
              <TrendingUp className="w-5 h-5" />
            </div>
            <h2 className="text-xl font-bold text-forest-950 font-serif">Land Growth & Infrastructure Insights</h2>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Evaluate how confirmed infrastructure corridors influence parcel appreciation scenarios.
          </p>
        </div>

        {/* Controls */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Property Selector */}
          <select
            value={selectedLandId}
            onChange={(e) => setSelectedLandId(e.target.value)}
            aria-label="Select property for growth insights"
            className="text-xs font-semibold bg-ivory-dark/60 border border-ivory-border px-3 py-2 rounded-xl text-forest-950 focus:outline-none focus:ring-2 focus:ring-forest-800"
          >
            {lands.map((l) => (
              <option key={l.id} value={l.id}>
                {l.title} ({l.survey_number})
              </option>
            ))}
          </select>

          {/* Timeframe Toggle */}
          <div className="flex bg-ivory-dark p-1 rounded-xl border border-ivory-border text-xs font-bold">
            <button
              onClick={() => setTimeframe('3yr')}
              className={`px-3 py-1.5 rounded-lg transition-all ${
                timeframe === '3yr' ? 'bg-forest-900 text-white shadow-sm' : 'text-gray-600'
              }`}
            >
              3-Year Horizon
            </button>
            <button
              onClick={() => setTimeframe('5yr')}
              className={`px-3 py-1.5 rounded-lg transition-all ${
                timeframe === '5yr' ? 'bg-forest-900 text-white shadow-sm' : 'text-gray-600'
              }`}
            >
              5-Year Horizon
            </button>
          </div>
        </div>
      </div>

      {/* Selected Property Quick Spec Banner */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-ivory-dark/40 p-4 rounded-2xl border border-ivory-border text-xs">
        <div>
          <span className="text-gray-500">Current Valuation:</span>
          <div className="text-base font-black text-forest-950 font-serif">
            ₹{selectedLand.price_per_acre_lakhs} <span className="text-xs font-sans font-normal text-gray-600">Lakhs/Acre</span>
          </div>
        </div>
        <div>
          <span className="text-gray-500">AI Growth Score:</span>
          <div className="text-base font-black text-amber-700 font-serif">
            {selectedLand.growth_score} <span className="text-xs font-sans font-normal text-gray-400">/ 100</span>
          </div>
        </div>
        <div>
          <span className="text-gray-500">Legal Risk Status:</span>
          <div className={`font-bold flex items-center gap-1 ${
            !isDisputed ? 'text-emerald-700' : 'text-rose-600'
          }`}>
            {!isDisputed ? <ShieldCheck className="w-4 h-4" /> : <AlertTriangle className="w-4 h-4" />}
            <span>{!isDisputed ? 'Clean Title' : 'Litigation / Lien'}</span>
          </div>
        </div>
        <div>
          <span className="text-gray-500">Extent & Zone:</span>
          <div className="font-bold text-gray-800">
            {selectedLand.acres} Acres ({selectedLand.district})
          </div>
        </div>
      </div>

      {/* Recharts Area Chart */}
      <div className="h-72 w-full pt-2">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={projectionData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="colorAccel" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#15803D" stopOpacity={0.4}/>
                <stop offset="95%" stopColor="#15803D" stopOpacity={0.0}/>
              </linearGradient>
              <linearGradient id="colorCons" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#D97706" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#D97706" stopOpacity={0.0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#F0EBE1" />
            <XAxis dataKey="year" stroke="#9CA3AF" fontSize={11} />
            <YAxis
              unit=" L"
              domain={['dataMin - 5', 'dataMax + 10']}
              stroke="#9CA3AF"
              fontSize={11}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#0F3826',
                borderRadius: '12px',
                border: 'none',
                color: '#FFFFFF',
                fontSize: '12px'
              }}
              formatter={(val: any) => [`₹${val} Lakhs / Acre`, '']}
            />
            <Legend verticalAlign="top" height={36} iconType="circle" />
            <Area
              type="monotone"
              dataKey="accelerated"
              name="Infrastructure Acceleration Scenario"
              stroke="#15803D"
              strokeWidth={2.5}
              fillOpacity={1}
              fill="url(#colorAccel)"
            />
            <Area
              type="monotone"
              dataKey="conservative"
              name="Conservative Baseline Scenario"
              stroke="#D97706"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorCons)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Key Factors Analysis Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
        {/* Infrastructure Catalysts */}
        <div className="bg-emerald-50/60 border border-emerald-200/80 p-4 rounded-2xl text-xs space-y-2">
          <div className="font-bold text-emerald-950 flex items-center gap-1.5 text-sm">
            <Milestone className="w-4 h-4 text-emerald-700" />
            <span>Infrastructure Value Drivers</span>
          </div>
          <ul className="space-y-1.5 text-emerald-900">
            {selectedLand.infrastructure_evidence.map((inf, idx) => (
              <li key={idx} className="flex items-start justify-between gap-2">
                <span>• {inf.claim} ({inf.distance_km} km)</span>
                <span className="font-bold shrink-0">{inf.status}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Risk Multipliers */}
        <div className="bg-amber-50/60 border border-amber-200/80 p-4 rounded-2xl text-xs space-y-2">
          <div className="font-bold text-amber-950 flex items-center gap-1.5 text-sm">
            <AlertTriangle className="w-4 h-4 text-amber-700" />
            <span>Encumbrance & Liquidity Factors</span>
          </div>
          {selectedLand.legal_risks.length > 0 ? (
            <ul className="space-y-1 text-rose-900">
              {selectedLand.legal_risks.map((r, idx) => (
                <li key={idx}>
                  <strong>[{r.severity}]</strong> {r.risk_type} - {r.description}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-amber-900">
              Clear 30-year ancestral devolution and zero encumbrances provide maximum market liquidity and straightforward registration.
            </p>
          )}
        </div>
      </div>

      {/* Mandatory Statutory Disclaimer */}
      <div className="p-3 bg-ivory-dark border border-ivory-border rounded-xl flex items-start gap-2 text-xs text-gray-500">
        <Info className="w-4 h-4 text-gray-400 shrink-0 mt-0.5" />
        <p className="leading-relaxed">
          <strong>STATUTORY NOTICE:</strong> Projections displayed above represent illustrative mathematical scenarios derived from historical regional growth patterns and synthetic infrastructure models. They DO NOT constitute a prediction, guarantee, or investment return commitment. Land values may fluctuate due to policy amendments, macro conditions, and acquisition orders.
        </p>
      </div>
    </div>
  );
};
