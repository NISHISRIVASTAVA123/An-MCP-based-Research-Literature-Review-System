import React, { useState, useEffect } from 'react';
import { ResearchRequestSummary } from '../types';
import { listResearchRequests, deleteResearchRequest } from '../services/api';
import { X, History, Trash2, ArrowRight, BookOpen, Clock, Calendar } from 'lucide-react';

interface HistoryModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectRequest: (requestId: string) => void;
}

export const HistoryModal: React.FC<HistoryModalProps> = ({
  isOpen,
  onClose,
  onSelectRequest,
}) => {
  if (!isOpen) return null;

  const [history, setHistory] = useState<ResearchRequestSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const loadHistory = async () => {
    setIsLoading(true);
    try {
      const items = await listResearchRequests();
      setHistory(items);
    } catch (err) {
      console.error('Failed to load history:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!window.confirm('Delete this saved research review and its retrieved papers?')) return;
    try {
      await deleteResearchRequest(id);
      setHistory(history.filter((h) => h.id !== id));
    } catch (err) {
      alert('Failed to delete request.');
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-panel"
        style={{ maxWidth: 640, width: '100%', display: 'flex', flexDirection: 'column' }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div style={{ padding: '1.25rem 1.5rem', borderBottom: '1px solid #e2e8f0', background: '#f8fafc', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <div style={{ padding: '0.35rem', borderRadius: '0.45rem', background: '#eef2ff' }}>
              <History size={16} color="#6366f1" />
            </div>
            <div>
              <h2 style={{ fontFamily: 'Sora, sans-serif', fontSize: '1rem', fontWeight: 700, color: '#0f172a' }}>
                Saved Research Reviews
              </h2>
              <p style={{ fontSize: '0.72rem', color: '#64748b' }}>
                Reopen past literature reviews or check saved search results
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="btn btn-ghost"
            style={{ borderRadius: '0.4rem', padding: '0.4rem', color: '#64748b' }}
          >
            <X size={18} />
          </button>
        </div>

        {/* List Body */}
        <div style={{ padding: '1.25rem 1.5rem', overflowY: 'auto', maxHeight: 440, display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {isLoading ? (
            <div style={{ padding: '3rem', textAlign: 'center', color: '#64748b', fontSize: '0.82rem' }}>
              <div className="spinner" style={{ margin: '0 auto 0.75rem', width: 24, height: 24, borderWidth: 2 }} />
              Loading review history...
            </div>
          ) : history.length === 0 ? (
            <div style={{ padding: '3rem', textAlign: 'center', color: '#64748b' }}>
              <BookOpen size={32} color="#cbd5e1" style={{ margin: '0 auto 0.5rem' }} />
              <p style={{ fontWeight: 600, fontSize: '0.9rem', color: '#1e293b' }}>No previous reviews found.</p>
              <p style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '0.2rem' }}>Submit your first research review to save it in SQLite.</p>
            </div>
          ) : (
            history.map((item) => (
              <div
                key={item.id}
                onClick={() => {
                  onSelectRequest(item.id);
                  onClose();
                }}
                className="card"
                style={{
                  padding: '1rem 1.25rem',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: '1rem',
                  border: '1.5px solid #e2e8f0',
                  transition: 'all 0.15s',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = '#c7d2fe';
                  e.currentTarget.style.backgroundColor = '#fafbff';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = '#e2e8f0';
                  e.currentTarget.style.backgroundColor = '#fff';
                }}
              >
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', marginBottom: '0.25rem' }}>
                    <span className="badge badge-brand" style={{ fontSize: '0.65rem' }}>
                      {item.domain}
                    </span>
                    <span style={{ fontSize: '0.68rem', color: '#94a3b8', fontFamily: 'JetBrains Mono, monospace' }}>
                      {item.start_year}–{item.end_year}
                    </span>
                  </div>

                  <h3 style={{ fontFamily: 'Sora, sans-serif', fontSize: '0.9rem', fontWeight: 700, color: '#0f172a', marginBottom: '0.25rem' }} className="truncate">
                    {item.topic}
                  </h3>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', fontSize: '0.72rem', color: '#64748b' }}>
                    <span>
                      <strong>{item.total_papers}</strong> papers retrieved
                    </span>
                    <span>•</span>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                      <Clock size={11} /> {new Date(item.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexShrink: 0 }}>
                  <button
                    onClick={(e) => handleDelete(item.id, e)}
                    className="btn btn-ghost"
                    style={{ padding: '0.4rem', color: '#94a3b8' }}
                    title="Delete review"
                    onMouseEnter={(e) => (e.currentTarget.style.color = '#f43f5e')}
                    onMouseLeave={(e) => (e.currentTarget.style.color = '#94a3b8')}
                  >
                    <Trash2 size={15} />
                  </button>

                  <div style={{ width: 28, height: 28, borderRadius: '50%', background: '#eef2ff', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <ArrowRight size={14} color="#6366f1" />
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        <div style={{ padding: '0.85rem 1.5rem', borderTop: '1px solid #e2e8f0', background: '#f8fafc', display: 'flex', justifyContent: 'flex-end' }}>
          <button onClick={onClose} className="btn btn-secondary btn-sm">
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
