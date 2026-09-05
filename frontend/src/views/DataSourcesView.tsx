import React, { useEffect, useState } from 'react';
import { Database, FileSpreadsheet, RefreshCw, Eye, CheckCircle2, ShieldCheck, ArrowRight } from 'lucide-react';
import { api } from '../services/api';

export const DataSourcesView: React.FC = () => {
  const [sources, setSources] = useState<any[]>([]);
  const [tables, setTables] = useState<any[]>([]);
  const [selectedTable, setSelectedTable] = useState<string | null>(null);
  const [tablePreview, setTablePreview] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [srcRes, tblRes] = await Promise.all([
        api.getDataSources(),
        api.getCatalogTables()
      ]);
      setSources(srcRes);
      setTables(tblRes);
      if (tblRes.length > 0 && !selectedTable) {
        handlePreview(tblRes[0].table_name);
      }
    } catch (err) {
      console.error('Error loading data sources', err);
    } finally {
      setLoading(false);
    }
  };

  const handlePreview = async (tableName: string) => {
    setSelectedTable(tableName);
    try {
      const res = await api.executeSQL(`SELECT * FROM "${tableName}" LIMIT 10`);
      setTablePreview(res);
    } catch (err) {
      console.error('Error previewing table', err);
    }
  };

  return (
    <div className="space-y-6 pb-12">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-white tracking-wide">Connected Operational Sources</h2>
          <p className="text-xs text-slate-400">Multi-source unified SQLite warehouse with automatic schema profiling</p>
        </div>
        <button
          onClick={loadData}
          disabled={loading}
          className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Sources</span>
        </button>
      </div>

      {/* Warehouse Tables Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {tables.map((tbl) => {
          const isSelected = selectedTable === tbl.table_name;
          return (
            <div
              key={tbl.id}
              onClick={() => handlePreview(tbl.table_name)}
              className={`p-4 rounded-xl border transition-all cursor-pointer ${
                isSelected
                  ? 'bg-blue-950/30 border-blue-500/80 shadow-md shadow-blue-500/10'
                  : 'bg-slate-900/80 border-slate-800 hover:border-slate-700'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-2.5">
                  <div className="p-2 rounded-lg bg-slate-800 text-cyan-400">
                    <Database className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-white font-mono">{tbl.table_name}</h3>
                    <span className="text-[11px] text-slate-400">{tbl.detected_entity || 'Operational Entity'}</span>
                  </div>
                </div>
                <span className={`text-[11px] font-bold px-2 py-0.5 rounded ${
                  tbl.data_health_score >= 80 ? 'bg-emerald-500/10 text-emerald-400' : 'bg-amber-500/10 text-amber-400'
                }`}>
                  {tbl.data_health_score}%
                </span>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
                <span>{tbl.row_count?.toLocaleString()} rows</span>
                <span>{tbl.column_count} columns</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Interactive Table Preview */}
      {selectedTable && tablePreview && (
        <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800/80 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Eye className="w-4 h-4 text-cyan-400" />
              <h3 className="text-sm font-bold text-white">
                Live Data Preview: <span className="font-mono text-cyan-400">{selectedTable}</span> (First 10 rows)
              </h3>
            </div>
            <span className="text-xs text-slate-500 font-mono">
              AST Validated • Safe Read-Only Mode
            </span>
          </div>

          <div className="overflow-x-auto rounded-xl border border-slate-800">
            <table className="w-full text-xs text-left">
              <thead className="bg-slate-950 text-slate-400">
                <tr>
                  {tablePreview.columns?.map((col: string, idx: number) => (
                    <th key={idx} className="p-3 font-semibold uppercase tracking-wider text-[10px]">
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {tablePreview.rows?.map((row: any[], rIdx: number) => (
                  <tr key={rIdx} className="hover:bg-slate-800/40 text-slate-300 transition-colors">
                    {row.map((cell, cIdx) => (
                      <td key={cIdx} className="p-3 font-mono text-[11px] whitespace-nowrap">
                        {cell !== null && cell !== undefined ? String(cell) : <span className="text-slate-600">NULL</span>}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
