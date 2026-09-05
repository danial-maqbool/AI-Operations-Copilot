import React, { useEffect, useState } from 'react';
import { Download, FileSpreadsheet, FileCode, FileText, Plus, RefreshCw, CheckCircle2 } from 'lucide-react';
import { api } from '../services/api';

export const ReportsView: React.FC = () => {
  const [reports, setReports] = useState<any[]>([]);
  const [title, setTitle] = useState('Executive Operations Report');
  const [period, setPeriod] = useState('Weekly');
  const [reportType, setReportType] = useState('EXECUTIVE');
  const [generating, setGenerating] = useState(false);
  const [activeReport, setActiveReport] = useState<any>(null);

  useEffect(() => {
    loadReports();
  }, []);

  const loadReports = async () => {
    try {
      const res = await api.getReports();
      setReports(res);
      if (res.length > 0 && !activeReport) {
        setActiveReport(res[0]);
      }
    } catch (err) {
      console.error('Error loading reports', err);
    }
  };

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setGenerating(true);
    try {
      const res = await api.generateReport({
        title,
        period,
        report_type: reportType
      });
      setActiveReport(res);
      loadReports();
    } catch (err) {
      alert('Report generation failed: ' + err);
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="space-y-6 pb-12">
      <div>
        <h2 className="text-lg font-bold text-white tracking-wide">Executive Operations Reports & Exports</h2>
        <p className="text-xs text-slate-400">
          Generate comprehensive operational audits in multi-tab styled Excel (.xlsx), CSV, and structured JSON formats
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Generate Report Form */}
        <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4 shadow-sm">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">Generate New Report</h3>

          <form onSubmit={handleGenerate} className="space-y-3">
            <div>
              <label className="text-xs text-slate-400 block mb-1">Report Title</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white outline-none focus:border-blue-500"
              />
            </div>

            <div>
              <label className="text-xs text-slate-400 block mb-1">Reporting Period</label>
              <select
                value={period}
                onChange={(e) => setPeriod(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white outline-none"
              >
                <option value="Daily">Daily</option>
                <option value="Weekly">Weekly</option>
                <option value="Monthly">Monthly</option>
                <option value="Quarterly">Quarterly</option>
              </select>
            </div>

            <div>
              <label className="text-xs text-slate-400 block mb-1">Report Focus</label>
              <select
                value={reportType}
                onChange={(e) => setReportType(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white outline-none"
              >
                <option value="EXECUTIVE">Executive Operations</option>
                <option value="FINANCIAL">Financial & AR Aging</option>
                <option value="FULFILLMENT">Fulfillment & Logistics</option>
                <option value="INVENTORY">Inventory & Safety Stock</option>
              </select>
            </div>

            <button
              type="submit"
              disabled={generating}
              className="w-full py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-md shadow-blue-600/30 flex items-center justify-center gap-2 transition-all disabled:opacity-50"
            >
              {generating ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
              <span>{generating ? 'Compiling Multi-Tab Report...' : 'Generate Executive Report'}</span>
            </button>
          </form>

          {/* Historical Reports List */}
          <div className="pt-4 border-t border-slate-800 space-y-2">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 block">Previously Generated</span>
            <div className="space-y-1.5 max-h-60 overflow-y-auto">
              {reports.map((r) => (
                <button
                  key={r.id}
                  onClick={() => setActiveReport(r)}
                  className={`w-full text-left p-2.5 rounded-lg text-xs transition-colors flex items-center justify-between ${
                    activeReport?.id === r.id
                      ? 'bg-blue-600/20 border border-blue-500 text-white'
                      : 'hover:bg-slate-800 text-slate-400'
                  }`}
                >
                  <span className="truncate max-w-[180px] font-medium">{r.title}</span>
                  <span className="text-[10px] text-slate-500 font-mono">{r.period}</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Report Preview & Download Center */}
        <div className="lg:col-span-2 p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-6">
          {activeReport ? (
            <>
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-base font-bold text-white">{activeReport.title}</h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Period: {activeReport.period} • Generated: {new Date(activeReport.created_at).toLocaleString()}
                  </p>
                </div>
                <span className="text-xs px-2.5 py-1 rounded bg-blue-500/10 text-blue-400 font-semibold border border-blue-500/20">
                  {activeReport.report_type}
                </span>
              </div>

              {/* Download Buttons Bar */}
              <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center justify-between">
                <span className="text-xs text-slate-300 font-semibold">Available Export Formats:</span>
                <div className="flex items-center gap-2">
                  <a
                    href={activeReport.download_urls?.xlsx}
                    download
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-400 border border-emerald-500/30 text-xs font-semibold transition-colors"
                  >
                    <FileSpreadsheet className="w-3.5 h-3.5" />
                    <span>Download Excel (.xlsx)</span>
                  </a>
                  <a
                    href={activeReport.download_urls?.csv}
                    download
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold transition-colors"
                  >
                    <FileText className="w-3.5 h-3.5 text-cyan-400" />
                    <span>CSV</span>
                  </a>
                  <a
                    href={activeReport.download_urls?.json}
                    download
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold transition-colors"
                  >
                    <FileCode className="w-3.5 h-3.5 text-amber-400" />
                    <span>JSON</span>
                  </a>
                </div>
              </div>

              {/* Summary Stats Inside Active Report */}
              <div className="grid grid-cols-3 gap-4">
                <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-700/60">
                  <span className="text-xs text-slate-400">KPIs Audited</span>
                  <div className="text-xl font-bold text-white mt-1">
                    {activeReport.sections?.kpis?.length || 0} Metrics
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-700/60">
                  <span className="text-xs text-slate-400">Exceptions Captured</span>
                  <div className="text-xl font-bold text-rose-400 mt-1">
                    {activeReport.sections?.exceptions?.length || 0} Open Items
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-700/60">
                  <span className="text-xs text-slate-400">Action Plan</span>
                  <div className="text-xl font-bold text-cyan-400 mt-1">
                    {activeReport.sections?.actions?.length || 0} Actions
                  </div>
                </div>
              </div>

              {/* Multi-Tab Description Card */}
              <div className="p-4 rounded-xl bg-slate-800/30 border border-slate-700/40 space-y-2 text-xs text-slate-400">
                <span className="font-semibold text-slate-300 block">Excel (.xlsx) Workbook Tabs Included:</span>
                <div className="grid grid-cols-2 gap-2 text-[11px]">
                  <div>• <b>Tab 1:</b> Executive Summary</div>
                  <div>• <b>Tab 2:</b> Key Performance Indicators</div>
                  <div>• <b>Tab 3:</b> Operational Exceptions</div>
                  <div>• <b>Tab 4:</b> Priority Action Items</div>
                  <div>• <b>Tab 5:</b> SLA Risk & Exposure</div>
                </div>
              </div>
            </>
          ) : (
            <div className="py-24 text-center text-xs text-slate-500">
              Generate a report or select a previous report to download exports.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
