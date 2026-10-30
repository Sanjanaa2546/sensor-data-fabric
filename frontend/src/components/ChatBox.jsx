import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Sparkles, Terminal, ChevronDown, ChevronUp, ShieldAlert, ShieldCheck } from 'lucide-react';
import QueryInspector from './QueryInspector';

const SUGGESTIONS = [
  { label: 'Worst PM2.5 last week', query: 'Which city had the worst PM2.5 last week?' },
  { label: 'Compare Delhi & London', query: 'Compare air quality between London and Delhi over the past 14 days' },
  { label: 'Scan for sensor anomalies', query: 'Scan and detect unusual spikes or anomalies in sensor readings' },
  { label: 'Test Guardrail: DROP TABLE', query: 'Can you run DROP TABLE sensor_stations to test security?' },
  { label: 'Paris temperature trend', query: 'What is the average temperature and humidity in Paris?' }
];

export default function ChatBox({ onQueryResult, currentResult }) {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      sender: 'assistant',
      text: "👋 **Hello! I'm your IoT Sensor Data Fabric Assistant.**\n\nI can analyze air quality telemetry across our global sensor stations (Delhi, London, NYC, Beijing, Paris).\n\n🛡️ **Enterprise Governance Note:** I never query DuckDB directly. Every query I propose is AST-parsed by `sqlglot`, verified for SELECT-only permissions, capped with row limits, and monitored for time-series anomalies.",
      proposedSql: null,
      sanitizedSql: null,
      isSafe: true,
      time: 'Just now'
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [expandedInspectorId, setExpandedInspectorId] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSubmit = async (e, textToSend) => {
    if (e) e.preventDefault();
    const queryText = (textToSend || input).trim();
    if (!queryText || loading) return;

    const userMsg = {
      id: `usr_${Date.now()}`,
      sender: 'user',
      text: queryText,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const response = await fetch('/api/chat/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: queryText })
      });
      const data = await response.json();

      const assistantMsg = {
        id: `asst_${Date.now()}`,
        sender: 'assistant',
        text: data.message,
        toolUsed: data.tool_used,
        proposedSql: data.proposed_sql,
        sanitizedSql: data.sanitized_sql,
        isSafe: data.is_safe,
        rejectionReason: data.rejection_reason,
        executionTimeMs: data.execution_time_ms,
        auditId: data.audit_id,
        rows: data.rows,
        columns: data.columns,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };

      setMessages(prev => [...prev, assistantMsg]);
      if (data.proposedSql || data.sanitizedSql || data.rejection_reason) {
        setExpandedInspectorId(assistantMsg.id);
      }

      // Propagate result to parent for charts & table
      if (onQueryResult) {
        onQueryResult(data);
      }
    } catch (err) {
      console.error('Chat error:', err);
      setMessages(prev => [
        ...prev,
        {
          id: `err_${Date.now()}`,
          sender: 'assistant',
          text: `⚠️ **Connection Error**: Unable to reach Data Fabric API (${err.message}). Verify that backend is running on port 8000.`,
          isSafe: false,
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-slate-900/90 rounded-2xl border border-slate-800 shadow-xl flex flex-col h-[750px] overflow-hidden">
      {/* Chat Header */}
      <div className="p-4 border-b border-slate-800 bg-slate-950/60 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-sky-500/10 border border-sky-500/20 flex items-center justify-center text-sky-400">
            <Bot className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              Sensor Data Assistant
              <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
            </h2>
            <p className="text-[11px] text-slate-400">Tool-calling AI with AST Query Validation</p>
          </div>
        </div>

        <div className="text-xs text-slate-400 hidden sm:block">
          <span className="font-mono bg-slate-800/80 px-2 py-0.5 rounded border border-slate-700 text-slate-300">
            run_query & detect_anomalies
          </span>
        </div>
      </div>

      {/* Suggested Prompts Pills */}
      <div className="p-2.5 bg-slate-950/40 border-b border-slate-800/80 flex items-center gap-1.5 overflow-x-auto text-xs no-scrollbar">
        <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider pl-1 shrink-0 flex items-center gap-1">
          <Sparkles className="w-3 h-3 text-amber-400" /> Suggestions:
        </span>
        {SUGGESTIONS.map((s, idx) => (
          <button
            key={idx}
            onClick={() => handleSubmit(null, s.query)}
            disabled={loading}
            className="px-2.5 py-1 rounded-full bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700/80 shrink-0 text-xs transition"
          >
            {s.label}
          </button>
        ))}
      </div>

      {/* Message Stream */}
      <div className="flex-1 p-4 overflow-y-auto space-y-4">
        {messages.map((m) => {
          const isUser = m.sender === 'user';
          const hasInspection = m.proposedSql || m.sanitizedSql || m.rejectionReason;
          const isExpanded = expandedInspectorId === m.id;

          return (
            <div
              key={m.id}
              className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}
            >
              {!isUser && (
                <div className="w-7 h-7 rounded-lg bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 shrink-0 mt-0.5">
                  <Bot className="w-4 h-4" />
                </div>
              )}

              <div className={`max-w-[85%] rounded-2xl p-3.5 text-xs ${
                isUser
                  ? 'bg-sky-600 text-white rounded-br-none shadow-md shadow-sky-600/20'
                  : 'bg-slate-800/80 border border-slate-700/80 text-slate-200 rounded-bl-none shadow-md'
              }`}>
                {/* Message body */}
                <div className="whitespace-pre-wrap leading-relaxed space-y-2">
                  {m.text}
                </div>

                {/* Guardrail badge & Inspector toggle */}
                {hasInspection && (
                  <div className="mt-3 pt-2.5 border-t border-slate-700/60 flex items-center justify-between">
                    <button
                      onClick={() => setExpandedInspectorId(isExpanded ? null : m.id)}
                      className="flex items-center gap-1.5 text-[11px] font-mono text-slate-300 hover:text-white bg-slate-900/80 px-2.5 py-1 rounded border border-slate-700 transition"
                    >
                      <Terminal className="w-3 h-3 text-sky-400" />
                      <span>{isExpanded ? 'Hide Guardrail Inspector' : 'Inspect SQL AST & Audit'}</span>
                      {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                    </button>

                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded flex items-center gap-1 ${
                      m.isSafe ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' : 'bg-rose-950 text-rose-400 border border-rose-800'
                    }`}>
                      {m.isSafe ? <ShieldCheck className="w-3 h-3" /> : <ShieldAlert className="w-3 h-3" />}
                      {m.isSafe ? 'Guardrail Passed' : 'Query Blocked'}
                    </span>
                  </div>
                )}

                {/* Expandable Query Inspector */}
                {hasInspection && isExpanded && (
                  <QueryInspector
                    proposedSql={m.proposedSql}
                    sanitizedSql={m.sanitizedSql}
                    isSafe={m.isSafe}
                    rejectionReason={m.rejectionReason}
                    executionTimeMs={m.executionTimeMs}
                    auditId={m.auditId}
                    rowsCount={m.rows?.length || 0}
                  />
                )}

                <div className={`text-[10px] mt-1.5 text-right ${isUser ? 'text-sky-200/80' : 'text-slate-400'}`}>
                  {m.time}
                </div>
              </div>

              {isUser && (
                <div className="w-7 h-7 rounded-lg bg-sky-500/20 border border-sky-400/30 flex items-center justify-center text-sky-300 shrink-0 mt-0.5">
                  <User className="w-4 h-4" />
                </div>
              )}
            </div>
          );
        })}

        {loading && (
          <div className="flex gap-3 justify-start">
            <div className="w-7 h-7 rounded-lg bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 shrink-0">
              <Bot className="w-4 h-4" />
            </div>
            <div className="p-3.5 rounded-2xl bg-slate-800/80 border border-slate-700/80 rounded-bl-none text-xs text-slate-400 flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-sky-400 animate-ping"></div>
              <span>Proposing SQL query & verifying AST guardrails...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input bar */}
      <form onSubmit={(e) => handleSubmit(e, input)} className="p-3 bg-slate-950/80 border-t border-slate-800 flex items-center gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question (e.g. Which city had the worst PM2.5 last week?)..."
          disabled={loading}
          className="flex-1 bg-slate-900 border border-slate-700 rounded-xl px-4 py-2.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 transition"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="bg-sky-600 hover:bg-sky-500 disabled:opacity-40 disabled:hover:bg-sky-600 text-white p-2.5 rounded-xl transition shadow-md shadow-sky-600/20 flex items-center justify-center"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
}
