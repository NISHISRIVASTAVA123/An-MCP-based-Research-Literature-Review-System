import React, { useState } from 'react';
import { EvidenceRecord, EvidencePassage } from '../types';
import { updateEvidencePassage } from '../services/api';
import {
  X, CheckCircle2, AlertTriangle, FileText, Layers, Tag,
  BarChart2, ShieldAlert, Compass, Sparkles, BookOpen, Quote,
} from 'lucide-react';

interface EvidenceViewModalProps {
  evidence: EvidenceRecord | null;
  paperTitle: string;
  onClose: () => void;
  onPassageUpdated?: () => void;
}

export const EvidenceViewModal: React.FC<EvidenceViewModalProps> = ({
  evidence,
  paperTitle,
  onClose,
  onPassageUpdated,
}) => {
  if (!evidence) return null;

  const [activeTab, setActiveTab] = useState<
    'objective' | 'methodology' | 'datasets' | 'metrics_findings' | 'limitations' | 'passages'
  >('objective');

  const [isUpdatingPassage, setIsUpdatingPassage] = useState<string | null>(null);

  const handleVerifyPassage = async (passageId: string, status: 'user_verified' | 'flagged_incorrect') => {
    setIsUpdatingPassage(passageId);
    try {
      await updateEvidencePassage(passageId, {
        verification_status: status,
        user_notes: status === 'user_verified' ? 'Verified by researcher' : 'Flagged by researcher for review',
      });
      if (onPassageUpdated) onPassageUpdated();
    } catch (err) {
      console.error('Failed to update passage status:', err);
    } finally {
      setIsUpdatingPassage(null);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-panel"
        style={{ maxWidth: 860, width: '100%', display: 'flex', flexDirection: 'column' }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div style={{ padding: '1.5rem 1.75rem', borderBottom: '1px solid #e2e8f0', background: 'linear-gradient(135deg, #1e1b4b 0%, #312e81 100%)', color: '#fff', display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '1rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.4rem' }}>
              <span style={{
                fontSize: '0.68rem', fontWeight: 700, padding: '0.15rem 0.55rem', borderRadius: '100px',
                background: evidence.source_scope === 'full_text' ? 'rgba(16,185,129,0.25)' : 'rgba(245,158,11,0.25)',
                color: evidence.source_scope === 'full_text' ? '#6ee7b7' : '#fcd34d',
                border: `1px solid ${evidence.source_scope === 'full_text' ? 'rgba(52,211,153,0.4)' : 'rgba(251,191,36,0.4)'}`,
              }}>
                {evidence.source_scope === 'full_text' ? 'Full-Text Document Extraction' : 'Abstract-Only Extraction'}
              </span>
              <span className="badge badge-brand" style={{ fontSize: '0.68rem' }}>
                Backend: {evidence.extractor_backend}
              </span>
            </div>
            <h2 style={{ fontFamily: 'Sora, sans-serif', fontSize: '1.15rem', fontWeight: 700, lineHeight: 1.35 }}>
              {paperTitle}
            </h2>
          </div>
          <button onClick={onClose} className="btn btn-ghost" style={{ borderRadius: '0.4rem', padding: '0.4rem', color: '#cbd5e1' }}>
            <X size={18} />
          </button>
        </div>

        {/* Tab Navigation */}
        <div style={{ padding: '0 1.75rem', borderBottom: '1px solid #e2e8f0', display: 'flex', gap: '1.25rem', background: '#fff', overflowX: 'auto' }}>
          {[
            { id: 'objective', label: 'Objective & Problem' },
            { id: 'methodology', label: `Methodology (${evidence.methodology.items.length})` },
            { id: 'datasets', label: `Datasets (${evidence.datasets.length})` },
            { id: 'metrics_findings', label: `Metrics & Findings (${evidence.evaluation_metrics.length + evidence.findings.length})` },
            { id: 'limitations', label: `Limitations (${evidence.limitations.length})` },
            { id: 'passages', label: `Verifiable Passages (${evidence.passages.length})` },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              style={{
                background: 'none',
                border: 'none',
                borderBottom: `2.5px solid ${activeTab === tab.id ? '#4f46e5' : 'transparent'}`,
                padding: '0.75rem 0',
                fontWeight: 600,
                fontSize: '0.78rem',
                color: activeTab === tab.id ? '#4f46e5' : '#64748b',
                cursor: 'pointer',
                whiteSpace: 'nowrap',
                transition: 'all 0.15s',
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content Body */}
        <div style={{ padding: '1.5rem 1.75rem', overflowY: 'auto', maxHeight: 480, display: 'flex', flexDirection: 'column', gap: '1.25rem', fontSize: '0.82rem' }}>
          {/* Objective Tab */}
          {activeTab === 'objective' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div className="card" style={{ padding: '1.25rem', background: '#f8fafc' }}>
                <span style={{ fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: '#4f46e5', display: 'block', marginBottom: '0.4rem' }}>
                  Research Problem Statement
                </span>
                <p style={{ fontWeight: 600, color: '#1e293b', lineHeight: 1.55 }}>
                  {evidence.research_objective.problem_statement}
                </p>
                {evidence.research_objective.supporting_passage && (
                  <div style={{ marginTop: '0.75rem', paddingTop: '0.6rem', borderTop: '1px solid #e2e8f0', fontSize: '0.75rem', color: '#64748b', fontStyle: 'italic' }}>
                    <Quote size={12} style={{ display: 'inline', marginRight: 4 }} />
                    "{evidence.research_objective.supporting_passage}"
                    {evidence.research_objective.page_number && (
                      <span style={{ fontWeight: 600, color: '#4f46e5', marginLeft: 6 }}>
                        (Page {evidence.research_objective.page_number}, {evidence.research_objective.section_heading || 'Intro'})
                      </span>
                    )}
                  </div>
                )}
              </div>

              {evidence.contributions.length > 0 && (
                <div>
                  <span style={{ fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: '#64748b', display: 'block', marginBottom: '0.4rem' }}>
                    Claimed Contributions
                  </span>
                  <ul style={{ paddingLeft: '1.25rem', color: '#334155', lineHeight: 1.6 }}>
                    {evidence.contributions.map((c, i) => (
                      <li key={i}>{c}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* Methodology Tab */}
          {activeTab === 'methodology' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
              {evidence.methodology.items.map((m, i) => (
                <div key={i} className="card" style={{ padding: '1.15rem 1.25rem', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <span style={{ fontFamily: 'Sora, sans-serif', fontWeight: 700, fontSize: '0.95rem', color: '#1e293b' }}>
                      {m.approach_name}
                    </span>
                    <span className="badge badge-brand" style={{ fontSize: '0.68rem', textTransform: 'capitalize' }}>
                      {m.approach_type.replace('_', ' ')}
                    </span>
                  </div>
                  {m.description && <p style={{ color: '#475569', fontSize: '0.78rem' }}>{m.description}</p>}
                  {m.supporting_passage && (
                    <div style={{ background: '#f8fafc', padding: '0.5rem 0.75rem', borderRadius: '0.4rem', border: '1px solid #e2e8f0', fontSize: '0.72rem', color: '#64748b', fontStyle: 'italic' }}>
                      "{m.supporting_passage}"
                      {m.page_number && <span style={{ color: '#4f46e5', fontWeight: 600, marginLeft: 5 }}>(p. {m.page_number})</span>}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Datasets Tab */}
          {activeTab === 'datasets' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {evidence.datasets.length === 0 ? (
                <p style={{ color: '#94a3b8', fontStyle: 'italic' }}>No explicit dataset records identified in text.</p>
              ) : (
                evidence.datasets.map((d, i) => (
                  <div key={i} className="card" style={{ padding: '1rem 1.25rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
                      <strong style={{ fontSize: '0.9rem', color: '#1e293b' }}>{d.dataset_name}</strong>
                      {d.modality && <span className="badge badge-neutral" style={{ fontSize: '0.68rem' }}>{d.modality}</span>}
                    </div>
                    {d.reported_sample_size && (
                      <div style={{ fontSize: '0.75rem', color: '#64748b' }}>
                        Sample Size: <strong style={{ color: '#1e293b' }}>{d.reported_sample_size}</strong>
                      </div>
                    )}
                    {d.supporting_passage && (
                      <div style={{ marginTop: '0.5rem', background: '#f8fafc', padding: '0.4rem 0.65rem', borderRadius: '0.4rem', border: '1px solid #e2e8f0', fontSize: '0.72rem', color: '#64748b', fontStyle: 'italic' }}>
                        "{d.supporting_passage}"
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          )}

          {/* Metrics & Findings Tab */}
          {activeTab === 'metrics_findings' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              {/* Metrics */}
              {evidence.evaluation_metrics.length > 0 && (
                <div>
                  <span style={{ fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: '#059669', display: 'block', marginBottom: '0.5rem' }}>
                    Reported Quantitative Metrics
                  </span>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.65rem' }}>
                    {evidence.evaluation_metrics.map((met, i) => (
                      <div key={i} style={{ background: '#ecfdf5', borderRadius: '0.6rem', padding: '0.75rem 1rem', border: '1px solid #a7f3d0' }}>
                        <div style={{ fontSize: '0.68rem', fontWeight: 700, textTransform: 'uppercase', color: '#065f46' }}>{met.metric_name}</div>
                        <div style={{ fontSize: '1.35rem', fontWeight: 800, fontFamily: 'JetBrains Mono, monospace', color: '#047857' }}>
                          {met.reported_value}
                        </div>
                        {met.experimental_context && (
                          <div style={{ fontSize: '0.68rem', color: '#065f46', marginTop: 2 }}>{met.experimental_context}</div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Findings */}
              <div>
                <span style={{ fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: '#64748b', display: 'block', marginBottom: '0.5rem' }}>
                  Scientific Findings & Results
                </span>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
                  {evidence.findings.map((f, i) => (
                    <div key={i} className="card" style={{ padding: '0.85rem 1.15rem' }}>
                      <p style={{ color: '#1e293b', fontWeight: 500 }}>{f.finding_statement}</p>
                      {f.supporting_passage && (
                        <div style={{ marginTop: '0.4rem', fontSize: '0.72rem', color: '#64748b', fontStyle: 'italic' }}>
                          "{f.supporting_passage}" {f.page_number && <span style={{ color: '#4f46e5' }}>(p. {f.page_number})</span>}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Limitations & Future Work Tab */}
          {activeTab === 'limitations' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.5rem' }}>
                  <ShieldAlert size={15} color="#e11d48" />
                  <span style={{ fontSize: '0.72rem', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: '#e11d48' }}>
                    Author-Reported Limitations (Critical for Phase 5 Gap Verification)
                  </span>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
                  {evidence.limitations.map((lim, i) => (
                    <div key={i} style={{ background: '#fff1f2', borderRadius: '0.65rem', padding: '0.85rem 1.15rem', border: '1px solid #fecdd3' }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                        <strong style={{ color: '#9f1239', fontSize: '0.82rem' }}>
                          {lim.limitation_type === 'author_reported' ? 'Explicit Author Limitation' : 'System-Inferred Limitation'}
                        </strong>
                        {lim.aspect && <span className="badge badge-error" style={{ fontSize: '0.65rem' }}>{lim.aspect}</span>}
                      </div>
                      <p style={{ color: '#881337', fontSize: '0.8rem' }}>{lim.limitation_text}</p>
                      {lim.supporting_passage && (
                        <div style={{ marginTop: '0.4rem', fontSize: '0.72rem', color: '#9f1239', fontStyle: 'italic' }}>
                          "{lim.supporting_passage}" {lim.page_number && <span>(p. {lim.page_number}, {lim.section_heading || 'Limitations'})</span>}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {evidence.future_work.length > 0 && (
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.5rem' }}>
                    <Compass size={15} color="#0284c7" />
                    <span style={{ fontSize: '0.72rem', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: '#0284c7' }}>
                      Author-Proposed Future Directions
                    </span>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    {evidence.future_work.map((fw, i) => (
                      <div key={i} style={{ background: '#f0f9ff', borderRadius: '0.65rem', padding: '0.85rem 1.15rem', border: '1px solid #bae6fd' }}>
                        <p style={{ color: '#0369a1', fontSize: '0.8rem', fontWeight: 500 }}>{fw.direction_text}</p>
                        {fw.supporting_passage && (
                          <div style={{ marginTop: '0.35rem', fontSize: '0.72rem', color: '#0284c7', fontStyle: 'italic' }}>
                            "{fw.supporting_passage}" {fw.page_number && <span>(p. {fw.page_number})</span>}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Passages Tab */}
          {activeTab === 'passages' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <p style={{ fontSize: '0.78rem', color: '#64748b' }}>
                Every extracted statement is traced back to verbatim text in the scientific article:
              </p>
              {evidence.passages.map((p) => {
                const isVerified = p.verification_status === 'user_verified';
                const isFlagged = p.verification_status === 'flagged_incorrect';
                return (
                  <div key={p.id} className="card" style={{ padding: '1rem 1.25rem', borderLeft: `4px solid ${isVerified ? '#10b981' : isFlagged ? '#f43f5e' : '#6366f1'}` }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                        <span className="badge badge-brand" style={{ fontSize: '0.65rem', textTransform: 'capitalize' }}>
                          {p.category}
                        </span>
                        {p.page_number && (
                          <span style={{ fontSize: '0.7rem', color: '#64748b', fontFamily: 'JetBrains Mono, monospace' }}>
                            Page {p.page_number} {p.section_heading ? `• ${p.section_heading}` : ''}
                          </span>
                        )}
                      </div>
                      <span className={`badge ${isVerified ? 'badge-success' : isFlagged ? 'badge-error' : 'badge-neutral'}`} style={{ fontSize: '0.65rem' }}>
                        {p.verification_status.replace('_', ' ')}
                      </span>
                    </div>

                    <strong style={{ fontSize: '0.82rem', color: '#1e293b', display: 'block', marginBottom: '0.35rem' }}>
                      {p.statement}
                    </strong>

                    {p.verbatim_passage && (
                      <div style={{ background: '#f8fafc', padding: '0.5rem 0.75rem', borderRadius: '0.4rem', border: '1px solid #e2e8f0', fontSize: '0.74rem', color: '#475569', fontStyle: 'italic', marginBottom: '0.5rem' }}>
                        "{p.verbatim_passage}"
                      </div>
                    )}

                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '0.5rem', paddingTop: '0.4rem', borderTop: '1px solid #f1f5f9' }}>
                      <button
                        onClick={() => handleVerifyPassage(p.id, 'user_verified')}
                        disabled={isUpdatingPassage === p.id}
                        className="btn btn-secondary btn-sm"
                        style={{ fontSize: '0.7rem', color: '#059669', borderColor: '#a7f3d0' }}
                      >
                        <CheckCircle2 size={12} /> Verify Passage
                      </button>
                      <button
                        onClick={() => handleVerifyPassage(p.id, 'flagged_incorrect')}
                        disabled={isUpdatingPassage === p.id}
                        className="btn btn-secondary btn-sm"
                        style={{ fontSize: '0.7rem', color: '#e11d48', borderColor: '#fecdd3' }}
                      >
                        <AlertTriangle size={12} /> Flag for Review
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        <div style={{ padding: '0.85rem 1.75rem', borderTop: '1px solid #e2e8f0', background: '#f8fafc', display: 'flex', justifyContent: 'flex-end' }}>
          <button onClick={onClose} className="btn btn-primary btn-sm">
            Close Inspector
          </button>
        </div>
      </div>
    </div>
  );
};
