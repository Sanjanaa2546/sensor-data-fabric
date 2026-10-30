import React, { useState, useEffect } from 'react';
import { Shield, CheckCircle2, XCircle, Clock, RefreshCw } from 'lucide-react';
import { fetchAuditLogs } from '../api/client';

export default function AuditTrail() {
  const [audits, setAudits] = useState([]);
  const [loading, setLoading] = useState(false);

  const loadAudits = async () => {
    setLoading(true);
    try {
      const data = await fetchAuditLogs(25);
      setAudits(data.audits || []);
    } catch (err) {
      console.error('Failed to load audit logs:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAudits();
  }, []);

  return (
    <div className="bg-slate-900/90 rounded-xl border border-slate-800 overflow-hidden shadow-lg">
      <div className="p-3.5 border-b border-slate-800 flex items-center justify-between bg-slate-950/40">
        <div className="flex items-center gap-2">
          <Shield className="w-4 h-4 text-indigo-400" />
          <h3 className="text-sm font-bold text-slate-200">Data Fabric Governance Audit Trail</h3>
          <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-mono">
            {audits.length} Records
          </span>
        </div>

        <button
          onClick={loadAudits}
          disabled={loading}
          className="p-1.5 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200 border border-slate-700 transition"
          title="Refresh Audits"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-indigo-400' : ''}`} />
        </button>
      </div>

      <div className="p-3.5 space-y-2 max-h-96 overflow-y-auto font-mono text-xs">
        {loading && <div className="text-center py-6 text-slate-500">Refreshing audit trail...</div>}
        {!loading && audits.length === 0 && (
          <div className="text-center py-6 text-slate-500">No query audit logs recorded yet.</div>
        )}

        {!loading && audits.map((a, idx) => (
          <div
            key={idx}
            className={`p-2.5 rounded-lg border ${
              a.is_safe
                ? 'bg-slate-950/60 border-slate-800 hover:border-slate-700'
                : 'bg-rose-950/20 border-rose-900/40 hover:border-rose-700'
            }`}
          >
            <div className="flex items-center justify-between mb-1.5">
              <div className="flex items-center gap-2">
                {a.is_safe ? (
                  <span className="flex items-center gap-1 text-[11px] text-emerald-400 font-sans font-bold">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    EXECUTED
                  </span>
                ) : (
                  <span className="flex items-center gap-1 text-[11px] text-rose-400 font-sans font-bold">
                    <XCircle className="w-3.5 h-3.5" />
                    BLOCKED
                  </span>
                )}
                <span className="text-[11px] text-slate-500">[{a.audit_id}]</span>
              </div>

              <div className="flex items-center gap-2 text-slate-400 text-[11px]">
                <span className="flex items-center gap-1">
                  <Clock className="w-3 h-3 text-sky-400" />
                  {a.execution_time_ms}ms
                </span>
                <span>•</span>
                <span>{a.row_count} rows</span>
              </div>
            </div>

            <div className="p-1.5 rounded bg-slate-900 border border-slate-800 text-slate-300 break-all text-[11px] mb-1">
              {a.query_text}
            </div>

            {a.rejection_reason && (
              <div className="text-[11px] text-rose-300 font-sans bg-rose-950/40 p-1.5 rounded border border-rose-900/40">
                Reason: {a.rejection_reason}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
