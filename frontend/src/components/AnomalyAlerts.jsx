import React, { useState, useEffect } from 'react';
import { AlertOctagon, TrendingUp, Filter, RefreshCw, Zap } from 'lucide-react';
import { fetchAnomalies } from '../api/client';

export default function AnomalyAlerts({ onSelectAnomaly }) {
  const [anomalies, setAnomalies] = useState([]);
  const [loading, setLoading] = useState(false);
  const [pollutant, setPollutant] = useState('pm25');

  const loadAnomalies = async (poll) => {
    setLoading(true);
    try {
      const data = await fetchAnomalies(poll);
      setAnomalies(data.anomalies || []);
    } catch (err) {
      console.error('Failed to load anomalies:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAnomalies(pollutant);
  }, [pollutant]);

  return (
    <div className="bg-slate-900/90 rounded-xl border border-slate-800 overflow-hidden shadow-lg">
      {/* Header */}
      <div className="p-3.5 border-b border-slate-800 flex flex-wrap items-center justify-between gap-3 bg-slate-950/40">
        <div className="flex items-center gap-2">
          <AlertOctagon className="w-4 h-4 text-amber-400" />
          <h3 className="text-sm font-bold text-slate-200">Time-Series Anomaly Sentinel</h3>
          <span className="text-xs px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20 font-mono">
            {anomalies.length} Flagged
          </span>
        </div>

        {/* Filter controls */}
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1 bg-slate-800/80 rounded-md p-0.5 border border-slate-700 text-xs">
            {['pm25', 'pm10', 'no2', 'o3', 'temperature'].map((p) => (
              <button
                key={p}
                onClick={() => setPollutant(p)}
                className={`px-2 py-1 rounded capitalize font-medium transition ${
                  pollutant === p ? 'bg-sky-500 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {p === 'temperature' ? 'Temp' : p.toUpperCase()}
              </button>
            ))}
          </div>

          <button
            onClick={() => loadAnomalies(pollutant)}
            disabled={loading}
            className="p-1.5 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200 border border-slate-700 transition"
            title="Refresh Scan"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-sky-400' : ''}`} />
          </button>
        </div>
      </div>

      {/* List of Anomalies */}
      <div className="p-3.5 space-y-2.5 max-h-96 overflow-y-auto">
        {loading && (
          <div className="text-center py-8 text-xs text-slate-500">
            Running statistical Z-score & rolling average scan...
          </div>
        )}

        {!loading && anomalies.length === 0 && (
          <div className="text-center py-8 text-slate-500 text-xs">
            No statistical anomalies flagged for {pollutant.toUpperCase()} within the active time window.
          </div>
        )}

        {!loading && anomalies.map((a, idx) => {
          const isCritical = a.severity === 'CRITICAL';
          const isHigh = a.severity === 'HIGH';

          return (
            <div
              key={idx}
              className={`p-3 rounded-lg border transition ${
                isCritical
                  ? 'bg-rose-950/20 border-rose-900/40 hover:border-rose-700'
                  : isHigh
                  ? 'bg-amber-950/20 border-amber-900/40 hover:border-amber-700'
                  : 'bg-slate-800/30 border-slate-800 hover:border-slate-700'
              }`}
            >
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold tracking-wide uppercase ${
                    isCritical
                      ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                      : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                  }`}>
                    {a.severity} ANOMALY
                  </span>
                  <span className="text-xs font-bold text-slate-200">{a.station_name}</span>
                  <span className="text-xs text-slate-400">({a.city})</span>
                </div>

                <div className="text-[11px] font-mono text-slate-400">
                  {a.timestamp.slice(0, 16)}
                </div>
              </div>

              {/* Plain language explanation */}
              <p className="text-xs text-slate-300 leading-relaxed mb-2 font-sans">
                {a.explanation}
              </p>

              {/* Stat badges */}
              <div className="flex flex-wrap items-center gap-2 text-[11px] font-mono">
                <span className="px-2 py-0.5 rounded bg-slate-950 border border-slate-800 text-sky-400">
                  Observed: <strong className="text-white">{a.value}</strong>
                </span>
                <span className="px-2 py-0.5 rounded bg-slate-950 border border-slate-800 text-slate-400">
                  24h Baseline: <strong className="text-slate-200">{a.rolling_mean}</strong>
                </span>
                <span className="px-2 py-0.5 rounded bg-slate-950 border border-slate-800 text-indigo-400">
                  Z-Score: <strong className="text-indigo-300">+{a.z_score}σ</strong>
                </span>
                <span className="px-2 py-0.5 rounded bg-slate-950 border border-slate-800 text-amber-400">
                  Spike: <strong className="text-amber-300">{a.spike_ratio}x</strong>
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
