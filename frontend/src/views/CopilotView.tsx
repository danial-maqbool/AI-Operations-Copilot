import React, { useState } from 'react';
import {
  Bot,
  User,
  Send,
  Code,
  ShieldCheck,
  FileText,
  CheckCircle2,
  Table,
  BarChart2,
  Sparkles,
  Info,
  ChevronRight,
  RefreshCw
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid
} from 'recharts';
import { api } from '../services/api';
import { CopilotResponse } from '../types';

interface MessageItem {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  response?: CopilotResponse;
  timestamp: string;
}

export const CopilotView: React.FC = () => {
  const [messages, setMessages] = useState<MessageItem[]>([
    {
      id: 'msg-welcome',
      role: 'assistant',
      content:
        'Hello! I am your AI Operations Copilot. I analyze live company data, enforce deterministic business rules, retrieve standard operating procedures, and recommend prioritized actions.\n\nYou can ask about delayed shipments, overdue receivables, low inventory, SLA breaches, or internal company policies.',
      timestamp: 'Just now'
    }
  ]);
  const [inputQuery, setInputQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [activeEvidence, setActiveEvidence] = useState<CopilotResponse | null>(null);

  const sampleQuestions = [
    'Which orders are delayed and what are the carrier causes?',
    'Which customers have overdue invoices exceeding $5,000?',
    'What is our policy for refund approvals under $5,000?',
    'Which products are below safety stock?',
    'Which support tickets have breached SLA?'
  ];

  const handleSend = async (questionToSend?: string) => {
    const q = (questionToSend || inputQuery).trim();
    if (!q || loading) return;

    const userMsg: MessageItem = {
      id: 'msg-' + Date.now(),
      role: 'user',
      content: q,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputQuery('');
    setLoading(true);

    try {
      const response: CopilotResponse = await api.sendCopilotMessage(q);
      const assistantMsg: MessageItem = {
        id: response.message_id || 'msg-' + Date.now(),
        role: 'assistant',
        content: response.direct_answer,
        response: response,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages((prev) => [...prev, assistantMsg]);
      setActiveEvidence(response);
    } catch (err) {
      const errorMsg: MessageItem = {
        id: 'msg-err-' + Date.now(),
        role: 'assistant',
        content: 'Apologies, encountered an error processing your query: ' + err,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-[calc(100vh-7.5rem)] gap-6 overflow-hidden">
      {/* Left Column: Chat Conversation Stream */}
      <div className="flex-1 flex flex-col bg-slate-900/80 border border-slate-800/80 rounded-2xl overflow-hidden shadow-sm">
        {/* Chat Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-5">
          {messages.map((m) => (
            <div key={m.id} className={`flex gap-3.5 ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              {m.role === 'assistant' && (
                <div className="w-8 h-8 rounded-xl bg-blue-600/20 text-blue-400 border border-blue-500/30 flex items-center justify-center shrink-0">
                  <Bot className="w-4 h-4" />
                </div>
              )}

              <div
                className={`max-w-2xl rounded-2xl p-4 text-sm leading-relaxed space-y-3 ${
                  m.role === 'user'
                    ? 'bg-blue-600 text-white rounded-tr-sm'
                    : 'bg-slate-800/70 text-slate-200 border border-slate-700/60 rounded-tl-sm'
                }`}
              >
                <div className="whitespace-pre-line">{m.content}</div>

                {/* Inline Chart if returned */}
                {m.response?.chart && (
                  <div className="mt-3 p-3 rounded-xl bg-slate-900/80 border border-slate-700/60">
                    <span className="text-xs font-semibold text-slate-300 block mb-2">
                      {m.response.chart.title}
                    </span>
                    <div className="h-44 w-full">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={m.response.chart.series}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                          <XAxis dataKey="name" stroke="#64748b" fontSize={10} />
                          <YAxis stroke="#64748b" fontSize={10} />
                          <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155' }} />
                          <Bar dataKey="value" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                )}

                {/* Inline Data Table if returned */}
                {m.response?.table_data && (
                  <div className="mt-3 rounded-lg overflow-x-auto border border-slate-700/60 bg-slate-900/60">
                    <table className="w-full text-xs text-left">
                      <thead className="bg-slate-950/80 text-slate-400">
                        <tr>
                          {m.response.table_data.columns?.slice(0, 5).map((c: any, idx: number) => (
                            <th key={idx} className="p-2 font-medium">{String(c)}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800">
                        {m.response.table_data.rows?.slice(0, 5).map((row: any, rIdx: number) => {
                          const cells = Array.isArray(row)
                            ? row
                            : (m.response!.table_data?.columns ? m.response!.table_data.columns.map((col: string) => row[col]) : Object.values(row));
                          return (
                            <tr key={rIdx} className="hover:bg-slate-800/40">
                              {cells.slice(0, 5).map((cell: any, cIdx: number) => (
                                <td key={cIdx} className="p-2 text-slate-300 font-mono text-[11px]">
                                  {cell !== null && cell !== undefined ? String(cell) : ''}
                                </td>
                              ))}
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                )}

                {/* Evidence Drawer Toggle Shortcut */}
                {m.response && (
                  <div className="pt-2 flex items-center justify-between border-t border-slate-700/50 text-xs">
                    <span className="text-[11px] text-slate-400">Confidence: <b className="text-emerald-400 font-semibold">{m.response.confidence}</b></span>
                    <button
                      onClick={() => setActiveEvidence(m.response!)}
                      className="text-xs text-cyan-400 hover:text-cyan-300 font-medium flex items-center gap-1"
                    >
                      <span>Inspect Evidence</span>
                      <ChevronRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                )}
              </div>

              {m.role === 'user' && (
                <div className="w-8 h-8 rounded-xl bg-slate-800 text-slate-300 border border-slate-700 flex items-center justify-center shrink-0">
                  <User className="w-4 h-4" />
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="flex gap-3.5 items-center text-slate-400 text-xs animate-pulse">
              <div className="w-8 h-8 rounded-xl bg-blue-600/20 flex items-center justify-center">
                <RefreshCw className="w-4 h-4 animate-spin text-blue-400" />
              </div>
              <span>Analyzing warehouse records, evaluating business rules...</span>
            </div>
          )}
        </div>

        {/* Suggested Quick Questions */}
        <div className="px-5 py-2.5 bg-slate-950/40 border-t border-slate-800/80 flex gap-2 overflow-x-auto">
          {sampleQuestions.map((q, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(q)}
              className="text-[11px] px-2.5 py-1 rounded-full bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700/60 whitespace-nowrap transition-colors"
            >
              {q}
            </button>
          ))}
        </div>

        {/* Input Bar */}
        <div className="p-4 border-t border-slate-800/80 bg-slate-900/90 flex items-center gap-3">
          <input
            type="text"
            placeholder="Ask anything about orders, shipments, overdue accounts, or policies..."
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleSend();
            }}
            className="flex-1 bg-slate-800/80 border border-slate-700/60 rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-500 outline-none focus:border-blue-500 transition-colors"
          />
          <button
            onClick={() => handleSend()}
            disabled={!inputQuery.trim() || loading}
            className="p-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-medium shadow-md shadow-blue-600/30 transition-all disabled:opacity-50 active:scale-95"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Right Column: Evidence & Verification Drawer */}
      <div className="w-96 bg-slate-900/80 border border-slate-800/80 rounded-2xl flex flex-col overflow-hidden shadow-sm">
        <div className="p-4 border-b border-slate-800/80 flex items-center justify-between bg-slate-950/50">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">Auditable Evidence</h3>
          </div>
          <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-semibold">
            READ-ONLY AST
          </span>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs">
          {activeEvidence ? (
            <>
              {/* Safe SQL Executed */}
              <div className="space-y-2">
                <div className="flex items-center gap-1.5 text-slate-400 font-semibold">
                  <Code className="w-3.5 h-3.5 text-blue-400" />
                  <span>Validated Safe SQL ({activeEvidence.sql_queries?.length || 0})</span>
                </div>
                {activeEvidence.sql_queries?.map((sql: any, i: number) => {
                  const sqlText = typeof sql === 'string' ? sql : (sql?.sql || JSON.stringify(sql));
                  const explanation = typeof sql === 'object' && sql?.explanation ? sql.explanation : null;
                  return (
                    <div key={i} className="space-y-1">
                      <pre className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-[11px] font-mono text-cyan-300 overflow-x-auto whitespace-pre-wrap leading-relaxed">
                        {sqlText}
                      </pre>
                      {explanation && (
                        <p className="text-[11px] text-slate-400 italic px-1">{String(explanation)}</p>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Policy Document Citations */}
              <div className="space-y-2">
                <div className="flex items-center gap-1.5 text-slate-400 font-semibold">
                  <FileText className="w-3.5 h-3.5 text-amber-400" />
                  <span>Policy Citations ({activeEvidence.policy_citations?.length || 0})</span>
                </div>
                {activeEvidence.policy_citations?.map((cit: any, i: number) => {
                  const citText = typeof cit === 'string' ? cit : (cit?.citation || cit?.text || JSON.stringify(cit));
                  return (
                    <div key={i} className="p-2.5 rounded-lg bg-slate-800/40 border border-slate-700/50 text-[11px] text-slate-300 whitespace-pre-line">
                      {citText}
                    </div>
                  );
                })}
              </div>

              {/* Data Sources Used */}
              <div className="space-y-1.5">
                <span className="text-slate-400 font-semibold block">Data Tables Consulted</span>
                <div className="flex flex-wrap gap-1.5">
                  {activeEvidence.data_used?.map((tbl: any, i: number) => (
                    <span key={i} className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono text-[10px] border border-slate-700">
                      {typeof tbl === 'string' ? tbl : (tbl?.table_name || JSON.stringify(tbl))}
                    </span>
                  ))}
                </div>
              </div>

              {/* Recommended Actions */}
              {activeEvidence.recommended_actions && activeEvidence.recommended_actions.length > 0 && (
                <div className="space-y-2 pt-2 border-t border-slate-800">
                  <span className="text-slate-400 font-semibold block">Recommended Action Items</span>
                  {activeEvidence.recommended_actions.map((act: any, i: number) => (
                    <div key={i} className="p-2.5 rounded-lg bg-blue-950/30 border border-blue-800/40 space-y-1">
                      <span className="font-semibold text-blue-300 text-xs">{typeof act === 'string' ? act : (act?.title || JSON.stringify(act))}</span>
                      {act?.reason && <p className="text-[11px] text-slate-400">{String(act.reason)}</p>}
                    </div>
                  ))}
                </div>
              )}
            </>
          ) : (
            <div className="py-20 text-center text-slate-500 space-y-2">
              <Info className="w-6 h-6 mx-auto text-slate-600" />
              <p className="text-xs">Ask a question to inspect verifiable SQL, AST audit tokens, and document citations.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
