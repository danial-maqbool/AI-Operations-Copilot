import React, { useEffect, useState } from 'react';
import { ShieldCheck, Lock, EyeOff, Activity, RefreshCw, CheckCircle2, AlertCircle } from 'lucide-react';
import { api } from '../services/api';

export const AuditView: React.FC = () => {
  const [events, setEvents] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [selectedEventType, setSelectedEventType] = useState<string>('ALL');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadAudit();
  }, []);

  const loadAudit = async () => {
    setLoading(true);
    try {
      const [logRes, statRes] = await Promise.all([
        api.getAuditLog(100),
        api.getAuditStats()
      ]);
      setEvents(logRes);
      setStats(statRes);
    } catch (err) {
      console.error('Error loading audit log', err);
    } finally {
      setLoading(false);
    }
  };

  const filtered = events.filter((e) => {
    if (selectedEventType !== 'ALL' && e.event_type !== selectedEventType) return false;
    return true;
  });

  return (
    <div className="space-y-6 pb-12">
      <div>
        <h2 className="text-lg font-bold text-white tracking-wide">Audit Trail, Data Governance & Safety Settings</h2>
        <p className="text-xs text-slate-400">
          Immutable event log of every operational query, proposed workflow action, approval, and execution
        </p>
      </div>

      {/* Safety Mechanisms Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-3">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-white">Safe SQL AST Engine</h3>
              <span className="text-[10px] text-emerald-400 font-semibold">Strict Read-Only Mode</span>
            </div>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            All SQL queries parsed via sqlglot AST. Destructive keywords (DROP, DELETE, UPDATE, INSERT, ALTER) strictly blocked.
          </p>
        </div>

        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-3">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              <EyeOff className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-white">PII Redaction Guard</h3>
              <span className="text-[10px] text-cyan-400 font-semibold">Pre-Prompt Anonymization</span>
            </div>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            Customer emails, phone numbers, and sensitive identifiers are masked before reaching AI models and restored on response.
          </p>
        </div>

        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-3">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20">
              <Lock className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-white">Human Approval Gate</h3>
              <span className="text-[10px] text-amber-400 font-semibold">Execution Isolation</span>
            </div>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            Operational modifications and communications require affirmative human review before execution.
          </p>
        </div>
      </div>

      {/* Audit Stats */}
      {stats && (
        <div className="grid grid-cols-4 gap-4">
          <div className="p-4 rounded-xl bg-slate-800/50 border border-slate-700/60">
            <span className="text-xs text-slate-400">Total Audit Events</span>
            <div className="text-xl font-bold text-white mt-1">{stats.total_audit_events}</div>
          </div>
          <div className="p-4 rounded-xl bg-slate-800/50 border border-slate-700/60">
            <span className="text-xs text-slate-400">Actions Approved</span>
            <div className="text-xl font-bold text-emerald-400 mt-1">{stats.actions_approved}</div>
          </div>
          <div className="p-4 rounded-xl bg-slate-800/50 border border-slate-700/60">
            <span className="text-xs text-slate-400">Workflows Executed</span>
            <div className="text-xl font-bold text-cyan-400 mt-1">{stats.workflows_executed}</div>
          </div>
          <div className="p-4 rounded-xl bg-slate-800/50 border border-slate-700/60">
            <span className="text-xs text-slate-400">Reports Generated</span>
            <div className="text-xl font-bold text-amber-400 mt-1">{stats.reports_generated}</div>
          </div>
        </div>
      )}

      {/* Audit Events Log Table */}
      <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
            Event Log History ({filtered.length})
          </h3>
          <div className="flex items-center gap-2">
            {['ALL', 'action_proposed', 'action_approved', 'action_executed', 'workflow_run', 'report_generated'].map((t) => (
              <button
                key={t}
                onClick={() => setSelectedEventType(t)}
                className={`px-2.5 py-1 rounded text-[11px] font-semibold transition-colors ${
                  selectedEventType === t
                    ? 'bg-blue-600 text-white'
                    : 'bg-slate-800 text-slate-400 hover:text-slate-200'
                }`}
              >
                {t.replace('_', ' ')}
              </button>
            ))}
          </div>
        </div>

        <div className="overflow-x-auto rounded-xl border border-slate-800">
          <table className="w-full text-xs text-left">
            <thead className="bg-slate-950 text-slate-400">
              <tr>
                <th className="p-3">Timestamp</th>
                <th className="p-3">Event Type</th>
                <th className="p-3">User / Actor</th>
                <th className="p-3">Entity Type</th>
                <th className="p-3">Details</th>
                <th className="p-3 text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {filtered.map((e) => (
                <tr key={e.id} className="hover:bg-slate-800/40 text-slate-300 transition-colors">
                  <td className="p-3 font-mono text-slate-400 text-[11px] whitespace-nowrap">
                    {new Date(e.created_at).toLocaleString()}
                  </td>
                  <td className="p-3 font-semibold font-mono text-cyan-400 text-[11px]">
                    {e.event_type}
                  </td>
                  <td className="p-3">{e.user_name}</td>
                  <td className="p-3 font-mono text-slate-400 text-[11px]">{e.entity_type || '—'}</td>
                  <td className="p-3 max-w-sm truncate text-slate-400 text-[11px]">
                    {JSON.stringify(e.details)}
                  </td>
                  <td className="p-3 text-right">
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400">
                      {e.status}
                    </span>
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-500">
                    No audit records match the selected filter.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
