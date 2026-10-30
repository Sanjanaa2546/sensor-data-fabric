import React from 'react';
import { Activity, ShieldCheck, Database, Cpu, ExternalLink } from 'lucide-react';

export default function Header({ stats }) {
  return (
    <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-md sticky top-0 z-50 px-6 py-3.5">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Brand & Subtitle */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-sky-500/20 text-white font-bold">
            <Activity className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-extrabold tracking-tight text-white">
                AeroFabric <span className="text-xs px-2 py-0.5 rounded-full bg-sky-500/10 text-sky-400 border border-sky-500/20 font-semibold">Data Fabric v1.0</span>
              </h1>
            </div>
            <p className="text-xs text-slate-400">
              Enterprise IoT Sensor Fabric • AST Guardrails • Embedded DuckDB OLAP • LLM Tool Calling
            </p>
          </div>
        </div>

        {/* Live System Architecture Badges */}
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-medium">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <Database className="w-3.5 h-3.5" />
            <span>DuckDB Columnar</span>
          </div>

          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-medium">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>sqlglot AST Guardrails Active</span>
          </div>

          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-amber-500/10 border border-amber-500/20 text-amber-400 text-xs font-medium">
            <Cpu className="w-3.5 h-3.5" />
            <span>LLM Tool-Calling Agent</span>
          </div>
        </div>
      </div>
    </header>
  );
}
