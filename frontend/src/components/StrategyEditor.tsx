import React, { useState } from 'react';
import { ResearchRequest, SearchStrategy, StrategyQuery } from '../types';
import {
  Sparkles, Play, Edit2, Check, Plus, Trash2,
  Database, Tag, Sliders, ArrowLeft, Zap, Info,
} from 'lucide-react';

interface StrategyEditorProps {
  request: ResearchRequest;
  strategy: SearchStrategy;
  onExecuteSearch: (updatedQueries?: StrategyQuery[]) => void;
  onSaveStrategy: (updatedQueries: StrategyQuery[]) => void;
  isExecuting: boolean;
  onBack: () => void;
}

const DB_COLORS: Record<string, { bg: string; color: string; border: string }> = {
  openalex:         { bg: '#e0f2fe', color: '#0369a1', border: '#bae6fd' },
  semantic_scholar: { bg: '#f3e8ff', color: '#6d28d9', border: '#ddd6fe' },
  crossref:         { bg: '#fef3c7', color: '#92400e', border: '#fde68a' },
  arxiv:            { bg: '#fee2e2', color: '#991b1b', border: '#fecaca' },
};

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
  const [tempText, setTempText] = useState('');

  const toggleQuery  = (i: number) => { const q = [...queries]; q[i].is_enabled = !q[i].is_enabled; setQueries(q); };
  const startEdit    = (i: number) => { setEditingIndex(i); setTempText(queries[i].query_text); };
  const saveEdit     = (i: number) => { const q = [...queries]; q[i].query_text = tempText.trim(); setQueries(q); setEditingIndex(null); };
  const deleteQuery  = (i: number) => setQueries(queries.filter((_, idx) => idx !== i));

  const addQuery = () => {
    const nq: StrategyQuery = { target_database: 'openalex', query_text: `"${request.topic}"`, is_enabled: true, order_index: queries.length };
    setQueries([...queries, nq]);
    setEditingIndex(queries.length);
    setTempText(nq.query_text);
  };

  const handleExecute = () => { onSaveStrategy(queries); onExecuteSearch(queries); };
  const activeCount = queries.filter((q) => q.is_enabled).length;

  return (
    <div style={{ maxWidth: 900, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>

      {/* Hero banner */}
      <div className="card-dark" style={{ padding: '1.75rem 2rem' }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'flex-start', justifyContent: 'space-between', gap: '1rem' }}>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
              <div style={{ padding: '0.3rem', borderRadius: '0.4rem', background: 'rgba(129,140,248,.2)' }}>
                <Sparkles size={15} color="#a5b4fc" />
              </div>
              <span style={{ fontSize: '0.68rem', fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase', color: '#a5b4fc' }}>
                Step 2 · AI-Generated Search Strategy
              </span>
            </div>
            <h2 style={{ fontFamily: 'Sora, sans-serif', fontWeight: 800, fontSize: '1.3rem', color: '#fff', marginBottom: '0.4rem' }}>
              {request.topic}
            </h2>
            <p style={{ fontSize: '0.82rem', color: 'rgba(255,255,255,.5)', maxWidth: 540 }} className="line-clamp-2">
              {request.objective}
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', flexShrink: 0 }}>
            <button onClick={onBack} className="btn btn-sm" style={{
              background: 'rgba(255,255,255,.1)', color: 'rgba(255,255,255,.8)',
              border: '1px solid rgba(255,255,255,.15)',
            }}>
              <ArrowLeft size={14} /> Edit Scope
            </button>
            <button onClick={handleExecute} disabled={isExecuting || activeCount === 0} className="btn btn-primary btn-sm" style={{ padding: '0.5rem 1.25rem' }}>
              {isExecuting ? (
                <><div className="spinner" style={{ width: 15, height: 15, borderWidth: 2 }} /><span>Retrieving Literature...</span></>
              ) : (
                <><Play size={14} style={{ fill: 'currentColor' }} /><span>Start Literature Search</span></>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Strategy Overview — 3 cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
        {/* Concepts */}
        <div className="card" style={{ padding: '1.25rem 1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.9rem' }}>
            <Tag size={15} color="#6366f1" />
            <span style={{ fontSize: '0.72rem', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: '#6366f1' }}>Extracted Concepts</span>
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
            {strategy.concepts.map((c, i) => (
              <span key={i} className="badge badge-brand" style={{ fontSize: '0.72rem' }}>{c}</span>
            ))}
          </div>
        </div>

        {/* Keywords */}
        <div className="card" style={{ padding: '1.25rem 1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.9rem' }}>
            <Tag size={15} color="#10b981" />
            <span style={{ fontSize: '0.72rem', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: '#10b981' }}>Keywords & Synonyms</span>
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
            {strategy.keywords.slice(0, 10).map((k, i) => (
              <span key={i} className="badge badge-success" style={{ fontSize: '0.72rem' }}>{k}</span>
            ))}
          </div>
        </div>

        {/* Parameters */}
        <div className="card" style={{ padding: '1.25rem 1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.9rem' }}>
            <Sliders size={15} color="#f59e0b" />
            <span style={{ fontSize: '0.72rem', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: '#f59e0b' }}>Review Parameters</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
            {[
              ['Timeframe', `${request.start_year} – ${request.end_year}`],
              ['Max Papers', String(request.max_papers)],
              ['Citation', request.citation_style],
              ['Domain', request.domain],
            ].map(([k, v]) => (
              <div key={k} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem' }}>
                <span style={{ color: '#94a3b8', fontWeight: 500 }}>{k}</span>
                <span style={{ color: '#1e293b', fontWeight: 600 }}>{v}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Query Table */}
      <div className="card" style={{ padding: '1.5rem 1.75rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.3rem' }}>
              <Database size={16} color="#6366f1" />
              <span style={{ fontWeight: 700, fontSize: '0.95rem', color: '#1e293b' }}>Database-Specific Search Queries</span>
            </div>
            <p style={{ fontSize: '0.78rem', color: '#64748b' }}>
              Queries tailored per database syntax. Toggle, edit, or add before running retrieval.
            </p>
          </div>
          <button onClick={addQuery} className="btn btn-secondary btn-sm">
            <Plus size={14} /> Add Custom Query
          </button>
        </div>

        {/* Info bar */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: '0.5rem',
          padding: '0.65rem 1rem', borderRadius: '0.6rem',
          background: '#eef2ff', marginBottom: '1rem', fontSize: '0.78rem', color: '#4f46e5',
        }}>
          <Info size={14} />
          <span><strong>{activeCount}</strong> of <strong>{queries.length}</strong> queries active · These will execute across selected providers simultaneously.</span>
        </div>

        {/* Table */}
        <div style={{ overflowX: 'auto', borderRadius: '0.65rem', border: '1px solid #e2e8f0' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
            <thead>
              <tr style={{ background: '#f8fafc' }}>
                <th style={{ padding: '0.65rem 0.75rem', textAlign: 'center', fontWeight: 700, fontSize: '0.7rem', letterSpacing: '0.07em', textTransform: 'uppercase', color: '#64748b', width: 60 }}>On</th>
                <th style={{ padding: '0.65rem 0.75rem', fontWeight: 700, fontSize: '0.7rem', letterSpacing: '0.07em', textTransform: 'uppercase', color: '#64748b', width: 150 }}>Database</th>
                <th style={{ padding: '0.65rem 0.75rem', fontWeight: 700, fontSize: '0.7rem', letterSpacing: '0.07em', textTransform: 'uppercase', color: '#64748b' }}>Query Syntax</th>
                <th style={{ padding: '0.65rem 0.75rem', fontWeight: 700, fontSize: '0.7rem', letterSpacing: '0.07em', textTransform: 'uppercase', color: '#64748b', textAlign: 'right', width: 90 }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {queries.map((q, idx) => {
                const dbStyle = DB_COLORS[q.target_database] || { bg: '#f1f5f9', color: '#475569', border: '#e2e8f0' };
                return (
                  <tr key={idx} style={{
                    borderTop: '1px solid #f1f5f9',
                    background: q.is_enabled ? '#fff' : '#fafbfc',
                    opacity: q.is_enabled ? 1 : 0.5,
                    transition: 'all 0.15s',
                  }}>
                    <td style={{ padding: '0.75rem', textAlign: 'center' }}>
                      <input type="checkbox" checked={q.is_enabled} onChange={() => toggleQuery(idx)}
                        style={{ accentColor: '#6366f1', width: 15, height: 15, cursor: 'pointer' }} />
                    </td>
                    <td style={{ padding: '0.75rem' }}>
                      <span style={{
                        display: 'inline-flex', alignItems: 'center',
                        padding: '0.2rem 0.6rem', borderRadius: '100px',
                        fontSize: '0.72rem', fontWeight: 700,
                        background: dbStyle.bg, color: dbStyle.color,
                        border: `1.5px solid ${dbStyle.border}`,
                      }}>
                        {q.target_database}
                      </span>
                    </td>
                    <td style={{ padding: '0.75rem 0.75rem 0.75rem 0' }}>
                      {editingIndex === idx ? (
                        <div style={{ display: 'flex', gap: '0.5rem' }}>
                          <input type="text" className="input" style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '0.78rem', padding: '0.4rem 0.65rem' }}
                            value={tempText} onChange={(e) => setTempText(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && saveEdit(idx)} autoFocus />
                          <button onClick={() => saveEdit(idx)} style={{
                            background: '#10b981', color: '#fff', border: 'none',
                            borderRadius: '0.4rem', padding: '0.4rem 0.65rem', cursor: 'pointer',
                          }}><Check size={14} /></button>
                        </div>
                      ) : (
                        <code style={{
                          display: 'block', background: '#f8fafc', borderRadius: '0.4rem',
                          padding: '0.4rem 0.65rem', fontSize: '0.75rem', color: '#1e293b',
                          fontFamily: 'JetBrains Mono, monospace', wordBreak: 'break-all',
                          border: '1px solid #e2e8f0',
                        }}>{q.query_text}</code>
                      )}
                    </td>
                    <td style={{ padding: '0.75rem', textAlign: 'right' }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '0.25rem' }}>
                        <button onClick={() => startEdit(idx)} className="btn btn-ghost btn-sm" title="Edit query" style={{ padding: '0.35rem' }}>
                          <Edit2 size={13} />
                        </button>
                        <button onClick={() => deleteQuery(idx)} className="btn btn-ghost btn-sm" title="Delete"
                          style={{ padding: '0.35rem', color: '#94a3b8' }}
                          onMouseEnter={(e) => e.currentTarget.style.color = '#f43f5e'}
                          onMouseLeave={(e) => e.currentTarget.style.color = '#94a3b8'}
                        >
                          <Trash2 size={13} />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Bottom CTA */}
        <div style={{
          marginTop: '1.25rem', paddingTop: '1.25rem',
          borderTop: '1px solid #f1f5f9',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        }}>
          <p style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
            All queries run concurrently via async provider pipeline.
          </p>
          <button onClick={handleExecute}
            disabled={isExecuting || activeCount === 0}
            className="btn btn-primary"
            style={{ padding: '0.65rem 1.75rem', fontSize: '0.9rem' }}
          >
            {isExecuting ? (
              <><div className="spinner" style={{ width: 18, height: 18, borderWidth: 2 }} /><span>Retrieving Literature...</span></>
            ) : (
              <><Zap size={16} style={{ fill: 'currentColor' }} /><span>Start Literature Search</span></>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
