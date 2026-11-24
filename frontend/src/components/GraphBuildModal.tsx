import React, { useState, useEffect } from 'react';
import {
  X,
  History,
  ShieldCheck,
  AlertTriangle,
  RefreshCw,
  Clock,
  Layers,
  CheckCircle2,
  FileText,
} from 'lucide-react';
import { GraphBuildRun, GraphValidationRecord } from '../types/graph';
import { getGraphBuildHistory, getGraphValidation } from '../services/api';

interface GraphBuildModalProps {
  requestId: string;
  isOpen: boolean;
  onClose: () => void;
  onRebuildTriggered: () => void;
}

export const GraphBuildModal: React.FC<GraphBuildModalProps> = ({
  requestId,
  isOpen,
  onClose,
  onRebuildTriggered,
}) => {
  const [activeTab, setActiveTab] = useState<'validation' | 'history'>('validation');
  const [runs, setRuns] = useState<GraphBuildRun[]>([]);
  const [validation, setValidation] = useState<GraphValidationRecord | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (isOpen && requestId) {
      loadData();
    }
  }, [isOpen, requestId]);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [historyData, valData] = await Promise.all([
        getGraphBuildHistory(requestId),
        getGraphValidation(requestId),
      ]);
      setRuns(historyData);
      setValidation(valData);
    } catch (err) {
      console.error('Failed to load build data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 50,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'rgba(15, 23, 42, 0.65)',
        backdropFilter: 'blur(4px)',
        padding: '1rem',
      }}
    >
      <div
        style={{
          background: '#fff',
          borderRadius: '1rem',
          maxWidth: 800,
          width: '100%',
          maxHeight: '85vh',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: '0 25px 50px -12px rgba(0,0,0,0.25)',
          overflow: 'hidden',
        }}
      >
        {/* Header */}
        <div
          style={{
            padding: '1.25rem 1.5rem',
            borderBottom: '1px solid #e2e8f0',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: 'linear-gradient(135deg, #1e1b4b 0%, #312e81 100%)',
            color: '#fff',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div
              style={{
                width: 36,
                height: 36,
                borderRadius: '0.5rem',
                background: 'rgba(255,255,255,0.15)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <ShieldCheck size={20} color="#fff" />
            </div>
            <div>
              <h2 style={{ fontSize: '1.1rem', fontWeight: 700, margin: 0 }}>
                Evidence Graph Audit & Build History
              </h2>
              <div style={{ fontSize: '0.75rem', color: '#cbd5e1', marginTop: 2 }}>
                Reproducibility log and provenance verification status
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              color: '#fff',
              cursor: 'pointer',
              padding: '0.4rem',
              borderRadius: '0.375rem',
            }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Tab Controls */}
        <div
          style={{
            display: 'flex',
            gap: '1rem',
            padding: '0.75rem 1.5rem',
            borderBottom: '1px solid #e2e8f0',
            background: '#f8fafc',
          }}
        >
          <button
            onClick={() => setActiveTab('validation')}
            style={{
              padding: '0.45rem 0.9rem',
              borderRadius: '0.5rem',
              border: 'none',
              fontSize: '0.82rem',
              fontWeight: 600,
              cursor: 'pointer',
              background: activeTab === 'validation' ? '#6366f1' : 'transparent',
              color: activeTab === 'validation' ? '#fff' : '#64748b',
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
            }}
          >
            <ShieldCheck size={16} />
            <span>Integrity & Provenance Report</span>
          </button>
          <button
            onClick={() => setActiveTab('history')}
            style={{
              padding: '0.45rem 0.9rem',
              borderRadius: '0.5rem',
              border: 'none',
              fontSize: '0.82rem',
              fontWeight: 600,
              cursor: 'pointer',
              background: activeTab === 'history' ? '#6366f1' : 'transparent',
              color: activeTab === 'history' ? '#fff' : '#64748b',
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
            }}
          >
            <History size={16} />
            <span>Build Batches ({runs.length})</span>
          </button>
        </div>

        {/* Content Body */}
        <div style={{ padding: '1.5rem', overflowY: 'auto', flex: 1 }}>
          {isLoading ? (
            <div style={{ textAlign: 'center', padding: '3rem 0', color: '#64748b' }}>
              <RefreshCw size={28} className="animate-spin" style={{ margin: '0 auto 1rem' }} />
              <div>Auditing graph integrity...</div>
            </div>
          ) : activeTab === 'validation' && validation ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              {/* Status Banner */}
              <div
                style={{
                  padding: '1rem 1.25rem',
                  borderRadius: '0.75rem',
                  background:
                    validation.integrity_status === 'valid'
                      ? '#ecfdf5'
                      : '#fffbeb',
                  border: `1px solid ${
                    validation.integrity_status === 'valid' ? '#a7f3d0' : '#fde68a'
                  }`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  {validation.integrity_status === 'valid' ? (
                    <CheckCircle2 size={24} color="#059669" />
                  ) : (
                    <AlertTriangle size={24} color="#d97706" />
                  )}
                  <div>
                    <div
                      style={{
                        fontSize: '0.92rem',
                        fontWeight: 700,
                        color:
                          validation.integrity_status === 'valid'
                            ? '#065f46'
                            : '#92400e',
                      }}
                    >
                      Graph Integrity Status: {validation.integrity_status.toUpperCase()}
                    </div>
                    <div style={{ fontSize: '0.76rem', color: '#64748b', marginTop: 2 }}>
                      {validation.claims_with_evidence} /{' '}
                      {validation.claims_with_evidence + validation.claims_without_evidence} claims anchored to verbatim evidence passages
                    </div>
                  </div>
                </div>
              </div>

              {/* KPI Grid */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
                  gap: '0.75rem',
                }}
              >
                <div style={{ padding: '0.85rem', background: '#f8fafc', borderRadius: '0.5rem', border: '1px solid #e2e8f0' }}>
                  <div style={{ fontSize: '0.7rem', color: '#64748b', fontWeight: 600 }}>TOTAL NODES</div>
                  <div style={{ fontSize: '1.35rem', fontWeight: 800, color: '#1e293b' }}>{validation.total_nodes}</div>
                </div>
                <div style={{ padding: '0.85rem', background: '#f8fafc', borderRadius: '0.5rem', border: '1px solid #e2e8f0' }}>
                  <div style={{ fontSize: '0.7rem', color: '#64748b', fontWeight: 600 }}>RELATIONSHIPS</div>
                  <div style={{ fontSize: '1.35rem', fontWeight: 800, color: '#1e293b' }}>{validation.total_relationships}</div>
                </div>
                <div style={{ padding: '0.85rem', background: '#f8fafc', borderRadius: '0.5rem', border: '1px solid #e2e8f0' }}>
                  <div style={{ fontSize: '0.7rem', color: '#64748b', fontWeight: 600 }}>ANCHORED PASSAGES</div>
                  <div style={{ fontSize: '1.35rem', fontWeight: 800, color: '#059669' }}>{validation.findings_with_passages}</div>
                </div>
                <div style={{ padding: '0.85rem', background: '#f8fafc', borderRadius: '0.5rem', border: '1px solid #e2e8f0' }}>
                  <div style={{ fontSize: '0.7rem', color: '#64748b', fontWeight: 600 }}>ORPHAN NODES</div>
                  <div style={{ fontSize: '1.35rem', fontWeight: 800, color: validation.orphan_nodes_count > 0 ? '#e11d48' : '#059669' }}>
                    {validation.orphan_nodes_count}
                  </div>
                </div>
              </div>

              {/* Node Types Distribution */}
              <div>
                <h4 style={{ fontSize: '0.82rem', fontWeight: 700, color: '#334155', marginBottom: '0.5rem' }}>
                  Node Entity Breakdown
                </h4>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
                  {Object.entries(validation.nodes_by_type || {}).map(([type, count]) => (
                    <span
                      key={type}
                      style={{
                        padding: '0.25rem 0.6rem',
                        background: '#f1f5f9',
                        borderRadius: '0.375rem',
                        fontSize: '0.75rem',
                        color: '#475569',
                        border: '1px solid #cbd5e1',
                      }}
                    >
                      <strong>{type}</strong>: {count}
                    </span>
                  ))}
                </div>
              </div>

              {/* Relationships Breakdown */}
              <div>
                <h4 style={{ fontSize: '0.82rem', fontWeight: 700, color: '#334155', marginBottom: '0.5rem' }}>
                  Relationship Edge Breakdown
                </h4>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
                  {Object.entries(validation.relationships_by_type || {}).map(([rel, count]) => (
                    <span
                      key={rel}
                      style={{
                        padding: '0.25rem 0.6rem',
                        background: '#e0e7ff',
                        borderRadius: '0.375rem',
                        fontSize: '0.75rem',
                        color: '#3730a3',
                        border: '1px solid #c7d2fe',
                      }}
                    >
                      <strong>{rel}</strong>: {count}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ) : activeTab === 'history' ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {runs.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '2rem 0', color: '#94a3b8' }}>
                  No past build runs recorded yet.
                </div>
              ) : (
                runs.map((r) => (
                  <div
                    key={r.id}
                    style={{
                      padding: '1rem',
                      borderRadius: '0.5rem',
                      background: '#f8fafc',
                      border: '1px solid #e2e8f0',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                    }}
                  >
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span
                          style={{
                            fontWeight: 700,
                            fontSize: '0.88rem',
                            color: '#1e293b',
                          }}
                        >
                          Run #{r.run_number} ({r.trigger_type})
                        </span>
                        <span
                          style={{
                            fontSize: '0.65rem',
                            fontWeight: 700,
                            padding: '0.15rem 0.45rem',
                            borderRadius: '100px',
                            background: '#dcfce7',
                            color: '#166534',
                          }}
                        >
                          {r.status.toUpperCase()}
                        </span>
                      </div>
                      <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: 4 }}>
                        {r.total_nodes} nodes · {r.total_edges} edges · {r.papers_processed} papers processed in {r.execution_time_seconds}s
                      </div>
                    </div>
                    <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>
                      {new Date(r.created_at).toLocaleString()}
                    </div>
                  </div>
                ))
              )}
            </div>
          ) : null}
        </div>

        {/* Footer */}
        <div
          style={{
            padding: '1rem 1.5rem',
            borderTop: '1px solid #e2e8f0',
            background: '#f8fafc',
            display: 'flex',
            justifyContent: 'flex-end',
            gap: '0.75rem',
          }}
        >
          <button
            onClick={onClose}
            style={{
              padding: '0.5rem 1rem',
              borderRadius: '0.5rem',
              border: '1px solid #cbd5e1',
              background: '#fff',
              fontSize: '0.82rem',
              fontWeight: 600,
              cursor: 'pointer',
              color: '#475569',
            }}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
