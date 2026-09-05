import React, { useEffect, useState } from 'react';
import { BookOpen, Key, Shield, Tag, Edit3, Check, X, AlertCircle } from 'lucide-react';
import { api } from '../services/api';
import { TableProfile, ColumnProfile } from '../types';

export const CatalogView: React.FC = () => {
  const [tables, setTables] = useState<TableProfile[]>([]);
  const [selectedTable, setSelectedTable] = useState<TableProfile | null>(null);
  const [editingColumnId, setEditingColumnId] = useState<string | null>(null);
  const [editRole, setEditRole] = useState('');
  const [editDesc, setEditDesc] = useState('');

  useEffect(() => {
    loadCatalog();
  }, []);

  const loadCatalog = async () => {
    try {
      const res = await api.getCatalogTables();
      setTables(res);
      if (res.length > 0) {
        setSelectedTable(res[0]);
      }
    } catch (err) {
      console.error('Error loading catalog', err);
    }
  };

  const handleStartEdit = (col: ColumnProfile) => {
    setEditingColumnId(col.id);
    setEditRole(col.user_role_override || col.inferred_role);
    setEditDesc(col.user_description_override || col.inferred_description || '');
  };

  const handleSaveEdit = async (colId: string) => {
    try {
      await api.updateColumnOverride(colId, {
        user_role_override: editRole,
        user_description_override: editDesc
      });
      setEditingColumnId(null);
      loadCatalog();
    } catch (err) {
      alert('Failed to save override: ' + err);
    }
  };

  return (
    <div className="space-y-6 pb-12">
      <div>
        <h2 className="text-lg font-bold text-white tracking-wide">Semantic Data Catalog</h2>
        <p className="text-xs text-slate-400">Classified business roles, entity heuristics, and verified column semantics</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Tables Navigation Sidebar */}
        <div className="space-y-2">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 px-1">Discovered Tables</span>
          <div className="space-y-1">
            {tables.map((t) => (
              <button
                key={t.id}
                onClick={() => setSelectedTable(t)}
                className={`w-full text-left p-3 rounded-xl border transition-all flex items-center justify-between ${
                  selectedTable?.id === t.id
                    ? 'bg-blue-600/20 border-blue-500 text-white shadow-sm'
                    : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                }`}
              >
                <div>
                  <div className="text-xs font-bold font-mono text-slate-200">{t.table_name}</div>
                  <span className="text-[10px] text-slate-500">{t.detected_entity}</span>
                </div>
                <span className="text-[11px] font-mono text-slate-500">{t.columns?.length || 0} cols</span>
              </button>
            ))}
          </div>
        </div>

        {/* Selected Table Semantic Profile */}
        <div className="lg:col-span-3 space-y-4">
          {selectedTable ? (
            <>
              {/* Entity Overview Card */}
              <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 flex items-center justify-between">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-bold text-white font-mono">{selectedTable.table_name}</span>
                    <span className="text-xs px-2 py-0.5 rounded bg-blue-500/20 text-blue-400 font-semibold border border-blue-500/30">
                      {selectedTable.detected_entity}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400">
                    {selectedTable.row_count?.toLocaleString()} rows • {selectedTable.column_count} columns • {selectedTable.missing_cells_total} missing cells
                  </p>
                </div>
                <div className="text-right">
                  <span className="text-xs text-slate-400">Health Score</span>
                  <div className="text-xl font-bold text-emerald-400">{selectedTable.data_health_score}%</div>
                </div>
              </div>

              {/* Columns Table */}
              <div className="rounded-2xl border border-slate-800 bg-slate-900/80 overflow-hidden">
                <div className="p-4 border-b border-slate-800">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">Column Semantics & Classification</h3>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-slate-950 text-slate-400">
                      <tr>
                        <th className="p-3">Column Name</th>
                        <th className="p-3">Data Type</th>
                        <th className="p-3">Semantic Role</th>
                        <th className="p-3">Description</th>
                        <th className="p-3 text-center">Uniqueness</th>
                        <th className="p-3 text-center">Nulls</th>
                        <th className="p-3 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800">
                      {selectedTable.columns?.map((col) => {
                        const isEditing = editingColumnId === col.id;
                        return (
                          <tr key={col.id} className="hover:bg-slate-800/40 text-slate-300">
                            <td className="p-3 font-mono font-semibold text-cyan-300">
                              <div className="flex items-center gap-1.5">
                                {col.is_primary_key && <Key className="w-3.5 h-3.5 text-amber-400" />}
                                {col.is_sensitive && <Shield className="w-3.5 h-3.5 text-rose-400" />}
                                <span>{col.column_name}</span>
                              </div>
                            </td>
                            <td className="p-3 font-mono text-slate-400 text-[11px]">{col.data_type}</td>
                            <td className="p-3">
                              {isEditing ? (
                                <select
                                  value={editRole}
                                  onChange={(e) => setEditRole(e.target.value)}
                                  className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-xs text-white"
                                >
                                  <option value="identifier">identifier</option>
                                  <option value="business_date">business_date</option>
                                  <option value="category">category</option>
                                  <option value="metric">metric</option>
                                  <option value="status">status</option>
                                  <option value="sensitive">sensitive</option>
                                </select>
                              ) : (
                                <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono text-[10px] border border-slate-700">
                                  {col.user_role_override || col.inferred_role}
                                </span>
                              )}
                            </td>
                            <td className="p-3 max-w-xs truncate text-[11px]">
                              {isEditing ? (
                                <input
                                  type="text"
                                  value={editDesc}
                                  onChange={(e) => setEditDesc(e.target.value)}
                                  className="w-full bg-slate-800 border border-slate-700 rounded px-2 py-1 text-xs text-white"
                                />
                              ) : (
                                <span className="text-slate-400">{col.user_description_override || col.inferred_description || 'N/A'}</span>
                              )}
                            </td>
                            <td className="p-3 text-center font-mono text-[11px] text-slate-400">
                              {col.unique_count}
                            </td>
                            <td className="p-3 text-center font-mono text-[11px]">
                              <span className={col.null_percentage > 0 ? 'text-amber-400 font-semibold' : 'text-slate-500'}>
                                {col.null_percentage}%
                              </span>
                            </td>
                            <td className="p-3 text-right">
                              {isEditing ? (
                                <div className="flex items-center justify-end gap-1">
                                  <button
                                    onClick={() => handleSaveEdit(col.id)}
                                    className="p-1 rounded bg-emerald-600 text-white hover:bg-emerald-500"
                                  >
                                    <Check className="w-3.5 h-3.5" />
                                  </button>
                                  <button
                                    onClick={() => setEditingColumnId(null)}
                                    className="p-1 rounded bg-slate-800 text-slate-400 hover:text-white"
                                  >
                                    <X className="w-3.5 h-3.5" />
                                  </button>
                                </div>
                              ) : (
                                <button
                                  onClick={() => handleStartEdit(col)}
                                  className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-cyan-400 transition-colors"
                                >
                                  <Edit3 className="w-3.5 h-3.5" />
                                </button>
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          ) : (
            <div className="py-16 text-center text-xs text-slate-500">Select a table to view semantic catalog details.</div>
          )}
        </div>
      </div>
    </div>
  );
};
