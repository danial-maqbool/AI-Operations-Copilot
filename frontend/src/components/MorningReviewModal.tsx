import React from 'react';
import { X, Sun, CheckCircle2, AlertTriangle, AlertOctagon, TrendingUp, ShieldAlert, ArrowRight } from 'lucide-react';
import { MorningReviewData } from '../types';

interface MorningReviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  data: MorningReviewData | null;
  onNavigateToActions: () => void;
}

export const MorningReviewModal: React.FC<MorningReviewModalProps> = ({
  isOpen,
  onClose,
  data,
  onNavigateToActions
}) => {
  if (!isOpen || !data) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl w-full max-w-4xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-gradient-to-r from-amber-500/10 via-orange-500/10 to-slate-900">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-orange-500/20 text-orange-400 border border-orange-500/30">
              <Sun className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold text-white">Daily Morning Operations Review</h2>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                  {data.review_id}
                </span>
              </div>
              <p className="text-xs text-slate-400">{data.timestamp} • Execution time: {data.duration_ms}ms</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Quick Metrics Grid */}
          <div className="grid grid-cols-4 gap-4">
            <div className="p-4 rounded-xl bg-slate-800/60 border border-slate-700/60">
              <span className="text-xs text-slate-400">Data Health</span>
              <div className="text-2xl font-bold text-emerald-400 mt-1">{data.data_health_score}%</div>
              <span className="text-[11px] text-slate-500">Integrity verified</span>
            </div>

            <div className="p-4 rounded-xl bg-slate-800/60 border border-slate-700/60">
              <span className="text-xs text-slate-400">Active Exceptions</span>
              <div className="text-2xl font-bold text-rose-400 mt-1">{data.exceptions_summary.total_open}</div>
              <span className="text-[11px] text-slate-500">
                ${data.exceptions_summary.total_financial_impact.toLocaleString()} total impact
              </span>
            </div>

            <div className="p-4 rounded-xl bg-slate-800/60 border border-slate-700/60">
              <span className="text-xs text-slate-400">SLA Breaches</span>
              <div className="text-2xl font-bold text-amber-400 mt-1">{data.sla_summary.breached_count}</div>
              <span className="text-[11px] text-slate-500">{data.sla_summary.at_risk_count} tickets at risk</span>
            </div>

            <div className="p-4 rounded-xl bg-slate-800/60 border border-slate-700/60">
              <span className="text-xs text-slate-400">KPI Statuses</span>
              <div className="flex items-center gap-2 mt-2">
                <span className="text-xs px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-bold">
                  {data.kpi_summary.counts['GOOD'] || 0} OK
                </span>
                <span className="text-xs px-2 py-0.5 rounded bg-rose-500/20 text-rose-400 font-bold">
                  {data.kpi_summary.counts['CRITICAL'] || 0} Alert
                </span>
              </div>
            </div>
          </div>

          {/* AI Executive Brief */}
          <div className="p-5 rounded-xl bg-slate-950/60 border border-slate-800 space-y-3">
            <div className="flex items-center gap-2 text-xs font-bold text-slate-300 uppercase tracking-wider">
              <TrendingUp className="w-4 h-4 text-cyan-400" />
              Executive Operations Brief
            </div>
            <div className="text-xs text-slate-300 leading-relaxed whitespace-pre-line font-sans prose-invert">
              {data.executive_brief}
            </div>
          </div>

          {/* Today's Prioritized Actions */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs font-bold text-slate-300 uppercase tracking-wider">
                <ShieldAlert className="w-4 h-4 text-amber-400" />
                Today's Action Focus ({data.todays_prioritized_actions.length} Items)
              </div>
              <button
                onClick={() => {
                  onClose();
                  onNavigateToActions();
                }}
                className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1 font-medium"
              >
                <span>Go to Action Center</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>

            <div className="space-y-2">
              {data.todays_prioritized_actions.map((act: any, idx: number) => (
                <div
                  key={idx}
                  className="p-3 rounded-lg bg-slate-800/40 hover:bg-slate-800/70 border border-slate-700/50 flex items-center justify-between transition-colors"
                >
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2">
                      <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                        act.priority === 'CRITICAL'
                          ? 'bg-rose-500/20 text-rose-400'
                          : 'bg-amber-500/20 text-amber-400'
                      }`}>
                        {act.priority}
                      </span>
                      <span className="text-xs font-semibold text-slate-200">{act.title}</span>
                    </div>
                    <p className="text-[11px] text-slate-400">{act.reason}</p>
                  </div>
                  <div className="text-right text-[11px] text-slate-400">
                    <div>Owner: <span className="text-slate-300 font-medium">{act.owner}</span></div>
                    <span className="text-[10px] text-amber-400 font-semibold">{act.status}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-3 border-t border-slate-800 flex items-center justify-between bg-slate-900/60">
          <span className="text-[11px] text-slate-500">OpsPilot AI Engine • Grounded calculations only</span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold"
          >
            Acknowledge & Close
          </button>
        </div>
      </div>
    </div>
  );
};
