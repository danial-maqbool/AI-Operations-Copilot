import React, { useState, useEffect } from 'react';
import { Search, Bot, BarChart3, AlertTriangle, CheckSquare, Sun, Database, ArrowRight, X } from 'lucide-react';

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  onNavigate: (tab: string) => void;
  onAskCopilot: (question: string) => void;
  onRunMorningReview: () => void;
}

export const CommandPalette: React.FC<CommandPaletteProps> = ({
  isOpen,
  onClose,
  onNavigate,
  onAskCopilot,
  onRunMorningReview
}) => {
  const [query, setQuery] = useState('');

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        onClose(); // toggle
      }
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const quickLinks = [
    { label: 'Run Morning Operations Review', icon: Sun, action: () => { onRunMorningReview(); onClose(); } },
    { label: 'Go to Action Center & Approvals', icon: CheckSquare, action: () => { onNavigate('actions'); onClose(); } },
    { label: 'View Operational Exceptions & SLA', icon: AlertTriangle, action: () => { onNavigate('exceptions'); onClose(); } },
    { label: 'Inspect Semantic Data Catalog', icon: Database, action: () => { onNavigate('catalog'); onClose(); } },
    { label: 'Operations KPI & Metrics Dashboard', icon: BarChart3, action: () => { onNavigate('metrics'); onClose(); } }
  ];

  const suggestedQuestions = [
    'Which orders are delayed and what are the carrier causes?',
    'Which customers have overdue invoices exceeding $5,000?',
    'What is our policy for refund approvals under $5,000?',
    'Which products are below safety stock?',
    'Which support tickets have breached SLA?'
  ];

  const handleAsk = (q: string) => {
    onAskCopilot(q);
    onNavigate('copilot');
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-24 p-4 bg-black/75 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl w-full max-w-2xl shadow-2xl overflow-hidden">
        {/* Search Input */}
        <div className="p-4 border-b border-slate-800 flex items-center gap-3">
          <Search className="w-5 h-5 text-slate-400" />
          <input
            type="text"
            placeholder="Type a command or ask Copilot anything..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && query.trim()) {
                handleAsk(query.trim());
              }
            }}
            autoFocus
            className="flex-1 bg-transparent text-white text-sm outline-none placeholder-slate-500"
          />
          <button onClick={onClose} className="p-1 rounded text-slate-400 hover:text-white">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Command Body */}
        <div className="p-3 max-h-96 overflow-y-auto space-y-4">
          {query.trim() && (
            <button
              onClick={() => handleAsk(query.trim())}
              className="w-full flex items-center justify-between p-2.5 rounded-lg bg-blue-600/20 hover:bg-blue-600/30 text-blue-300 text-xs font-semibold border border-blue-500/30"
            >
              <div className="flex items-center gap-2">
                <Bot className="w-4 h-4 text-blue-400" />
                <span>Ask Copilot: "{query}"</span>
              </div>
              <ArrowRight className="w-4 h-4" />
            </button>
          )}

          {/* Quick Actions */}
          <div className="space-y-1">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 px-2">Navigation & Commands</span>
            {quickLinks.map((link, idx) => {
              const Icon = link.icon;
              return (
                <button
                  key={idx}
                  onClick={link.action}
                  className="w-full flex items-center justify-between p-2 rounded-lg hover:bg-slate-800/80 text-slate-300 text-xs transition-colors"
                >
                  <div className="flex items-center gap-2.5">
                    <Icon className="w-4 h-4 text-slate-400" />
                    <span>{link.label}</span>
                  </div>
                  <kbd className="text-[10px] text-slate-500 font-mono">↵</kbd>
                </button>
              );
            })}
          </div>

          {/* Suggested Operational Questions */}
          <div className="space-y-1 pt-1 border-t border-slate-800/80">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 px-2">Suggested Copilot Questions</span>
            {suggestedQuestions.map((q, idx) => (
              <button
                key={idx}
                onClick={() => handleAsk(q)}
                className="w-full text-left p-2 rounded-lg hover:bg-slate-800/80 text-slate-400 hover:text-slate-200 text-xs transition-colors truncate"
              >
                💬 {q}
              </button>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="px-4 py-2 border-t border-slate-800 bg-slate-950 flex items-center justify-between text-[11px] text-slate-500 font-mono">
          <span>Navigation: ↑↓ • Select: ↵</span>
          <span>Close: ESC</span>
        </div>
      </div>
    </div>
  );
};
