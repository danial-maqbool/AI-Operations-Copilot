import React, { useEffect, useState } from 'react';
import { FileText, Search, BookOpen, ExternalLink, Bookmark, CheckCircle2 } from 'lucide-react';
import { api } from '../services/api';
import { DocumentItem, SearchCitation } from '../types';

export const KnowledgeBaseView: React.FC = () => {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchCitation[]>([]);
  const [searching, setSearching] = useState(false);

  useEffect(() => {
    loadDocs();
  }, []);

  const loadDocs = async () => {
    try {
      const res = await api.getDocuments();
      setDocuments(res);
    } catch (err) {
      console.error('Error loading documents', err);
    }
  };

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!searchQuery.trim()) return;
    setSearching(true);
    try {
      const res = await api.searchDocuments(searchQuery);
      setSearchResults(res);
    } catch (err) {
      console.error('Search failed', err);
    } finally {
      setSearching(false);
    }
  };

  return (
    <div className="space-y-6 pb-12">
      <div>
        <h2 className="text-lg font-bold text-white tracking-wide">Document Knowledge Base & Policy RAG</h2>
        <p className="text-xs text-slate-400">
          Search internal operational guidelines, standard operating procedures, and customer SLAs with verifiable page citations
        </p>
      </div>

      {/* Semantic Search Box */}
      <form onSubmit={handleSearch} className="flex gap-3">
        <div className="flex-1 relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-4 top-3.5" />
          <input
            type="text"
            placeholder="Search operational policies (e.g. 'refund approval threshold', 'credit hold rules', 'SLA targets')..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-900 border border-slate-700/80 rounded-xl pl-11 pr-4 py-2.5 text-sm text-white placeholder-slate-500 outline-none focus:border-blue-500"
          />
        </div>
        <button
          type="submit"
          disabled={searching}
          className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-md shadow-blue-600/30 transition-all disabled:opacity-50"
        >
          {searching ? 'Searching...' : 'Search Policies'}
        </button>
      </form>

      {/* Search Results Section */}
      {searchResults.length > 0 && (
        <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
              Retrieved Policy Citations ({searchResults.length})
            </h3>
            <span className="text-[11px] text-cyan-400 font-mono">TF-IDF Vector Relevance</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {searchResults.map((res, idx) => (
              <div
                key={idx}
                className="p-4 rounded-xl bg-slate-800/50 border border-slate-700/60 space-y-2 text-xs hover:border-slate-600 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Bookmark className="w-4 h-4 text-amber-400" />
                    <span className="font-semibold text-white truncate max-w-xs">{res.filename}</span>
                  </div>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-800">
                    Page {res.page_number}
                  </span>
                </div>

                <div className="text-[11px] text-cyan-300 font-semibold">{res.section_title}</div>

                <p className="text-slate-300 text-[11px] leading-relaxed whitespace-pre-line bg-slate-950/60 p-3 rounded-lg border border-slate-800 font-sans">
                  {res.content}
                </p>

                <div className="pt-2 border-t border-slate-700/40 text-[10px] text-slate-500 font-mono">
                  Relevance Score: {(res.score * 100).toFixed(1)}%
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Indexed Document Library */}
      <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
          Indexed Operational Documents ({documents.length})
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {documents.map((doc) => (
            <div
              key={doc.id}
              className="p-4 rounded-xl bg-slate-800/40 border border-slate-700/60 hover:border-slate-600 space-y-3 transition-colors"
            >
              <div className="flex items-start justify-between">
                <div className="p-2 rounded-lg bg-blue-500/10 text-blue-400 border border-blue-500/20">
                  <FileText className="w-5 h-5" />
                </div>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  {doc.status}
                </span>
              </div>

              <div>
                <h4 className="text-xs font-bold text-white truncate">{doc.filename}</h4>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  {doc.total_chunks} chunks • {doc.total_pages} page(s)
                </p>
              </div>

              <div className="text-[10px] text-slate-500 pt-2 border-t border-slate-700/40 font-mono">
                Indexed: {new Date(doc.uploaded_at).toLocaleDateString()}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
