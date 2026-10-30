import React, { useState, useEffect } from 'react';
import { Radio, MapPin, Wind, Thermometer, Droplets } from 'lucide-react';
import { fetchCitySummary } from '../api/client';

export default function StationMetrics() {
  const [summary, setSummary] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const data = await fetchCitySummary();
        setSummary(data.summary || []);
      } catch (e) {
        console.error('Failed to load summary:', e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
      {summary.map((s, idx) => (
        <div key={idx} className="bg-slate-900/80 border border-slate-800 rounded-xl p-3 shadow-md hover:border-slate-700 transition">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-slate-100 flex items-center gap-1">
              <MapPin className="w-3 h-3 text-sky-400" />
              {s.city}
            </span>
            <span className="text-[10px] text-slate-400">{s.country}</span>
          </div>

          <div className="space-y-1.5 text-xs font-mono">
            <div className="flex items-center justify-between">
              <span className="text-[11px] text-slate-400 font-sans flex items-center gap-1">
                <Wind className="w-3 h-3 text-amber-400" /> PM2.5
              </span>
              <span className={`font-bold ${s.avg_pm25 > 100 ? 'text-rose-400' : s.avg_pm25 > 50 ? 'text-amber-400' : 'text-emerald-400'}`}>
                {s.avg_pm25} µg/m³
              </span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-[11px] text-slate-400 font-sans flex items-center gap-1">
                <Thermometer className="w-3 h-3 text-sky-400" /> Temp
              </span>
              <span className="text-slate-300">
                {s.avg_temp}°C
              </span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-[11px] text-slate-400 font-sans flex items-center gap-1">
                <Droplets className="w-3 h-3 text-indigo-400" /> Humidity
              </span>
              <span className="text-slate-300">
                {s.avg_humidity}%
              </span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
