import React from 'react';
import { ShieldCheck, ShieldAlert, CheckCircle2, Clock, Terminal, Hash, AlertTriangle } from 'lucide-react';

export default function QueryInspector({ proposedSql, sanitizedSql, isSafe, rejectionReason, executionTimeMs, auditId, rowsCount }) {
  if (!proposedSql && !sanitizedSql) return null;

  return (
    <div className="mt-3 rounded-xl border border-slate-700/80 bg-slate-900/90 overflow-hidden shadow-xl text-xs font-mono">
      {/* Inspector Header */}
      <div className={`px-4 py-2.5 flex items-center justify-between border-b ${
        isSafe ? 'bg-slate-800/80 border-slate-700 text-slate-200' : 'bg-rose-950/40 border-rose-800/60 text-rose-300'
      }`}>
        <div className="flex items-center gap-2">
          {isSafe ? (
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          ) : (
            <ShieldAlert className="w-4 h-4 text-rose-400" />
          )}
          <span className="font-semibold tracking-wide">
            {isSafe ? 'SQL AST Guardrail: VALIDATED & PERMITTED' : 'SQL AST Guardrail: EXECUTION BLOCKED'}
          </span>
        </div>

        <div className="flex items-center gap-3 text-slate-400 font-sans">
          {executionTimeMs !== undefined && (
            <span className="flex items-center gap-1 text-[11px]">
              <Clock className="w-3 h-3 text-sky-400" />
              {executionTimeMs.toFixed(1)}ms
            </span>
          )}
          {auditId && (
            <span className="flex items-center gap-1 text-[11px] text-slate-400">
              <Hash className="w-3 h-3 text-indigo-400" />
              {auditId}
            </span>
          )}
        </div>
      </div>

      {/* Rejection Alert if unsafe */}
      {!isSafe && rejectionReason && (
        <div className="p-3.5 bg-rose-950/20 border-b border-rose-900/40 text-rose-300 flex items-start gap-2.5">
          <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
          <div>
            <div className="font-bold text-[11px] text-rose-400 uppercase tracking-wider mb-0.5">Policy Rejection Detail</div>
            <p className="text-xs leading-relaxed">{rejectionReason}</p>
          </div>
        </div>
      )}

      {/* AST Governance Checklist */}
      <div className="p-3 bg-slate-950/60 border-b border-slate-800/80 grid grid-cols-2 md:grid-cols-4 gap-2 font-sans text-[11px]">
        <div className="flex items-center gap-1.5 text-slate-300">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
          <span>AST Parsed (sqlglot)</span>
        </div>
        <div className="flex items-center gap-1.5 text-slate-300">
          <CheckCircle2 className={`w-3.5 h-3.5 ${isSafe ? 'text-emerald-400' : 'text-rose-400'}`} />
          <span>SELECT-Only Enforced</span>
        </div>
        <div className="flex items-center gap-1.5 text-slate-300">
          <CheckCircle2 className={`w-3.5 h-3.5 ${isSafe ? 'text-emerald-400' : 'text-rose-400'}`} />
          <span>Table Allowlist Checked</span>
        </div>
        <div className="flex items-center gap-1.5 text-slate-300">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
          <span>Row Limit Cap & Timeout</span>
        </div>
      </div>

      {/* SQL Viewers */}
      <div className="p-3.5 space-y-3">
        {/* Raw Proposed SQL */}
        {proposedSql && (
          <div>
            <div className="text-[10px] uppercase font-bold text-slate-400 mb-1 flex items-center gap-1">
              <Terminal className="w-3 h-3 text-amber-400" />
              <span>1. LLM Proposed Query (Unverified)</span>
            </div>
            <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 text-amber-200/90 whitespace-pre-wrap break-all leading-relaxed">
              {proposedSql}
            </div>
          </div>
        )}

        {/* Validated and Rewritten SQL */}
        {sanitizedSql && (
          <div>
            <div className="text-[10px] uppercase font-bold text-slate-400 mb-1 flex items-center gap-1">
              <CheckCircle2 className="w-3 h-3 text-emerald-400" />
              <span>2. Sanitized & Rewritten SQL (Executed in DuckDB)</span>
            </div>
            <div className="p-2.5 rounded-lg bg-slate-950 border border-emerald-900/40 text-emerald-300 whitespace-pre-wrap break-all leading-relaxed">
              {sanitizedSql}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
