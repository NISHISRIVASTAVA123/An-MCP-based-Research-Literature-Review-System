import React, { useState } from 'react';
import { Paper } from '../types';
import { X, ExternalLink, FileText, Database, Code, Check, Copy, BookOpen } from 'lucide-react';

interface PaperModalProps {
  paper: Paper | null;
  onClose: () => void;
}

const DB_COLORS: Record<string, { bg: string; color: string; border: string }> = {
  openalex: { bg: '#e0f2fe', color: '#0369a1', border: '#bae6fd' },
  semantic_scholar: { bg: '#f3e8ff', color: '#6d28d9', border: '#ddd6fe' },
  crossref: { bg: '#fef3c7', color: '#92400e', border: '#fde68a' },
  arxiv: { bg: '#fee2e2', color: '#991b1b', border: '#fecaca' },
};

export const PaperModal: React.FC<PaperModalProps> = ({ paper, onClose }) => {
  if (!paper) return null;

  const [activeTab, setActiveTab] = useState<'metadata' | 'provenance' | 'raw'>('metadata');
  const [copied, setCopied] = useState(false);

  const handleCopyCitation = () => {
    const authorsStr = paper.authors.join(', ');
    const citation = `${authorsStr}. "${paper.title}". ${paper.venue || 'Publication'}, ${paper.publication_year || 'n.d.'}. ${paper.doi ? `DOI: https://doi.org/${paper.doi}` : ''}`;
    navigator.clipboard.writeText(citation);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-panel"
        style={{ maxWidth: 760, width: '100%', display: 'flex', flexDirection: 'column' }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div style={{ padding: '1.5rem 1.75rem', borderBottom: '1px solid #e2e8f0', background: '#f8fafc', display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '1rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.4rem' }}>
              <span className="badge badge-brand" style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '0.68rem' }}>
                ID: {paper.id.slice(0, 16)}...
              </span>
              {paper.is_open_access && (
                <span className="badge badge-success" style={{ fontSize: '0.68rem' }}>
                  Open Access
                </span>
              )}
            </div>
            <h2 style={{ fontFamily: 'Sora, sans-serif', fontSize: '1.15rem', fontWeight: 700, color: '#0f172a', lineHeight: 1.35 }}>
              {paper.title}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="btn btn-ghost"
            style={{ borderRadius: '0.4rem', padding: '0.4rem', color: '#64748b' }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Tab Navigation */}
        <div style={{ padding: '0 1.75rem', borderBottom: '1px solid #e2e8f0', display: 'flex', gap: '1.5rem', background: '#fff' }}>
          {(['metadata', 'provenance', 'raw'] as const).map((tab) => {
            const labels = {
              metadata: 'Normalized Metadata',
              provenance: `Database Provenance (${paper.sources.length})`,
              raw: 'Raw Provider Payload',
            };
            const isActive = activeTab === tab;
            return (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                style={{
                  background: 'none',
                  border: 'none',
                  borderBottom: `2.5px solid ${isActive ? '#4f46e5' : 'transparent'}`,
                  padding: '0.75rem 0',
                  fontWeight: 600,
                  fontSize: '0.8rem',
                  color: isActive ? '#4f46e5' : '#64748b',
                  cursor: 'pointer',
                  transition: 'all 0.15s',
                }}
              >
                {labels[tab]}
              </button>
            );
          })}
        </div>

        {/* Content Body */}
        <div style={{ padding: '1.5rem 1.75rem', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '1.25rem', fontSize: '0.82rem' }}>
          {activeTab === 'metadata' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <div>
                <span style={{ fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: '#64748b', display: 'block', marginBottom: '0.3rem' }}>
                  Authors
                </span>
                <p style={{ fontWeight: 600, color: '#1e293b' }}>
                  {paper.authors.length > 0 ? paper.authors.join(', ') : 'Not recorded'}
                </p>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', background: '#f8fafc', padding: '1rem', borderRadius: '0.65rem', border: '1px solid #e2e8f0' }}>
                <div>
                  <span style={{ fontSize: '0.68rem', fontWeight: 700, textTransform: 'uppercase', color: '#64748b', display: 'block', marginBottom: '0.2rem' }}>
                    Year
                  </span>
                  <span style={{ fontFamily: 'JetBrains Mono, monospace', fontWeight: 700, color: '#0f172a' }}>
                    {paper.publication_year || 'N/A'}
                  </span>
                </div>
                <div>
                  <span style={{ fontSize: '0.68rem', fontWeight: 700, textTransform: 'uppercase', color: '#64748b', display: 'block', marginBottom: '0.2rem' }}>
                    Citations
                  </span>
                  <span style={{ fontFamily: 'JetBrains Mono, monospace', fontWeight: 700, color: '#059669' }}>
                    {paper.citation_count ?? 'N/A'}
                  </span>
                </div>
                <div>
                  <span style={{ fontSize: '0.68rem', fontWeight: 700, textTransform: 'uppercase', color: '#64748b', display: 'block', marginBottom: '0.2rem' }}>
                    Venue
                  </span>
                  <span style={{ fontWeight: 600, color: '#0f172a' }}>
                    {paper.venue || 'N/A'}
                  </span>
                </div>
              </div>

              {paper.doi && (
                <div>
                  <span style={{ fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: '#64748b', display: 'block', marginBottom: '0.3rem' }}>
                    DOI & Links
                  </span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <a
                      href={`https://doi.org/${paper.doi}`}
                      target="_blank"
                      rel="noreferrer"
                      className="badge badge-brand"
                      style={{ fontFamily: 'JetBrains Mono, monospace', textDecoration: 'none', padding: '0.35rem 0.65rem' }}
                    >
                      https://doi.org/{paper.doi}
                      <ExternalLink size={11} style={{ marginLeft: 4 }} />
                    </a>
                    {paper.pdf_url && (
                      <a
                        href={paper.pdf_url}
                        target="_blank"
                        rel="noreferrer"
                        className="badge badge-success"
                        style={{ textDecoration: 'none', padding: '0.35rem 0.65rem' }}
                      >
                        <FileText size={11} style={{ marginRight: 4 }} />
                        Direct PDF Link
                        <ExternalLink size={11} style={{ marginLeft: 4 }} />
                      </a>
                    )}
                  </div>
                </div>
              )}

              {paper.abstract && (
                <div>
                  <span style={{ fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: '#64748b', display: 'block', marginBottom: '0.3rem' }}>
                    Abstract
                  </span>
                  <p style={{ color: '#334155', lineHeight: 1.6, background: '#f8fafc', padding: '1rem', borderRadius: '0.65rem', border: '1px solid #e2e8f0' }}>
                    {paper.abstract}
                  </p>
                </div>
              )}
            </div>
          )}

          {activeTab === 'provenance' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <p style={{ color: '#64748b', fontSize: '0.78rem' }}>
                This canonical record was retrieved and synthesized from {paper.sources.length} academic source(s):
              </p>
              {paper.sources.map((src, i) => {
                const dbStyle = DB_COLORS[src.source_database] || { bg: '#f1f5f9', color: '#475569', border: '#e2e8f0' };
                return (
                  <div
                    key={i}
                    style={{
                      background: '#fff',
                      border: `1.5px solid ${dbStyle.border}`,
                      borderRadius: '0.65rem',
                      padding: '1rem 1.25rem',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '0.5rem',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <span
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          padding: '0.2rem 0.65rem',
                          borderRadius: '100px',
                          fontSize: '0.72rem',
                          fontWeight: 700,
                          background: dbStyle.bg,
                          color: dbStyle.color,
                        }}
                      >
                        {src.source_database}
                      </span>
                      <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '0.72rem', color: '#94a3b8' }}>
                        ID: {src.external_source_id || src.id.slice(0, 8)}
                      </span>
                    </div>
                    {src.source_url && (
                      <div style={{ fontSize: '0.75rem', color: '#475569' }}>
                        <strong>Source URL:</strong>{' '}
                        <a
                          href={src.source_url}
                          target="_blank"
                          rel="noreferrer"
                          style={{ fontFamily: 'JetBrains Mono, monospace', color: '#4f46e5', textDecoration: 'none' }}
                        >
                          {src.source_url}
                        </a>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}

          {activeTab === 'raw' && (
            <div>
              <span style={{ fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: '#64748b', display: 'block', marginBottom: '0.5rem' }}>
                Normalized JSON Document
              </span>
              <pre
                style={{
                  background: '#0f172a',
                  color: '#e2e8f0',
                  padding: '1rem',
                  borderRadius: '0.65rem',
                  fontSize: '0.72rem',
                  fontFamily: 'JetBrains Mono, monospace',
                  overflowX: 'auto',
                  maxHeight: 320,
                }}
              >
                {JSON.stringify(paper, null, 2)}
              </pre>
            </div>
          )}
        </div>

        {/* Footer actions */}
        <div style={{ padding: '1rem 1.75rem', borderTop: '1px solid #e2e8f0', background: '#f8fafc', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <button
            onClick={handleCopyCitation}
            className="btn btn-secondary btn-sm"
          >
            {copied ? <Check size={13} color="#10b981" /> : <Copy size={13} />}
            <span>{copied ? 'Citation Copied!' : 'Copy Formatted Citation'}</span>
          </button>
          <button onClick={onClose} className="btn btn-primary btn-sm">
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
