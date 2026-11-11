import React, { useState } from 'react';
import { Paper } from '../types';
import { X, ExternalLink, FileText, Database, Code, Check } from 'lucide-react';

interface PaperModalProps {
  paper: Paper | null;
  onClose: () => void;
}

export const PaperModal: React.FC<PaperModalProps> = ({ paper, onClose }) => {
  if (!paper) return null;

  const [activeTab, setActiveTab] = useState<'metadata' | 'provenance' | 'raw'>('metadata');
  const [copied, setCopied] = useState(false);

  const handleCopyCitation = () => {
    const authorsStr = paper.authors.join(', ');
    const citation = `${authorsStr}. "${paper.title}". ${paper.venue || 'Publication'}, ${paper.publication_year || 'n.d.'}. ${paper.doi ? `DOI: ${paper.doi}` : ''}`;
    navigator.clipboard.writeText(citation);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs">
      <div className="bg-white rounded-xl shadow-2xl max-w-3xl w-full max-h-[90vh] flex flex-col overflow-hidden border border-slate-200">
        {/* Header */}
        <div className="p-5 border-b border-slate-200 flex items-start justify-between gap-4 bg-slate-50/50">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="badge bg-indigo-50 text-indigo-700 border border-indigo-200 font-mono text-[11px]">
                ID: {paper.id.slice(0, 16)}...
              </span>
              {paper.is_open_access && (
                <span className="badge bg-emerald-50 text-emerald-800 border border-emerald-200 text-[11px]">
                  Open Access
                </span>
              )}
            </div>
            <h2 className="text-lg font-bold font-serif text-slate-900 leading-snug">
              {paper.title}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-700 rounded-md hover:bg-slate-200/60 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="px-5 border-b border-slate-200 flex items-center gap-6 text-xs font-semibold">
          <button
            onClick={() => setActiveTab('metadata')}
            className={`py-3 border-b-2 transition-colors ${
              activeTab === 'metadata'
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            Normalized Metadata
          </button>
          <button
            onClick={() => setActiveTab('provenance')}
            className={`py-3 border-b-2 transition-colors ${
              activeTab === 'provenance'
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            Database Provenance ({paper.sources.length})
          </button>
          <button
            onClick={() => setActiveTab('raw')}
            className={`py-3 border-b-2 transition-colors ${
              activeTab === 'raw'
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            Raw Provider Payload
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto space-y-5 text-xs flex-1">
          {activeTab === 'metadata' && (
            <div className="space-y-4">
              <div>
                <h4 className="font-semibold text-slate-400 uppercase tracking-wider text-[11px] mb-1">
                  Authors
                </h4>
                <p className="text-slate-800 text-sm font-medium">
                  {paper.authors.length > 0 ? paper.authors.join(', ') : 'Not recorded'}
                </p>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 p-3.5 bg-slate-50 rounded-lg border border-slate-200/80">
                <div>
                  <span className="text-slate-400 block text-[10px] uppercase font-semibold">Year</span>
                  <span className="font-mono text-slate-800">{paper.publication_year || 'Unknown'}</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px] uppercase font-semibold">Venue</span>
                  <span className="text-slate-800 truncate block">{paper.venue || 'Not available'}</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px] uppercase font-semibold">Citations</span>
                  <span className="font-mono font-bold text-emerald-700">{paper.citation_count || 0}</span>
                </div>
              </div>

              {paper.doi && (
                <div>
                  <span className="text-slate-400 block text-[10px] uppercase font-semibold mb-0.5">DOI</span>
                  <a
                    href={`https://doi.org/${paper.doi}`}
                    target="_blank"
                    rel="noreferrer"
                    className="font-mono text-indigo-600 hover:underline flex items-center gap-1"
                  >
                    <span>{paper.doi}</span>
                    <ExternalLink className="h-3 w-3" />
                  </a>
                </div>
              )}

              {paper.pdf_url && (
                <div>
                  <span className="text-slate-400 block text-[10px] uppercase font-semibold mb-0.5">Full-Text PDF</span>
                  <a
                    href={paper.pdf_url}
                    target="_blank"
                    rel="noreferrer"
                    className="font-medium text-emerald-700 hover:underline flex items-center gap-1"
                  >
                    <FileText className="h-3.5 w-3.5" />
                    <span>Open Access PDF Link</span>
                    <ExternalLink className="h-3 w-3" />
                  </a>
                </div>
              )}

              <div>
                <h4 className="font-semibold text-slate-400 uppercase tracking-wider text-[11px] mb-1">
                  Abstract
                </h4>
                <div className="p-3 bg-slate-50 rounded-lg text-slate-700 leading-relaxed border border-slate-100 text-xs">
                  {paper.abstract || 'No abstract was provided by the retrieved academic sources.'}
                </div>
              </div>

              <div className="pt-2 flex items-center gap-2">
                <button
                  onClick={handleCopyCitation}
                  className="btn-secondary py-1.5 px-3 text-xs flex items-center gap-1.5"
                >
                  {copied ? <Check className="h-3.5 w-3.5 text-emerald-600" /> : <Code className="h-3.5 w-3.5" />}
                  <span>{copied ? 'Citation Copied!' : 'Copy Formatted Citation'}</span>
                </button>
              </div>
            </div>
          )}

          {activeTab === 'provenance' && (
            <div className="space-y-4">
              <p className="text-slate-500 text-xs">
                This canonical paper record was aggregated from the following source databases. Duplicate detection verified identity and merged metadata.
              </p>
              <div className="space-y-3">
                {paper.sources.map((src, i) => (
                  <div key={i} className="p-4 rounded-lg border border-slate-200 bg-slate-50/70 space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className={`badge badge-${src.source_database}`}>
                        {src.source_database}
                      </span>
                      <span className="text-[10px] font-mono text-slate-400">
                        Retrieved: {new Date(src.retrieved_at).toLocaleString()}
                      </span>
                    </div>
                    <div className="text-xs">
                      <span className="text-slate-500">External ID: </span>
                      <code className="font-mono text-slate-800">{src.external_source_id || 'N/A'}</code>
                    </div>
                    {src.source_url && (
                      <div className="text-xs">
                        <span className="text-slate-500">Source Landing URL: </span>
                        <a
                          href={src.source_url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-indigo-600 hover:underline break-all"
                        >
                          {src.source_url}
                        </a>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'raw' && (
            <div className="space-y-3">
              <p className="text-slate-500 text-xs">
                Unmodified raw JSON payloads received directly from the provider API adapters:
              </p>
              {paper.sources.map((src, i) => (
                <div key={i} className="space-y-1">
                  <span className="font-semibold text-slate-700 capitalize">{src.source_database} Payload:</span>
                  <pre className="p-3 bg-slate-900 text-slate-200 rounded-lg text-[11px] font-mono overflow-x-auto max-h-60 border border-slate-800">
                    {JSON.stringify(src.raw_metadata, null, 2)}
                  </pre>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-200 bg-slate-50 flex items-center justify-end">
          <button onClick={onClose} className="btn-secondary py-1.5 px-4 text-xs">
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

