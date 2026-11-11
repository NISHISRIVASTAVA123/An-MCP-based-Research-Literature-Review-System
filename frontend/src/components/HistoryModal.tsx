import React, { useState, useEffect } from 'react';
import { ResearchRequestSummary } from '../types';
import { listResearchRequests, deleteResearchRequest } from '../services/api';
import { X, History, Trash2, ArrowRight, BookOpen, Clock } from 'lucide-react';

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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs">
      <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[85vh] flex flex-col overflow-hidden border border-slate-200">
        <div className="p-5 border-b border-slate-200 flex items-center justify-between bg-slate-50">
          <div className="flex items-center gap-2">
            <History className="h-5 w-5 text-indigo-600" />
            <h2 className="text-base font-bold font-serif text-slate-900">
              Saved Research Reviews
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-700 rounded-md hover:bg-slate-200/60 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="p-5 overflow-y-auto space-y-3 flex-1">
          {isLoading ? (
            <div className="py-12 text-center text-slate-500 text-xs">
              Loading review history...
            </div>
          ) : history.length === 0 ? (
            <div className="py-12 text-center text-slate-500 space-y-2">
              <BookOpen className="h-8 w-8 text-slate-300 mx-auto" />
              <p className="text-sm font-medium text-slate-700">No previous reviews found.</p>
              <p className="text-xs text-slate-400">Start a new review to save literature searches.</p>
            </div>
          ) : (
            history.map((item) => (
              <div
                key={item.id}
                onClick={() => {
                  onSelectRequest(item.id);
                  onClose();
                }}
                className="academic-card p-4 hover:border-indigo-300 hover:bg-indigo-50/20 cursor-pointer transition-all flex items-start justify-between gap-4"
              >
                <div className="space-y-1 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="badge bg-slate-100 text-slate-700 border border-slate-200 text-[10px]">
                      {item.domain}
                    </span>
                    <span className="text-[10px] text-slate-400 font-mono">
                      {item.start_year}–{item.end_year}
                    </span>
                  </div>

                  <h3 className="text-sm font-bold font-serif text-slate-900 line-clamp-1">
                    {item.topic}
                  </h3>
                  <p className="text-xs text-slate-500 line-clamp-1">
                    {item.objective}
                  </p>

                  <div className="flex items-center gap-4 pt-1 text-[11px] text-slate-500 font-mono">
                    <span className="flex items-center gap-1">
                      <BookOpen className="h-3 w-3 text-indigo-500" />
                      <strong>{item.total_papers}</strong> papers collected
                    </span>
                    <span className="flex items-center gap-1 text-slate-400">
                      <Clock className="h-3 w-3" />
                      {new Date(item.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={(e) => handleDelete(item.id, e)}
                    className="p-2 text-slate-400 hover:text-red-600 rounded hover:bg-slate-100"
                    title="Delete record"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                  <ArrowRight className="h-4 w-4 text-indigo-600" />
                </div>
              </div>
            ))
          )}
        </div>

        <div className="p-3.5 border-t border-slate-200 bg-slate-50 flex items-center justify-end">
          <button onClick={onClose} className="btn-secondary py-1 px-4 text-xs">
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

