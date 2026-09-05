import React, { useEffect, useState } from 'react';
import { CheckSquare, ShieldCheck, Mail, FileDown, PhoneCall, ListTodo, CheckCircle2, XCircle, Play, AlertTriangle } from 'lucide-react';
import { api } from '../services/api';
import { ActionItem } from '../types';

export const ActionCenterView: React.FC = () => {
  const [actions, setActions] = useState<ActionItem[]>([]);
  const [selectedFilter, setSelectedFilter] = useState<string>('ALL');
  const [rejectingActionId, setRejectingActionId] = useState<string | null>(null);
  const [rejectionReason, setRejectionReason] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadActions();
  }, []);

  const loadActions = async () => {
    setLoading(true);
    try {
      const res = await api.getActions();
      setActions(res);
    } catch (err) {
      console.error('Error loading actions', err);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (id: string) => {
    try {
      await api.approveAction(id);
      loadActions();
    } catch (err) {
      alert('Approval failed: ' + err);
    }
  };

  const handleReject = async (id: string) => {
    if (!rejectionReason.trim()) {
      alert('Please provide a reason for rejecting this action.');
      return;
    }
    try {
      await api.rejectAction(id, rejectionReason);
      setRejectingActionId(null);
      setRejectionReason('');
      loadActions();
    } catch (err) {
      alert('Rejection failed: ' + err);
    }
  };

  const handleExecute = async (id: string) => {
    try {
      await api.executeAction(id);
      loadActions();
    } catch (err) {
      alert('Execution failed: ' + err);
    }
  };

  const filtered = actions.filter((a) => {
    if (selectedFilter !== 'ALL' && a.status !== selectedFilter) return false;
    return true;
  });

  const getActionIcon = (type: string) => {
    switch (type) {
      case 'draft_email':
        return <Mail className="w-4 h-4 text-blue-400" />;
      case 'export_csv':
        return <FileDown className="w-4 h-4 text-emerald-400" />;
      case 'call_list':
        return <PhoneCall className="w-4 h-4 text-amber-400" />;
      default:
        return <ListTodo className="w-4 h-4 text-indigo-400" />;
    }
  };

  return (
    <div className="space-y-6 pb-12">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-white tracking-wide">Action Center & Human Approval Gate</h2>
          <p className="text-xs text-slate-400">
            Strict human-in-the-loop verification. No destructive business operations occur without explicit leadership approval.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {['ALL', 'PROPOSED', 'APPROVED', 'COMPLETED', 'REJECTED'].map((st) => (
            <button
              key={st}
              onClick={() => setSelectedFilter(st)}
              className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
                selectedFilter === st
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'bg-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      {/* Action Items List */}
      <div className="space-y-4">
        {filtered.map((act) => (
          <div
            key={act.id}
            className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4 shadow-sm"
          >
            <div className="flex items-start justify-between">
              <div className="flex items-start gap-3">
                <div className="p-2.5 rounded-xl bg-slate-800 border border-slate-700/60 mt-0.5">
                  {getActionIcon(act.action_type)}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                        act.priority === 'CRITICAL'
                          ? 'bg-rose-500/20 text-rose-400'
                          : 'bg-amber-500/20 text-amber-400'
                      }`}
                    >
                      {act.priority}
                    </span>
                    <h3 className="text-sm font-bold text-white">{act.title}</h3>
                    <span className="text-[10px] font-mono text-slate-500">#{act.id.slice(0, 8)}</span>
                  </div>
                  <p className="text-xs text-slate-400 mt-1">{act.description}</p>
                  <p className="text-[11px] text-cyan-400 mt-0.5">
                    <b>Rationale:</b> {act.reason}
                  </p>
                </div>
              </div>

              {/* Status Badge */}
              <span
                className={`text-xs font-bold px-2.5 py-1 rounded-full border ${
                  act.status === 'COMPLETED'
                    ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                    : act.status === 'APPROVED'
                    ? 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30'
                    : act.status === 'REJECTED'
                    ? 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                    : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                }`}
              >
                {act.status}
              </span>
            </div>

            {/* Suggested Steps Checklist */}
            {act.suggested_steps?.length > 0 && (
              <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-1.5">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">Suggested Execution Steps</span>
                <ul className="space-y-1">
                  {act.suggested_steps.map((step, sIdx) => (
                    <li key={sIdx} className="text-xs text-slate-300 flex items-center gap-2">
                      <div className="w-1.5 h-1.5 rounded-full bg-blue-400" />
                      <span>{step}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Rejection Form Drawer */}
            {rejectingActionId === act.id && (
              <div className="p-4 rounded-xl bg-rose-950/20 border border-rose-800/40 space-y-3">
                <label className="text-xs font-semibold text-rose-300 block">
                  Provide reason for rejection (Audit required):
                </label>
                <textarea
                  rows={2}
                  value={rejectionReason}
                  onChange={(e) => setRejectionReason(e.target.value)}
                  placeholder="e.g. Carrier verified delivery is already rescheduled; payment in transit..."
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-xs text-white outline-none"
                />
                <div className="flex justify-end gap-2">
                  <button
                    onClick={() => setRejectingActionId(null)}
                    className="px-3 py-1 rounded bg-slate-800 text-xs text-slate-300 hover:text-white"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={() => handleReject(act.id)}
                    className="px-3 py-1 rounded bg-rose-600 hover:bg-rose-500 text-xs text-white font-semibold"
                  >
                    Confirm Rejection
                  </button>
                </div>
              </div>
            )}

            {/* Execution Result Drawer if Completed */}
            {act.status === 'COMPLETED' && act.execution_result && (
              <div className="p-3.5 rounded-xl bg-emerald-950/20 border border-emerald-800/40 space-y-2 text-xs">
                <div className="flex items-center gap-2 text-emerald-400 font-semibold">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Executed Safely: {act.execution_result.message || 'Execution complete'}</span>
                </div>
                {act.execution_result.download_url && (
                  <a
                    href={act.execution_result.download_url}
                    className="text-xs text-blue-400 hover:underline font-semibold block"
                  >
                    📥 Download Exported CSV ({act.execution_result.file_name})
                  </a>
                )}
                {act.execution_result.body && (
                  <pre className="p-2.5 rounded bg-slate-950 text-slate-300 font-sans text-[11px] whitespace-pre-wrap">
                    {act.execution_result.body}
                  </pre>
                )}
              </div>
            )}

            {/* Action Bar Footer */}
            <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
              <div>
                <span>Owner: <b className="text-slate-300 font-medium">{act.owner}</b></span>
                {act.approved_by && (
                  <span className="ml-3 text-cyan-400">Approved by: {act.approved_by}</span>
                )}
              </div>

              {/* Action Controls */}
              <div className="flex items-center gap-2">
                {act.status === 'PROPOSED' && (
                  <>
                    <button
                      onClick={() => setRejectingActionId(act.id)}
                      className="px-3 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-rose-400 text-xs font-semibold border border-slate-700"
                    >
                      Reject
                    </button>
                    <button
                      onClick={() => handleApprove(act.id)}
                      className="px-4 py-1 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-sm"
                    >
                      Approve Action
                    </button>
                  </>
                )}

                {act.status === 'APPROVED' && (
                  <button
                    onClick={() => handleExecute(act.id)}
                    className="flex items-center gap-1.5 px-4 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-sm"
                  >
                    <Play className="w-3.5 h-3.5" />
                    <span>Execute Safely ({act.action_type.replace('_', ' ')})</span>
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
        {filtered.length === 0 && (
          <div className="py-16 text-center text-xs text-slate-500">
            No action items match the selected status filter.
          </div>
        )}
      </div>
    </div>
  );
};
