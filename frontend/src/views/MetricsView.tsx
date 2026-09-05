import React, { useEffect, useState } from 'react';
import { BarChart3, TrendingUp, Play, CheckCircle2, AlertTriangle, ShieldCheck } from 'lucide-react';
import { api } from '../services/api';
import { MetricSnapshot } from '../types';

export const MetricsView: React.FC = () => {
  const [metrics, setMetrics] = useState<any[]>([]);
  const [testTable, setTestTable] = useState('orders');
  const [testFormula, setTestFormula] = useState('COUNT(*)');
  const [testResult, setTestResult] = useState<any>(null);
  const [testing, setTesting] = useState(false);

  useEffect(() => {
    loadMetrics();
  }, []);

  const loadMetrics = async () => {
    try {
      const res = await api.getMetrics();
      setMetrics(res);
    } catch (err) {
      console.error('Error loading metrics', err);
    }
  };

  const handleTestFormula = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const res = await api.testMetricFormula(testTable, testFormula);
      setTestResult(res);
    } catch (err) {
      setTestResult({ success: false, error: String(err) });
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="space-y-6 pb-12">
      <div>
        <h2 className="text-lg font-bold text-white tracking-wide">Operations KPI & Metrics Catalog</h2>
        <p className="text-xs text-slate-400">Standardized KPI definitions, threshold rules, and verified mathematical formulas</p>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {metrics.map((m) => {
          const isGood = m.status === 'GOOD';
          const isCritical = m.status === 'CRITICAL';
          return (
            <div
              key={m.id}
              className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4 shadow-sm"
            >
              <div className="flex items-start justify-between">
                <div>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                    {m.code}
                  </span>
                  <h3 className="text-sm font-bold text-white mt-1.5">{m.name}</h3>
                </div>
                <span
                  className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                    isCritical
                      ? 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                      : isGood
                      ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                      : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                  }`}
                >
                  {m.status}
                </span>
              </div>

              <div className="flex items-baseline justify-between pt-1">
                <div>
                  <span className="text-xs text-slate-400 block">Current Value</span>
                  <div className="text-2xl font-bold text-white mt-0.5">
                    {m.current_value?.toLocaleString()}
                  </div>
                </div>
                <div className="text-right">
                  <span className="text-xs text-slate-400 block">Target</span>
                  <div className="text-sm font-semibold text-slate-300 mt-0.5">
                    {m.target_value !== null ? m.target_value : 'Dynamic'}
                  </div>
                </div>
              </div>

              <div className="p-2.5 rounded-xl bg-slate-950/70 border border-slate-800/80 space-y-1 text-[11px]">
                <div className="text-slate-500">Source: <span className="font-mono text-cyan-400">{m.source_table}</span></div>
                <div className="text-slate-400 font-mono text-[10px] truncate">{m.formula}</div>
              </div>

              <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
                <span>Owner: <b className="text-slate-300 font-medium">{m.owner}</b></span>
                <span className="text-[11px] text-slate-500">{m.comparison_direction?.replace('_', ' ')}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Interactive KPI Formula Tester Card */}
      <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
        <div className="flex items-center gap-2">
          <Play className="w-4 h-4 text-cyan-400" />
          <h3 className="text-sm font-bold text-white">Interactive KPI Formula Sandbox</h3>
        </div>
        <p className="text-xs text-slate-400">
          Safely test SQL aggregation expressions on any warehouse table before registering new operations metrics.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
          <div>
            <label className="text-xs text-slate-400 block mb-1">Target Table</label>
            <input
              type="text"
              value={testTable}
              onChange={(e) => setTestTable(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white outline-none"
            />
          </div>
          <div>
            <label className="text-xs text-slate-400 block mb-1">SQL Expression</label>
            <input
              type="text"
              value={testFormula}
              onChange={(e) => setTestFormula(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs font-mono text-cyan-300 outline-none"
            />
          </div>
          <button
            onClick={handleTestFormula}
            disabled={testing}
            className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-md shadow-blue-600/30"
          >
            {testing ? 'Evaluating...' : 'Run Test'}
          </button>
        </div>

        {testResult && (
          <div className={`p-4 rounded-xl border text-xs ${
            testResult.success ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300' : 'bg-rose-500/10 border-rose-500/30 text-rose-300'
          }`}>
            {testResult.success ? (
              <div className="flex items-center justify-between">
                <span>Evaluated Result: <b className="text-white font-mono text-sm">{String(testResult.sample_result)}</b></span>
                <span className="text-[11px] text-emerald-400">Query AST validated</span>
              </div>
            ) : (
              <div>Error: {testResult.error}</div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
