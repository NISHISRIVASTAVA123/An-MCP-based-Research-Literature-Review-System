import React from 'react';
import { BookOpen, History, Cpu, Sparkles } from 'lucide-react';

interface HeaderProps {
  onNewReview: () => void;
  onOpenHistory: () => void;
  onOpenMcp: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  onNewReview,
  onOpenHistory,
  onOpenMcp,
}) => {
  return (
    <header className="border-b border-slate-200 bg-white sticky top-0 z-30 shadow-xs">
      <div className="app-container py-3.5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-lg bg-indigo-600 flex items-center justify-center text-white shadow-sm">
            <BookOpen className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold tracking-tight text-slate-900 font-serif">
                Autonomous Academic Literature Review
              </h1>
              <span className="badge bg-indigo-50 text-indigo-700 border border-indigo-200 text-xs font-mono">
                Phase 1: Retrieval
              </span>
            </div>
            <p className="text-xs text-slate-500">
              MCP Multi-Agent Research Gap Assessment Framework • B.Tech Capstone
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={onOpenMcp}
            className="btn-secondary text-xs py-2 px-3 flex items-center gap-1.5"
            title="Inspect MCP Tools registered for autonomous agent execution"
          >
            <Cpu className="h-3.5 w-3.5 text-indigo-600" />
            <span>MCP Tools</span>
          </button>

          <button
            onClick={onOpenHistory}
            className="btn-secondary text-xs py-2 px-3 flex items-center gap-1.5"
          >
            <History className="h-3.5 w-3.5 text-slate-600" />
            <span>Review History</span>
          </button>

          <button
            onClick={onNewReview}
            className="btn-primary text-xs py-2 px-3.5 flex items-center gap-1.5 shadow-xs"
          >
            <Sparkles className="h-3.5 w-3.5" />
            <span>New Research Review</span>
          </button>
        </div>
      </div>
    </header>
  );
};

