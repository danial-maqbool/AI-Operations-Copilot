import React, { useEffect, useState } from 'react';
import {
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  AlertOctagon,
  Clock,
  ArrowUpRight,
  ArrowDownRight,
  ShieldCheck,
  Zap,
  ArrowRight
} from 'lucide-react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid
} from 'recharts';
import { api } from '../services/api';
import { MetricSnapshot, ExceptionItem, ActionItem } from '../types';

interface DashboardViewProps {
  onNavigate: (tab: string) => void;
  onSelectCustomer: (customerId: string) => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({ onNavigate, onSelectCustomer }) => {
  const [kpis, setKpis] = useState<MetricSnapshot[]>([]);
  const [exceptions, setExceptions] = useState<ExceptionItem[]>([]);
  const [actions, setActions] = useState<ActionItem[]>([]);
  const [slaMonitor, setSlaMonitor] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [kpiRes, excRes, actRes, slaRes] = await Promise.all([
        api.getMetrics(),
        api.getExceptions(),
        api.getActions('PROPOSED'),
        api.getSLAMonitor()
      ]);
      setKpis(kpiRes);
      setExceptions(excRes);
      setActions(actRes);
      setSlaMonitor(slaRes);
    } catch (err) {
      console.error('Error loading dashboard data', err);
    } finally {
      setLoading(false);
    }
  };

  const handleApproveAction = async (id: string) => {
    try {
      await api.approveAction(id);
      loadData();
    } catch (err) {
      alert('Failed to approve action: ' + err);
    }
  };

  // Mock weekly revenue trend for main chart
  const trendData = [
    { name: 'Mon', revenue: 42000, orders: 120, delays: 4 },
    { name: 'Tue', revenue: 48000, orders: 145, delays: 3 },
    { name: 'Wed', revenue: 55000, orders: 160, delays: 5 },
    { name: 'Thu', revenue: 61000, orders: 180, delays: 8 },
    { name: 'Fri', revenue: 58000, orders: 172, delays: 6 },
    { name: 'Sat', revenue: 38000, orders: 95, delays: 2 },
    { name: 'Sun', revenue: 32000, orders: 80, delays: 1 }
  ];

  return (
    <div className="space-y-6 pb-12">
      {/* Top Operations KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpis.slice(0, 4).map((kpi) => {
          const isGood = kpi.status === 'GOOD';
          const isCritical = kpi.status === 'CRITICAL';
          return (
            <div
              key={kpi.id}
              className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800/80 hover:border-slate-700/80 transition-all shadow-sm space-y-3"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">{kpi.name}</span>
                <span
                  className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                    isCritical
                      ? 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                      : isGood
                      ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                      : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                  }`}
                >
                  {kpi.status}
                </span>
              </div>

              <div className="flex items-baseline justify-between">
                <div className="text-2xl font-bold text-white tracking-tight">
                  {kpi.code === 'REV' || kpi.code === 'OVERDUE_INV' ? '$' : ''}
                  {kpi.current_value.toLocaleString()}
                  {kpi.code === 'LATE_RATE' || kpi.code === 'SLA_BREACH_RATE' ? '%' : ''}
                </div>
                <div
                  className={`flex items-center text-xs font-semibold ${
                    kpi.pct_change >= 0 ? 'text-emerald-400' : 'text-rose-400'
                  }`}
                >
                  {kpi.pct_change >= 0 ? <ArrowUpRight className="w-3.5 h-3.5" /> : <ArrowDownRight className="w-3.5 h-3.5" />}
                  <span>{Math.abs(kpi.pct_change)}%</span>
                </div>
              </div>

              {/* Sparkline mini chart */}
              <div className="h-10 w-full pt-1">
                {kpi.sparkline && kpi.sparkline.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={kpi.sparkline}>
                      <Area
                        type="monotone"
                        dataKey="value"
                        stroke={isCritical ? '#f43f5e' : '#3b82f6'}
                        fill={isCritical ? '#f43f5e20' : '#3b82f620'}
                        strokeWidth={2}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-full flex items-center text-[10px] text-slate-500">Tracking daily baseline</div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* SLA Risk Monitor & Operational Trends Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Operational Trend Chart */}
        <div className="lg:col-span-2 p-6 rounded-2xl bg-slate-900/80 border border-slate-800/80 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-white tracking-wide">Weekly Operations Throughput</h3>
              <p className="text-xs text-slate-400">Order revenue volume vs logistics fulfillment delay incidents</p>
            </div>
            <div className="flex items-center gap-4 text-xs">
              <div className="flex items-center gap-1.5 text-blue-400 font-medium">
                <div className="w-2.5 h-2.5 rounded-full bg-blue-500" />
                <span>Revenue ($)</span>
              </div>
              <div className="flex items-center gap-1.5 text-rose-400 font-medium">
                <div className="w-2.5 h-2.5 rounded-full bg-rose-500" />
                <span>Delayed Orders</span>
              </div>
            </div>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trendData}>
                <defs>
                  <linearGradient id="colorRev" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="name" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                  itemStyle={{ fontSize: '12px' }}
                />
                <Area type="monotone" dataKey="revenue" stroke="#3b82f6" strokeWidth={2} fillOpacity={1} fill="url(#colorRev)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Global SLA Risk Summary Widget */}
        <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800/80 flex flex-col justify-between space-y-4">
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-bold text-white tracking-wide">Global SLA Risk Monitor</h3>
              <span className="text-[10px] font-semibold text-cyan-400 bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/30">
                ACTIVE
              </span>
            </div>
            <p className="text-xs text-slate-400">Monitoring real-time order delivery, AR aging, and support queues.</p>
          </div>

          <div className="space-y-3">
            <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <AlertOctagon className="w-5 h-5 text-rose-400" />
                <div>
                  <div className="text-sm font-bold text-white">{slaMonitor?.summary?.breached_count || 0} Breaches</div>
                  <span className="text-[11px] text-rose-300">Past contract deadline</span>
                </div>
              </div>
              <span className="text-xs font-bold text-rose-400">CRITICAL</span>
            </div>

            <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Clock className="w-5 h-5 text-amber-400" />
                <div>
                  <div className="text-sm font-bold text-white">{slaMonitor?.summary?.at_risk_count || 0} At Risk</div>
                  <span className="text-[11px] text-amber-300">Due within 24-48 hours</span>
                </div>
              </div>
              <span className="text-xs font-bold text-amber-400">WARNING</span>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-800/40 border border-slate-700/50 flex items-center justify-between">
              <div>
                <span className="text-xs text-slate-400">Total SLA Financial Exposure</span>
                <div className="text-lg font-bold text-white mt-0.5">
                  ${slaMonitor?.summary?.financial_exposure?.toLocaleString() || '0'}
                </div>
              </div>
              <button
                onClick={() => onNavigate('exceptions')}
                className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1 font-semibold"
              >
                <span>View SLA</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Two Column Section: Priority Exceptions & Today's Action Plan */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Priority Operational Exceptions */}
        <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800/80 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-400" />
              <h3 className="text-sm font-bold text-white">Active Operational Exceptions</h3>
            </div>
            <button
              onClick={() => onNavigate('exceptions')}
              className="text-xs text-blue-400 hover:text-blue-300 font-medium"
            >
              View all ({exceptions.length})
            </button>
          </div>

          <div className="space-y-2.5">
            {exceptions.slice(0, 4).map((exc) => (
              <div
                key={exc.id}
                className="p-3.5 rounded-xl bg-slate-800/40 hover:bg-slate-800/70 border border-slate-700/40 transition-colors flex items-center justify-between"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                        exc.severity === 'CRITICAL'
                          ? 'bg-rose-500/20 text-rose-400'
                          : 'bg-amber-500/20 text-amber-400'
                      }`}
                    >
                      {exc.severity}
                    </span>
                    <span className="text-xs font-semibold text-slate-200">{exc.title}</span>
                  </div>
                  <p className="text-[11px] text-slate-400">
                    Impact: <span className="text-slate-300 font-medium">${exc.financial_impact.toLocaleString()}</span> • Age: {exc.age_days}d • Score: {exc.priority_score}
                  </p>
                </div>
                {exc.entity_type === 'customer' || exc.entity_type === 'invoice' ? (
                  <button
                    onClick={() => onSelectCustomer(exc.entity_id)}
                    className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-cyan-400 text-xs font-medium border border-slate-700"
                  >
                    Drill 360
                  </button>
                ) : null}
              </div>
            ))}
            {exceptions.length === 0 && (
              <div className="py-8 text-center text-xs text-slate-500">No active exceptions detected.</div>
            )}
          </div>
        </div>

        {/* Action Center / Approval Gate Summary */}
        <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800/80 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <h3 className="text-sm font-bold text-white">Action Center — Awaiting Approval</h3>
            </div>
            <button
              onClick={() => onNavigate('actions')}
              className="text-xs text-blue-400 hover:text-blue-300 font-medium"
            >
              Action Center ({actions.length})
            </button>
          </div>

          <div className="space-y-2.5">
            {actions.slice(0, 4).map((act) => (
              <div
                key={act.id}
                className="p-3.5 rounded-xl bg-slate-800/40 hover:bg-slate-800/70 border border-slate-700/40 transition-colors flex items-center justify-between"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-400">
                      {act.priority}
                    </span>
                    <span className="text-xs font-semibold text-slate-200">{act.title}</span>
                  </div>
                  <p className="text-[11px] text-slate-400">
                    Owner: <span className="text-slate-300 font-medium">{act.owner}</span> • Type: {act.action_type}
                  </p>
                </div>
                <button
                  onClick={() => handleApproveAction(act.id)}
                  className="px-3 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold transition-all shadow-sm"
                >
                  Approve
                </button>
              </div>
            ))}
            {actions.length === 0 && (
              <div className="py-8 text-center text-xs text-slate-500">All proposed operational actions approved.</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
