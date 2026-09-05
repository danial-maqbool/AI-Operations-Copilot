import React, { useEffect, useState } from 'react';
import { Workflow as WorkflowIcon, Play, Clock, CheckCircle2, AlertCircle, RefreshCw, ChevronRight } from 'lucide-react';
import { api } from '../services/api';
import { Workflow, WorkflowRun } from '../types';

export const WorkflowView: React.FC = () => {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [runningId, setRunningId] = useState<string | null>(null);
  const [activeRun, setActiveRun] = useState<WorkflowRun | null>(null);

  useEffect(() => {
    loadWorkflows();
  }, []);

  const loadWorkflows = async () => {
    try {
      const res = await api.getWorkflows();
      setWorkflows(res);
    } catch (err) {
      console.error('Error loading workflows', err);
    }
  };

  const handleRunWorkflow = async (id: string) => {
    setRunningId(id);
    try {
      const run = await api.runWorkflow(id);
      setActiveRun(run);
      loadWorkflows();
    } catch (err) {
      alert('Workflow execution failed: ' + err);
    } finally {
      setRunningId(null);
    }
  };

  return (
    <div className="space-y-6 pb-12">
      <div>
        <h2 className="text-lg font-bold text-white tracking-wide">Workflow Studio & Automation Runs</h2>
        <p className="text-xs text-slate-400">
          Orchestrated operational routines combining data sync, rule evaluations, outlier detection, and action formulation
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Workflows List */}
        <div className="lg:col-span-2 space-y-4">
          {workflows.map((wf) => (
            <div
              key={wf.id}
              className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4 shadow-sm"
            >
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-bold text-white">{wf.name}</h3>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-cyan-400 border border-slate-700">
                      {wf.trigger_type}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 mt-1">{wf.description}</p>
                </div>
                <button
                  onClick={() => handleRunWorkflow(wf.id)}
                  disabled={runningId === wf.id}
                  className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-md shadow-blue-600/30 disabled:opacity-50"
                >
                  {runningId === wf.id ? (
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <Play className="w-3.5 h-3.5" />
                  )}
                  <span>{runningId === wf.id ? 'Running...' : 'Run Workflow'}</span>
                </button>
              </div>

              {/* Step Sequence Badges */}
              <div className="space-y-1.5 pt-1">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Step Sequence</span>
                <div className="flex flex-wrap gap-2">
                  {wf.steps?.map((step: any, sIdx: number) => (
                    <div
                      key={sIdx}
                      className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-800/80 border border-slate-700/60 text-xs text-slate-300"
                    >
                      <span className="w-4 h-4 rounded-full bg-slate-700 flex items-center justify-center text-[10px] font-bold text-slate-400">
                        {sIdx + 1}
                      </span>
                      <span>{step.name}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Recent Runs Count */}
              <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-500">
                <span>Total Runs: {wf.runs?.length || 0}</span>
                {wf.runs && wf.runs.length > 0 && (
                  <button
                    onClick={() => setActiveRun(wf.runs[wf.runs.length - 1])}
                    className="text-cyan-400 hover:underline"
                  >
                    View Latest Run Logs
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Workflow Execution Log Drawer */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">Run Execution Log</h3>
            {activeRun && (
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                activeRun.status === 'COMPLETED' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'
              }`}>
                {activeRun.status}
              </span>
            )}
          </div>

          {activeRun ? (
            <div className="space-y-3">
              <div className="text-xs text-slate-400">
                Started: <span className="text-slate-300">{new Date(activeRun.started_at).toLocaleTimeString()}</span> • Records: {activeRun.records_processed}
              </div>

              <div className="space-y-2">
                {activeRun.execution_log?.map((log: any, idx: number) => (
                  <div key={idx} className="p-3 rounded-lg bg-slate-800/50 border border-slate-700/50 space-y-1 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-white">{log.step}</span>
                      <span className="text-[10px] text-emerald-400 font-mono">{log.status}</span>
                    </div>
                    {log.detail && <p className="text-[11px] text-slate-400">{log.detail}</p>}
                    {log.duration_ms !== undefined && (
                      <span className="text-[10px] text-slate-500 font-mono block">{log.duration_ms}ms</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="py-20 text-center text-xs text-slate-500">
              Run a workflow or select a historical run to view detailed step traces.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
