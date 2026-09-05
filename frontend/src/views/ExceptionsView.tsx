import React, { useEffect, useState } from 'react';
import { AlertTriangle, AlertOctagon, CheckCircle2, Filter, DollarSign, Clock, ShieldAlert } from 'lucide-react';
import { api } from '../services/api';
import { ExceptionItem } from '../types';

interface ExceptionsViewProps {
  onSelectCustomer: (customerId: string) => void;
}

export const ExceptionsView: React.FC<ExceptionsViewProps> = ({ onSelectCustomer }) => {
  const [exceptions, setExceptions] = useState<ExceptionItem[]>([]);
  const [slaMonitor, setSlaMonitor] = useState<any>(null);
  const [selectedSeverity, setSelectedSeverity] = useState<string>('ALL');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [excRes, slaRes] = await Promise.all([
        api.getExceptions(),
        api.getSLAMonitor()
      ]);
      setExceptions(excRes);
      setSlaMonitor(slaRes);
    } catch (err) {
      console.error('Error loading exceptions', err);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateStatus = async (id: string, newStatus: string) => {
    try {
      await api.updateExceptionStatus(id, newStatus);
      loadData();
    } catch (err) {
      alert('Failed to update status: ' + err);
    }
  };

  const filtered = exceptions.filter((e) => {
    if (selectedSeverity !== 'ALL' && e.severity !== selectedSeverity) return false;
    return true;
  });

  return (
    <div className="space-y-6 pb-12">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-white tracking-wide">Operational Exceptions & SLA Monitor</h2>
          <p className="text-xs text-slate-400">Prioritized business rule violations, stockouts, overdue AR, and SLA breach trackers</p>
        </div>

        {/* Severity Filters */}
        <div className="flex items-center gap-2">
          {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((sev) => (
            <button
              key={sev}
              onClick={() => setSelectedSeverity(sev)}
              className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
                selectedSeverity === sev
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'bg-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              {sev}
            </button>
          ))}
        </div>
      </div>

      {/* SLA Risk Stats Header */}
      {slaMonitor && (
        <div className="grid grid-cols-4 gap-4">
          <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
            <span className="text-xs text-slate-400">Entities Monitored</span>
            <div className="text-2xl font-bold text-white mt-1">{slaMonitor.summary.total_monitored}</div>
            <span className="text-[11px] text-slate-500">Orders, Invoices, Tickets</span>
          </div>

          <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20">
            <span className="text-xs text-rose-300">SLA Breached</span>
            <div className="text-2xl font-bold text-rose-400 mt-1">{slaMonitor.summary.breached_count}</div>
            <span className="text-[11px] text-rose-400/80">Immediate resolution required</span>
          </div>

          <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20">
            <span className="text-xs text-amber-300">Approaching Breach</span>
            <div className="text-2xl font-bold text-amber-400 mt-1">{slaMonitor.summary.at_risk_count}</div>
            <span className="text-[11px] text-amber-400/80">Due in under 48 hours</span>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
            <span className="text-xs text-slate-400">Total Financial Exposure</span>
            <div className="text-2xl font-bold text-white mt-1">
              ${slaMonitor.summary.financial_exposure?.toLocaleString()}
            </div>
            <span className="text-[11px] text-slate-500">Across breached accounts</span>
          </div>
        </div>
      )}

      {/* Exceptions List */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/80 overflow-hidden shadow-sm">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
            Prioritized Operational Exceptions ({filtered.length})
          </h3>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead className="bg-slate-950 text-slate-400">
              <tr>
                <th className="p-3">Severity</th>
                <th className="p-3">Exception Title</th>
                <th className="p-3">Entity Type</th>
                <th className="p-3">Financial Impact</th>
                <th className="p-3 text-center">Age</th>
                <th className="p-3 text-center">Score</th>
                <th className="p-3">Status</th>
                <th className="p-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {filtered.map((exc) => (
                <tr key={exc.id} className="hover:bg-slate-800/40 text-slate-300 transition-colors">
                  <td className="p-3">
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                        exc.severity === 'CRITICAL'
                          ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                          : exc.severity === 'HIGH'
                          ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                          : 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                      }`}
                    >
                      {exc.severity}
                    </span>
                  </td>
                  <td className="p-3">
                    <div className="font-semibold text-white">{exc.title}</div>
                    <div className="text-[11px] text-slate-400">{exc.description}</div>
                  </td>
                  <td className="p-3 font-mono text-cyan-300 text-[11px]">
                    {exc.entity_type} #{exc.entity_id}
                  </td>
                  <td className="p-3 font-medium text-slate-200">
                    {exc.financial_impact > 0 ? `$${exc.financial_impact.toLocaleString()}` : '—'}
                  </td>
                  <td className="p-3 text-center font-mono text-slate-400">{exc.age_days}d</td>
                  <td className="p-3 text-center">
                    <span className="font-bold text-amber-400">{exc.priority_score}</span>
                  </td>
                  <td className="p-3">
                    <span className={`text-[10px] font-semibold px-2 py-0.5 rounded ${
                      exc.status === 'OPEN' ? 'bg-rose-500/10 text-rose-400' : 'bg-emerald-500/10 text-emerald-400'
                    }`}>
                      {exc.status}
                    </span>
                  </td>
                  <td className="p-3 text-right">
                    <div className="flex items-center justify-end gap-1.5">
                      {exc.entity_id && (
                        <button
                          onClick={() => onSelectCustomer(exc.entity_id)}
                          className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-cyan-400 text-[11px] font-medium"
                        >
                          360
                        </button>
                      )}
                      {exc.status === 'OPEN' && (
                        <button
                          onClick={() => handleUpdateStatus(exc.id, 'RESOLVED')}
                          className="px-2 py-1 rounded bg-emerald-600 hover:bg-emerald-500 text-white text-[11px] font-medium"
                        >
                          Resolve
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-slate-500">
                    No exceptions found for the selected filter.
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
