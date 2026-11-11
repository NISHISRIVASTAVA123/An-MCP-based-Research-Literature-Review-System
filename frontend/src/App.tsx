import React, { useState, useEffect } from 'react';
import {
  ResearchRequest,
  ResearchRequestCreate,
  SearchStrategy,
  StrategyQuery,
  Paper,
  SearchExecutionSummary,
} from './types';
import {
  createResearchRequest,
  generateSearchStrategy,
  getResearchRequest,
  getSearchStrategy,
  updateSearchStrategy,
  executeSearch,
  getSearchHistory,
} from './services/api';
import { Header } from './components/Header';
import { ResearchForm } from './components/ResearchForm';
import { StrategyEditor } from './components/StrategyEditor';
import { SearchDashboard } from './components/SearchDashboard';
import { PaperModal } from './components/PaperModal';
import { HistoryModal } from './components/HistoryModal';
import { McpModal } from './components/McpModal';
import { AlertCircle } from 'lucide-react';

export function App() {
  const [activeStep, setActiveStep] = useState<'form' | 'strategy' | 'dashboard'>('form');
  const [currentRequest, setCurrentRequest] = useState<ResearchRequest | null>(null);
  const [currentStrategy, setCurrentStrategy] = useState<SearchStrategy | null>(null);
  const [lastExecution, setLastExecution] = useState<SearchExecutionSummary | undefined>(undefined);

  const [selectedPaper, setSelectedPaper] = useState<Paper | null>(null);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [isMcpOpen, setIsMcpOpen] = useState(false);

  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleCreateRequest = async (payload: ResearchRequestCreate) => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      // 1. Create request
      const req = await createResearchRequest(payload);
      setCurrentRequest(req);

      // 2. Generate search strategy
      const strat = await generateSearchStrategy(req.id);
      setCurrentStrategy(strat);

      setActiveStep('strategy');
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to initialize research request.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleExecuteSearch = async (queries?: StrategyQuery[]) => {
    if (!currentRequest) return;
    setIsLoading(true);
    setErrorMsg(null);
    try {
      // 1. If queries were updated, save them
      if (queries && currentStrategy) {
        const updated = await updateSearchStrategy(currentRequest.id, { queries });
        setCurrentStrategy(updated);
      }

      // 2. Execute retrieval pipeline
      const execResult = await executeSearch(currentRequest.id);

      // 3. Reload execution history
      const history = await getSearchHistory(currentRequest.id);
      if (history.length > 0) {
        setLastExecution(history[0]);
      }

      // 4. Reload updated request
      const reloadedReq = await getResearchRequest(currentRequest.id);
      setCurrentRequest(reloadedReq);

      setActiveStep('dashboard');
    } catch (err: any) {
      setErrorMsg(err.message || 'Search execution failed across academic providers.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSaveStrategy = async (updatedQueries: StrategyQuery[]) => {
    if (!currentRequest) return;
    try {
      const updated = await updateSearchStrategy(currentRequest.id, { queries: updatedQueries });
      setCurrentStrategy(updated);
    } catch (err) {
      console.error('Failed to save strategy:', err);
    }
  };

  const handleSelectSavedRequest = async (requestId: string) => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const req = await getResearchRequest(requestId);
      setCurrentRequest(req);

      const strat = await getSearchStrategy(requestId);
      setCurrentStrategy(strat);

      const history = await getSearchHistory(requestId);
      if (history.length > 0) {
        setLastExecution(history[0]);
      }

      if (req.total_papers_count > 0) {
        setActiveStep('dashboard');
      } else if (strat) {
        setActiveStep('strategy');
      } else {
        setActiveStep('form');
      }
    } catch (err: any) {
      setErrorMsg('Failed to reopen saved review.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewReview = () => {
    setCurrentRequest(null);
    setCurrentStrategy(null);
    setLastExecution(undefined);
    setErrorMsg(null);
    setActiveStep('form');
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <Header
        onNewReview={handleNewReview}
        onOpenHistory={() => setIsHistoryOpen(true)}
        onOpenMcp={() => setIsMcpOpen(true)}
      />

      {/* Global Error Banner */}
      {errorMsg && (
        <div className="bg-red-50 border-b border-red-200 px-4 py-3">
          <div className="app-container flex items-center justify-between text-xs text-red-800">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-4 w-4 text-red-600 shrink-0" />
              <span>{errorMsg}</span>
            </div>
            <button
              onClick={() => setErrorMsg(null)}
              className="text-red-600 hover:text-red-900 font-semibold"
            >
              Dismiss
            </button>
          </div>
        </div>
      )}

      {/* Main App Container */}
      <main className="app-container py-8 flex-1">
        {activeStep === 'form' && (
          <ResearchForm
            onSubmit={handleCreateRequest}
            isLoading={isLoading}
          />
        )}

        {activeStep === 'strategy' && currentRequest && currentStrategy && (
          <StrategyEditor
            request={currentRequest}
            strategy={currentStrategy}
            onExecuteSearch={handleExecuteSearch}
            onSaveStrategy={handleSaveStrategy}
            isExecuting={isLoading}
            onBack={() => setActiveStep('form')}
          />
        )}

        {activeStep === 'dashboard' && currentRequest && (
          <SearchDashboard
            request={currentRequest}
            onModifyStrategy={() => setActiveStep('strategy')}
            onSelectPaper={(p) => setSelectedPaper(p)}
            lastExecution={lastExecution}
          />
        )}
      </main>

      {/* Paper Details Modal */}
      <PaperModal
        paper={selectedPaper}
        onClose={() => setSelectedPaper(null)}
      />

      {/* Saved Reviews History Modal */}
      <HistoryModal
        isOpen={isHistoryOpen}
        onClose={() => setIsHistoryOpen(false)}
        onSelectRequest={handleSelectSavedRequest}
      />

      {/* MCP Tools Inspector Modal */}
      <McpModal
        isOpen={isMcpOpen}
        onClose={() => setIsMcpOpen(false)}
      />

      {/* Academic Footer */}
      <footer className="border-t border-slate-200 bg-white py-4 mt-auto">
        <div className="app-container flex flex-col sm:flex-row items-center justify-between gap-2 text-[11px] text-slate-500">
          <div>
            12-Week Capstone Research Project • MCP Multi-Agent Autonomous Literature Review Framework
          </div>
          <div className="flex items-center gap-3">
            <span>OpenAlex</span>
            <span>•</span>
            <span>Semantic Scholar</span>
            <span>•</span>
            <span>Crossref</span>
            <span>•</span>
            <span>arXiv</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

