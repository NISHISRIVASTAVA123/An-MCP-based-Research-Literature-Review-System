import React, { useState } from 'react';
import { ResearchRequest, SearchStrategy, StrategyQuery } from '../types';
import {
  Sparkles,
  Play,
  Edit2,
  Check,
  Plus,
  Trash2,
  Database,
  Tag,
  ArrowRight,
  Sliders,
} from 'lucide-react';

interface StrategyEditorProps {
  request: ResearchRequest;
  strategy: SearchStrategy;
  onExecuteSearch: (updatedQueries?: StrategyQuery[]) => void;
  onSaveStrategy: (updatedQueries: StrategyQuery[]) => void;
  isExecuting: boolean;
  onBack: () => void;
}

export const StrategyEditor: React.FC<StrategyEditorProps> = ({
  request,
  strategy,
  onExecuteSearch,
  onSaveStrategy,
  isExecuting,
  onBack,
}) => {
  const [queries, setQueries] = useState<StrategyQuery[]>(strategy.queries);
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [tempQueryText, setTempQueryText] = useState('');

  const handleToggleQuery = (index: number) => {
    const updated = [...queries];
    updated[index].is_enabled = !updated[index].is_enabled;
    setQueries(updated);
  };

  const handleStartEdit = (index: number) => {
    setEditingIndex(index);
    setTempQueryText(queries[index].query_text);
  };

  const handleSaveEdit = (index: number) => {
    const updated = [...queries];
    updated[index].query_text = tempQueryText.trim();
    setQueries(updated);
    setEditingIndex(null);
  };

  const handleAddQuery = () => {
    const newQ: StrategyQuery = {
      target_database: 'openalex',
      query_text: `"${request.topic}"`,
      is_enabled: true,
      order_index: queries.length,
    };
    setQueries([...queries, newQ]);
    setEditingIndex(queries.length);
    setTempQueryText(newQ.query_text);
  };

  const handleDeleteQuery = (index: number) => {
    setQueries(queries.filter((_, i) => i !== index));
  };

  const handleExecute = () => {
    onSaveStrategy(queries);
    onExecuteSearch(queries);
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Top Banner */}
      <div className="academic-card p-6 bg-gradient-to-r from-slate-900 to-indigo-950 text-white">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-indigo-300 text-xs font-semibold uppercase tracking-wider mb-1">
              <Sparkles className="h-3.5 w-3.5" />
              <span>Generated Academic Strategy</span>
            </div>
            <h2 className="text-xl font-bold font-serif">{request.topic}</h2>
            <p className="text-xs text-slate-300 mt-1 max-w-2xl line-clamp-2">
              {request.objective}
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={onBack}
              className="px-3 py-2 text-xs font-medium rounded-md bg-slate-800 text-slate-300 hover:bg-slate-700 transition-colors"
            >
              Edit Scope
            </button>
            <button
              onClick={handleExecute}
              disabled={isExecuting}
              className="btn-primary text-xs py-2 px-4 bg-indigo-500 hover:bg-indigo-600 shadow-md font-semibold flex items-center gap-1.5"
            >
              <Play className="h-3.5 w-3.5 fill-current" />
              <span>{isExecuting ? 'Retrieving Literature...' : 'Start Literature Search'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Concepts & Keywords Decomposition */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="academic-card p-5">
          <div className="flex items-center gap-2 mb-3">
            <Tag className="h-4 w-4 text-indigo-600" />
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-800">
              Extracted Concepts
            </h3>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {strategy.concepts.map((c, i) => (
              <span key={i} className="badge bg-slate-100 text-slate-700 border border-slate-200">
                {c}
              </span>
            ))}
          </div>
        </div>

        <div className="academic-card p-5">
          <div className="flex items-center gap-2 mb-3">
            <Tag className="h-4 w-4 text-emerald-600" />
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-800">
              Keywords & Synonyms
            </h3>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {strategy.keywords.slice(0, 10).map((k, i) => (
              <span key={i} className="badge bg-emerald-50 text-emerald-800 border border-emerald-200">
                {k}
              </span>
            ))}
          </div>
        </div>

        <div className="academic-card p-5">
          <div className="flex items-center gap-2 mb-3">
            <Sliders className="h-4 w-4 text-amber-600" />
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-800">
              Review Parameters
            </h3>
          </div>
          <ul className="text-xs text-slate-600 space-y-1.5">
            <li><strong>Timeframe:</strong> {request.start_year} – {request.end_year}</li>
            <li><strong>Max Papers:</strong> {request.max_papers}</li>
            <li><strong>Citation Style:</strong> {request.citation_style}</li>
            <li><strong>Domain:</strong> {request.domain}</li>
          </ul>
        </div>
      </div>

      {/* Database-Specific Executable Queries Table */}
      <div className="academic-card p-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mb-4">
          <div>
            <div className="flex items-center gap-2">
              <Database className="h-4 w-4 text-indigo-600" />
              <h3 className="text-sm font-bold uppercase tracking-wider text-slate-900">
                Database-Specific Search Queries
              </h3>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Queries are tailored for each database's syntax. Inspect, edit, or toggle before starting retrieval.
            </p>
          </div>

          <button
            onClick={handleAddQuery}
            className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 flex items-center gap-1 border border-indigo-200 rounded-md px-2.5 py-1.5 bg-indigo-50/50"
          >
            <Plus className="h-3.5 w-3.5" />
            <span>Add Custom Query</span>
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-100 text-slate-700 font-semibold uppercase tracking-wider border-b border-slate-200">
              <tr>
                <th className="py-2.5 px-3 w-16 text-center">Active</th>
                <th className="py-2.5 px-3 w-36">Database</th>
                <th className="py-2.5 px-3">Formatted Query Syntax</th>
                <th className="py-2.5 px-3 w-28 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {queries.map((q, idx) => (
                <tr key={idx} className={q.is_enabled ? 'hover:bg-slate-50/80' : 'bg-slate-50 opacity-60'}>
                  <td className="py-3 px-3 text-center">
                    <input
                      type="checkbox"
                      checked={q.is_enabled}
                      onChange={() => handleToggleQuery(idx)}
                      className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 h-4 w-4"
                    />
                  </td>
                  <td className="py-3 px-3 font-semibold">
                    <span className={`badge badge-${q.target_database}`}>
                      {q.target_database}
                    </span>
                  </td>
                  <td className="py-3 px-3">
                    {editingIndex === idx ? (
                      <div className="flex items-center gap-2">
                        <input
                          type="text"
                          className="input-base text-xs font-mono py-1"
                          value={tempQueryText}
                          onChange={(e) => setTempQueryText(e.target.value)}
                        />
                        <button
                          onClick={() => handleSaveEdit(idx)}
                          className="p-1.5 bg-emerald-600 text-white rounded hover:bg-emerald-700"
                        >
                          <Check className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    ) : (
                      <code className="text-[11px] font-mono bg-slate-100 text-slate-800 px-2 py-1 rounded block max-w-2xl break-all">
                        {q.query_text}
                      </code>
                    )}
                  </td>
                  <td className="py-3 px-3 text-right">
                    <div className="flex items-center justify-end gap-1.5">
                      <button
                        onClick={() => handleStartEdit(idx)}
                        className="p-1.5 text-slate-500 hover:text-slate-800 rounded hover:bg-slate-100"
                        title="Edit query syntax"
                      >
                        <Edit2 className="h-3.5 w-3.5" />
                      </button>
                      <button
                        onClick={() => handleDeleteQuery(idx)}
                        className="p-1.5 text-slate-400 hover:text-red-600 rounded hover:bg-slate-100"
                        title="Delete query"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Bottom Execute CTA */}
        <div className="mt-6 pt-4 border-t border-slate-200 flex items-center justify-between">
          <p className="text-xs text-slate-500">
            {queries.filter((q) => q.is_enabled).length} of {queries.length} queries active across selected providers.
          </p>
          <button
            onClick={handleExecute}
            disabled={isExecuting || queries.filter((q) => q.is_enabled).length === 0}
            className="btn-primary text-xs py-2.5 px-6 shadow-sm font-semibold flex items-center gap-2"
          >
            <Play className="h-3.5 w-3.5 fill-current" />
            <span>{isExecuting ? 'Retrieving Literature...' : 'Start Literature Search'}</span>
          </button>
        </div>
      </div>
    </div>
  );
};

