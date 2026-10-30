import React, { useState } from 'react';
import Header from './components/Header';
import StationMetrics from './components/StationMetrics';
import ChatBox from './components/ChatBox';
import SensorChart from './components/SensorChart';
import DataTable from './components/DataTable';
import AnomalyAlerts from './components/AnomalyAlerts';
import AuditTrail from './components/AuditTrail';
import { BarChart3, Table, AlertOctagon, ShieldCheck, Terminal, Play } from 'lucide-react';
import { executeDirectSQL } from './api/client';

export default function App() {
  const [activeTab, setActiveTab] = useState('chart'); // 'chart', 'table', 'anomalies', 'audits'
  const [currentQueryResult, setCurrentQueryResult] = useState(null);
  
  // Direct SQL testing console state
  const [customSql, setCustomSql] = useState("SELECT city, AVG(pm25) AS avg_pm25 FROM air_quality_readings r JOIN sensor_stations s ON r.station_id = s.station_id GROUP BY city;");
  const [sqlTestingResult, setSqlTestingResult] = useState(null);
  const [sqlTestingLoading, setSqlTestingLoading] = useState(false);

  const handleQueryResult = (result) => {
    setCurrentQueryResult(result);
    if (result.rows && result.rows.length > 0) {
      // Default to chart view on valid results
      setActiveTab('chart');
    }
  };

  const runCustomSqlTest = async () => {
    if (!customSql.trim()) return;
    setSqlTestingLoading(true);
    try {
      const res = await executeDirectSQL(customSql);
      setSqlTestingResult(res);
      setCurrentQueryResult({
        rows: res.rows,
        columns: res.columns,
        is_safe: res.is_safe,
        proposed_sql: res.raw_sql,
        sanitized_sql: res.sanitized_sql,
        execution_time_ms: res.execution_time_ms,
        rejection_reason: res.rejection_reason,
        audit_id: res.audit_id
      });
    } catch (e) {
      console.error('SQL test error:', e);
    } finally {
      setSqlTestingLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-['Plus_Jakarta_Sans',sans-serif]">
      <Header />

      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 space-y-5">
        {/* Top Sensor Station Overview Cards */}
        <StationMetrics />

        {/* Main Workspace Split View */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
          {/* Left Column: Chat with Sensor Data */}
          <div className="lg:col-span-5">
            <ChatBox onQueryResult={handleQueryResult} currentResult={currentQueryResult} />
          </div>

          {/* Right Column: Visualizations, Tables & Governance Sentinel */}
          <div className="lg:col-span-7 flex flex-col space-y-4">
            {/* View Switcher Tabs */}
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <div className="flex items-center gap-1 bg-slate-900 p-1 rounded-xl border border-slate-800 text-xs">
                <button
                  onClick={() => setActiveTab('chart')}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-medium transition ${
                    activeTab === 'chart'
                      ? 'bg-sky-500 text-white shadow-md shadow-sky-500/20'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <BarChart3 className="w-3.5 h-3.5" />
                  <span>Visual Chart</span>
                </button>

                <button
                  onClick={() => setActiveTab('table')}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-medium transition ${
                    activeTab === 'table'
                      ? 'bg-sky-500 text-white shadow-md shadow-sky-500/20'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <Table className="w-3.5 h-3.5" />
                  <span>Data Table</span>
                  {currentQueryResult?.rows?.length > 0 && (
                    <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-slate-950 text-sky-300 font-mono">
                      {currentQueryResult.rows.length}
                    </span>
                  )}
                </button>

                <button
                  onClick={() => setActiveTab('anomalies')}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-medium transition ${
                    activeTab === 'anomalies'
                      ? 'bg-amber-500 text-slate-950 shadow-md font-bold'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <AlertOctagon className="w-3.5 h-3.5" />
                  <span>Anomaly Sentinel</span>
                </button>

                <button
                  onClick={() => setActiveTab('audits')}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-medium transition ${
                    activeTab === 'audits'
                      ? 'bg-indigo-600 text-white shadow-md'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <ShieldCheck className="w-3.5 h-3.5" />
                  <span>Audit Trail</span>
                </button>
              </div>

              <span className="text-[11px] font-mono text-slate-400 hidden sm:block">
                Powered by DuckDB OLAP
              </span>
            </div>

            {/* Active Tab Panel */}
            <div className="flex-1">
              {activeTab === 'chart' && (
                <SensorChart
                  rows={currentQueryResult?.rows || []}
                  columns={currentQueryResult?.columns || []}
                />
              )}

              {activeTab === 'table' && (
                <DataTable
                  rows={currentQueryResult?.rows || []}
                  columns={currentQueryResult?.columns || []}
                />
              )}

              {activeTab === 'anomalies' && (
                <AnomalyAlerts />
              )}

              {activeTab === 'audits' && (
                <AuditTrail />
              )}
            </div>

            {/* Direct SQL Tester Console (For Recruiters / Interviewers) */}
            <div className="bg-slate-900/80 rounded-xl border border-slate-800 p-4 shadow-lg text-xs">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Terminal className="w-4 h-4 text-emerald-400" />
                  <span className="font-bold text-slate-200">Guardrail SQL Console (Direct Testing)</span>
                </div>
                <div className="flex items-center gap-1 text-[11px] text-slate-400">
                  <span>Try:</span>
                  <button
                    onClick={() => setCustomSql("DROP TABLE sensor_stations;")}
                    className="text-rose-400 hover:underline font-mono"
                  >
                    DROP TABLE
                  </button>
                  <span>|</span>
                  <button
                    onClick={() => setCustomSql("SELECT * FROM air_quality_readings LIMIT 5000;")}
                    className="text-sky-400 hover:underline font-mono"
                  >
                    LIMIT Capping
                  </button>
                </div>
              </div>

              <div className="flex gap-2">
                <input
                  type="text"
                  value={customSql}
                  onChange={(e) => setCustomSql(e.target.value)}
                  className="flex-1 bg-slate-950 font-mono text-slate-200 text-xs px-3 py-2 rounded-lg border border-slate-700 focus:outline-none focus:border-emerald-500"
                  placeholder="Enter custom SQL to test AST guardrails..."
                />
                <button
                  onClick={runCustomSqlTest}
                  disabled={sqlTestingLoading}
                  className="px-3 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 font-semibold text-white flex items-center gap-1 transition shadow-md shadow-emerald-600/20"
                >
                  <Play className="w-3.5 h-3.5 fill-current" />
                  <span>Execute</span>
                </button>
              </div>

              {sqlTestingResult && (
                <div className={`mt-2.5 p-2 rounded-lg border text-[11px] font-mono ${
                  sqlTestingResult.is_safe
                    ? 'bg-emerald-950/20 border-emerald-900/40 text-emerald-300'
                    : 'bg-rose-950/30 border-rose-900/50 text-rose-300'
                }`}>
                  <div className="flex items-center justify-between font-bold mb-1">
                    <span>{sqlTestingResult.is_safe ? '✓ Query Passed AST Guardrail' : '✗ Query Blocked by Security Policy'}</span>
                    <span>{sqlTestingResult.execution_time_ms}ms • {sqlTestingResult.row_count} rows</span>
                  </div>
                  {sqlTestingResult.rejection_reason && (
                    <div className="text-rose-400">{sqlTestingResult.rejection_reason}</div>
                  )}
                  {sqlTestingResult.sanitized_sql && (
                    <div className="text-slate-400 break-all">{sqlTestingResult.sanitized_sql}</div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </main>

      <footer className="border-t border-slate-800/80 bg-slate-950 px-6 py-4 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>AeroFabric Sensor Data Fabric • Built for Enterprise AI & Data Architecture</span>
          <span className="font-mono text-[11px] text-slate-400">FastAPI • DuckDB • sqlglot • React • Vite</span>
        </div>
      </footer>
    </div>
  );
}
