import React from 'react';
import { Sparkles, Sun, Search, Database, RefreshCw } from 'lucide-react';

interface HeaderProps {
  workspaceName?: string;
  dataHealthScore?: number;
  onRunMorningReview: () => void;
  onLoadDemo: () => void;
  onOpenCommandPalette: () => void;
  isLoadingDemo?: boolean;
  isRunningReview?: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  workspaceName = 'Acme Industrial Supplies',
  dataHealthScore = 91.6,
  onRunMorningReview,
  onLoadDemo,
  onOpenCommandPalette,
  isLoadingDemo = false,
  isRunningReview = false
}) => {
  return (
    <header className="h-16 bg-slate-900/80 border-b border-slate-800/80 fixed top-0 right-0 left-64 z-20 px-6 flex items-center justify-between backdrop-blur-md">
      {/* Workspace Indicator & Search */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <div className="w-2.5 h-2.5 rounded-full bg-blue-500" />
          <h1 className="text-sm font-semibold text-white tracking-wide">{workspaceName}</h1>
        </div>

        <button
          onClick={onOpenCommandPalette}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-800 text-slate-400 hover:text-slate-200 text-xs border border-slate-700/60 transition-colors"
        >
          <Search className="w-3.5 h-3.5" />
          <span>Quick actions or questions...</span>
          <kbd className="px-1.5 py-0.5 rounded bg-slate-900 text-[10px] text-slate-400 border border-slate-700 font-mono">
            ⌘K
          </kbd>
        </button>
      </div>

      {/* Action Buttons */}
      <div className="flex items-center gap-3">
        {/* Data Health Score */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/50 border border-slate-700/50">
          <span className="text-xs text-slate-400">Data Health:</span>
          <span className={`text-xs font-bold ${
            dataHealthScore >= 80 ? 'text-emerald-400' : dataHealthScore >= 60 ? 'text-amber-400' : 'text-rose-400'
          }`}>
            {dataHealthScore}%
          </span>
        </div>

        {/* Load Demo Company Button */}
        <button
          onClick={onLoadDemo}
          disabled={isLoadingDemo}
          className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition-all disabled:opacity-50"
        >
          {isLoadingDemo ? (
            <RefreshCw className="w-3.5 h-3.5 animate-spin text-blue-400" />
          ) : (
            <Database className="w-3.5 h-3.5 text-cyan-400" />
          )}
          <span>{isLoadingDemo ? 'Seeding Data...' : 'Reload Demo Data'}</span>
        </button>

        {/* Morning Operations Review Button */}
        <button
          onClick={onRunMorningReview}
          disabled={isRunningReview}
          className="flex items-center gap-2 px-4 py-1.5 rounded-lg bg-gradient-to-r from-amber-500 via-orange-500 to-rose-500 hover:from-amber-600 hover:via-orange-600 hover:to-rose-600 text-white text-xs font-semibold shadow-md shadow-orange-500/20 transition-all active:scale-95 disabled:opacity-60"
        >
          {isRunningReview ? (
            <RefreshCw className="w-3.5 h-3.5 animate-spin text-white" />
          ) : (
            <Sun className="w-3.5 h-3.5 text-white" />
          )}
          <span>{isRunningReview ? 'Running Audit...' : 'Morning Operations Review'}</span>
        </button>
      </div>
    </header>
  );
};
