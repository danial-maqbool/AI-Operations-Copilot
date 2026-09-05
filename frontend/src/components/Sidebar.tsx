import React from 'react';
import {
  LayoutDashboard,
  Bot,
  Database,
  BookOpen,
  BarChart3,
  AlertTriangle,
  CheckSquare,
  Workflow,
  FileText,
  Download,
  ShieldCheck,
  Activity
} from 'lucide-react';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  openExceptionsCount?: number;
  proposedActionsCount?: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  setActiveTab,
  openExceptionsCount = 0,
  proposedActionsCount = 0
}) => {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'copilot', label: 'Operations Copilot', icon: Bot, badge: 'AI' },
    { id: 'data-sources', label: 'Data Warehouse', icon: Database },
    { id: 'catalog', label: 'Semantic Catalog', icon: BookOpen },
    { id: 'metrics', label: 'KPIs & Metrics', icon: BarChart3 },
    {
      id: 'exceptions',
      label: 'Exceptions & SLA',
      icon: AlertTriangle,
      count: openExceptionsCount,
      countColor: 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
    },
    {
      id: 'actions',
      label: 'Action Center',
      icon: CheckSquare,
      count: proposedActionsCount,
      countColor: 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
    },
    { id: 'workflows', label: 'Workflow Studio', icon: Workflow },
    { id: 'knowledge', label: 'Knowledge Base', icon: FileText },
    { id: 'reports', label: 'Reports & Exports', icon: Download },
    { id: 'audit', label: 'Audit & Safety', icon: ShieldCheck }
  ];

  return (
    <aside className="w-64 bg-slate-900/90 border-r border-slate-800/80 flex flex-col h-screen fixed left-0 top-0 z-30 backdrop-blur-md">
      {/* Brand Header */}
      <div className="h-16 flex items-center justify-between px-5 border-b border-slate-800/80">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-cyan-600 via-blue-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-blue-500/20 ring-1 ring-white/20">
            <Activity className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-bold tracking-tight text-white text-base">OpsPilot</span>
              <span className="text-[10px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-400 border border-blue-500/30">
                PRO
              </span>
            </div>
            <span className="text-[11px] text-slate-400">AI Operations Intelligence</span>
          </div>
        </div>
      </div>

      {/* Navigation Links */}
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
        <div className="text-[10px] uppercase font-bold tracking-wider text-slate-500 px-3 pb-1">
          Operations Platform
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-all group ${
                isActive
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-600/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <div className="flex items-center gap-3">
                <Icon className={`w-4 h-4 transition-transform ${isActive ? 'scale-110' : 'group-hover:scale-105'}`} />
                <span>{item.label}</span>
              </div>
              <div className="flex items-center gap-1.5">
                {item.badge && (
                  <span className={`text-[10px] font-bold px-1.5 py-0.2 rounded ${
                    isActive ? 'bg-white/20 text-white' : 'bg-blue-500/10 text-blue-400'
                  }`}>
                    {item.badge}
                  </span>
                )}
                {typeof item.count === 'number' && item.count > 0 && (
                  <span className={`text-[11px] font-bold px-2 py-0.5 rounded-full ${item.countColor}`}>
                    {item.count}
                  </span>
                )}
              </div>
            </button>
          );
        })}
      </div>

      {/* Live System Status Pill */}
      <div className="p-4 border-t border-slate-800/80 bg-slate-950/40">
        <div className="flex items-center justify-between text-xs text-slate-400">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="font-medium text-slate-300">Live Warehouse</span>
          </div>
          <span className="text-[10px] text-slate-500 font-mono">AST Protected</span>
        </div>
      </div>
    </aside>
  );
};
