import React, { useState } from 'react';
import {
  ResearchRequest,
  ResearchRequestCreate,
  SearchStrategy,
  StrategyQuery,
  Paper,
  SearchExecutionSummary,
  EvidenceRecord,
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
import { PhaseRoadmap } from './components/PhaseRoadmap';
import { ResearchForm } from './components/ResearchForm';
import { StrategyEditor } from './components/StrategyEditor';
import { SearchDashboard } from './components/SearchDashboard';
import { ScreeningView } from './components/ScreeningView';
import { EvidenceViewModal } from './components/EvidenceViewModal';
import { PaperModal } from './components/PaperModal';
import { HistoryModal } from './components/HistoryModal';
import { McpModal } from './components/McpModal';
import { AlertCircle, FlaskConical } from 'lucide-react';

export function App() {
  const [activeStep, setActiveStep] = useState<'form' | 'strategy' | 'dashboard' | 'screening'>('form');
  const [currentRequest, setCurrentRequest] = useState<ResearchRequest | null>(null);
  const [currentStrategy, setCurrentStrategy] = useState<SearchStrategy | null>(null);
  const [lastExecution, setLastExecution] = useState<SearchExecutionSummary | undefined>(undefined);

  const [selectedPaper, setSelectedPaper] = useState<Paper | null>(null);
  const [selectedEvidence, setSelectedEvidence] = useState<EvidenceRecord | null>(null);
  const [inspectPaperTitle, setInspectPaperTitle] = useState('');
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [isMcpOpen, setIsMcpOpen] = useState(false);

  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleCreateRequest = async (payload: ResearchRequestCreate) => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      // 1. Create request in SQLite
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

      // 2. Execute retrieval pipeline concurrently across providers
      await executeSearch(currentRequest.id);

      // 3. Reload execution history
      const history = await getSearchHistory(currentRequest.id);
      if (history.length > 0) {
        setLastExecution(history[0]);
      }

      // 4. Reload updated request with paper counts
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
    <div className="app-shell">
      {/* Top Navigation Bar with Step Indicator */}
      <Header
        onNewReview={handleNewReview}
        onOpenHistory={() => setIsHistoryOpen(true)}
        onOpenMcp={() => setIsMcpOpen(true)}
        activeStep={activeStep}
      />

      {/* Global Error Banner */}
      {errorMsg && (
        <div style={{ background: '#fef2f2', borderBottom: '1px solid #fecaca', padding: '0.75rem 1.5rem' }}>
          <div className="app-container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.82rem', color: '#991b1b' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <AlertCircle size={16} color="#ef4444" style={{ flexShrink: 0 }} />
              <span>{errorMsg}</span>
            </div>
            <button
              onClick={() => setErrorMsg(null)}
              style={{ background: 'none', border: 'none', color: '#b91c1c', fontWeight: 700, cursor: 'pointer', fontSize: '0.78rem' }}
            >
              Dismiss
            </button>
          </div>
        </div>
      )}

      {/* Main Two-Column Layout (Sidebar + Work Area) */}
      <div className="two-col-layout">
        {/* Left Sidebar: 12-Week 9-Phase Research Roadmap */}
        <PhaseRoadmap currentActiveStep={activeStep} />

        {/* Right Work Area */}
        <main style={{ padding: '2rem 2.5rem', background: '#f0f2ff', flex: 1, minWidth: 0 }}>
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
              onProceedToScreening={() => setActiveStep('screening')}
            />
          )}

          {activeStep === 'screening' && currentRequest && (
            <ScreeningView
              request={currentRequest}
              onBackToCorpus={() => setActiveStep('dashboard')}
              onInspectEvidence={(ev, title) => {
                setSelectedEvidence(ev);
                setInspectPaperTitle(title);
              }}
            />
          )}
        </main>
      </div>

      {/* Modals */}
      <PaperModal
        paper={selectedPaper}
        onClose={() => setSelectedPaper(null)}
      />

      <EvidenceViewModal
        evidence={selectedEvidence}
        paperTitle={inspectPaperTitle}
        onClose={() => setSelectedEvidence(null)}
      />

      <HistoryModal
        isOpen={isHistoryOpen}
        onClose={() => setIsHistoryOpen(false)}
        onSelectRequest={handleSelectSavedRequest}
      />

      <McpModal
        isOpen={isMcpOpen}
        onClose={() => setIsMcpOpen(false)}
      />

      {/* Academic Footer */}
      <footer style={{ borderTop: '1px solid #e2e8f0', background: '#fff', padding: '0.85rem 1.5rem' }}>
        <div className="app-container" style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: '0.5rem', fontSize: '0.74rem', color: '#64748b' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <FlaskConical size={14} color="#6366f1" />
            <span>12-Week Capstone Research Project • MCP Multi-Agent Autonomous Literature Review Framework</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', fontFamily: 'JetBrains Mono, monospace', fontSize: '0.7rem' }}>
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
