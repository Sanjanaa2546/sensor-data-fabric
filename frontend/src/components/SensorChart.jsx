import React from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend
} from 'recharts';
import { BarChart3, TrendingUp, Info } from 'lucide-react';

export default function SensorChart({ rows, columns, title }) {
  if (!rows || rows.length === 0) {
    return (
      <div className="h-64 flex flex-col items-center justify-center text-slate-500 bg-slate-900/50 rounded-xl border border-slate-800 p-6">
        <BarChart3 className="w-10 h-10 mb-2 stroke-1 text-slate-600" />
        <p className="text-sm font-medium">No visualization available</p>
        <p className="text-xs text-slate-600">Query results did not return plottable metrics</p>
      </div>
    );
  }

  // Determine chart type based on columns
  const first = rows[0] || {};
  const keys = Object.keys(first);

  const hasTimestamp = keys.some(k => k.toLowerCase().includes('timestamp') || k.toLowerCase().includes('date') || k.toLowerCase().includes('time'));
  const hasCity = keys.some(k => k.toLowerCase() === 'city');
  const hasStation = keys.some(k => k.toLowerCase().includes('station'));

  // Numeric keys
  const numericKeys = keys.filter(k => {
    const val = first[k];
    return typeof val === 'number' && !k.toLowerCase().includes('id') && !k.toLowerCase().includes('lat') && !k.toLowerCase().includes('lon');
  });

  const chartTitle = title || (hasCity ? 'City Pollutant Breakdown' : 'Sensor Metric Telemetry');

  // Time-series Line Chart
  if (hasTimestamp && numericKeys.length > 0) {
    const timeKey = keys.find(k => k.toLowerCase().includes('timestamp') || k.toLowerCase().includes('date') || k.toLowerCase().includes('time'));
    const primaryMetric = numericKeys[0];
    const secondaryMetric = numericKeys.length > 1 ? numericKeys[1] : null;

    // Format timestamps for display
    const formattedData = rows.map(r => ({
      ...r,
      timeLabel: String(r[timeKey]).slice(-8, -3) || String(r[timeKey])
    }));

    return (
      <div className="bg-slate-900/90 rounded-xl border border-slate-800 p-4 shadow-lg">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-sky-400" />
            <h3 className="text-sm font-bold text-slate-200">{chartTitle}</h3>
          </div>
          <span className="text-xs px-2 py-0.5 rounded bg-sky-950/60 text-sky-400 border border-sky-800/40">
            Time-Series Trend ({rows.length} points)
          </span>
        </div>

        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={formattedData} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="timeLabel" stroke="#64748b" tick={{ fontSize: 11 }} />
              <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
              <Tooltip 
                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                itemStyle={{ color: '#e2e8f0' }}
              />
              <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '8px' }} />
              <Line 
                type="monotone" 
                dataKey={primaryMetric} 
                stroke="#38bdf8" 
                strokeWidth={2} 
                dot={{ r: 2, fill: '#38bdf8' }}
                activeDot={{ r: 5 }}
              />
              {secondaryMetric && (
                <Line 
                  type="monotone" 
                  dataKey={secondaryMetric} 
                  stroke="#fbbf24" 
                  strokeWidth={2} 
                  dot={{ r: 2, fill: '#fbbf24' }} 
                />
              )}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    );
  }

  // Categorical Bar Chart (e.g. Cities or Stations)
  const categoryKey = hasCity ? 'city' : (hasStation ? keys.find(k => k.includes('station')) : keys[0]);
  const primaryMetric = numericKeys[0] || (keys.includes('count') ? 'count' : null);
  const secondaryMetric = numericKeys.length > 1 ? numericKeys[1] : null;

  if (!primaryMetric) {
    return null;
  }

  return (
    <div className="bg-slate-900/90 rounded-xl border border-slate-800 p-4 shadow-lg">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <BarChart3 className="w-4 h-4 text-sky-400" />
          <h3 className="text-sm font-bold text-slate-200">{chartTitle}</h3>
        </div>
        <span className="text-xs px-2 py-0.5 rounded bg-indigo-950/60 text-indigo-400 border border-indigo-800/40">
          Comparative Aggregates
        </span>
      </div>

      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={rows} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey={categoryKey} stroke="#64748b" tick={{ fontSize: 11 }} />
            <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
            <Tooltip 
              contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
              itemStyle={{ color: '#e2e8f0' }}
            />
            <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '8px' }} />
            <Bar dataKey={primaryMetric} fill="#0ea5e9" radius={[4, 4, 0, 0]} />
            {secondaryMetric && (
              <Bar dataKey={secondaryMetric} fill="#818cf8" radius={[4, 4, 0, 0]} />
            )}
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
