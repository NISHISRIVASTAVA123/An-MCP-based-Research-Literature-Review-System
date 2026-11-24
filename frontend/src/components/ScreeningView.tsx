import React, { useState, useEffect, useRef } from 'react';
import {
  ResearchRequest,
  Paper,
  ScreeningRun,
  ScreeningDecision,
  DocumentStatus,
  EvidenceRecord,
} from '../types';
import {
  listPapers,
  createScreeningRun,
  getScreeningResults,
  overrideScreeningDecision,
  retrievePaperFullText,
  uploadPaperPdf,
  getDocumentStatus,
  extractPaperEvidence,
  getPaperEvidence,
} from '../services/api';
import {
  CheckCircle2,
  AlertTriangle,
  XCircle,
  FileText,
  UploadCloud,
  DownloadCloud,
  Sparkles,
  Search,
  ArrowLeft,
  ArrowRight,
  ChevronDown,
  ChevronUp,
  UserCheck,
  Eye,
  ExternalLink,
  Loader2,
} from 'lucide-react';

interface ScreeningViewProps {
  request: ResearchRequest;
  onBackToCorpus: () => void;
  onInspectEvidence: (evidence: EvidenceRecord, paperTitle: string) => void;
  onProceedToGraph?: () => void;
}

export const ScreeningView: React.FC<ScreeningViewProps> = ({
  request,
  onBackToCorpus,
  onInspectEvidence,
  onProceedToGraph,
}) => {
  const [papers, setPapers] = useState<Paper[]>([]);
  const [screeningRun, setScreeningRun] = useState<ScreeningRun | null>(null);
  const [decisions, setDecisions] = useState<Record<string, ScreeningDecision>>({});
  const [docStatuses, setDocStatuses] = useState<Record<string, DocumentStatus>>({});
  const [evidenceMap, setEvidenceMap] = useState<Record<string, EvidenceRecord>>({});

  const [isLoading, setIsLoading] = useState(true);
  const [isScreening, setIsScreening] = useState(false);
  const [activeTab, setActiveTab] = useState<'all' | 'included' | 'excluded' | 'needs_human_review' | 'has_doc' | 'has_evidence'>('all');
  const [searchFilter, setSearchFilter] = useState('');

  // Processing state maps
  const [retrievingDocs, setRetrievingDocs] = useState<Record<string, boolean>>({});
  const [uploadingDocs, setUploadingDocs] = useState<Record<string, boolean>>({});
  const [extractingEvidence, setExtractingEvidence] = useState<Record<string, boolean>>({});

  // Human override state maps
  const [editingOverride, setEditingOverride] = useState<Record<string, boolean>>({});
  const [overrideSelection, setOverrideSelection] = useState<Record<string, 'included' | 'excluded' | 'needs_human_review'>>({});
  const [overrideNotes, setOverrideNotes] = useState<Record<string, string>>({});
  const [expandedReasons, setExpandedReasons] = useState<Record<string, boolean>>({});

  // File upload input ref mapping
  const fileInputRefs = useRef<Record<string, HTMLInputElement | null>>({});

  // Initial Load: Fetch papers, latest screening decisions, and document statuses
  const loadData = async () => {
    setIsLoading(true);
    try {
      const papersResp = await listPapers(request.id, { page_size: 100 });
      setPapers(papersResp.items);

      // Check for screening decisions
      try {
        const decList = await getScreeningResults(request.id);
        const decMap: Record<string, ScreeningDecision> = {};
        for (const d of decList) {
          decMap[d.paper_id] = d;
        }
        setDecisions(decMap);
      } catch {
        // No screening run yet
      }

      // Check document statuses & evidence for papers
      const docMap: Record<string, DocumentStatus> = {};
      const evMap: Record<string, EvidenceRecord> = {};

      await Promise.all(
        papersResp.items.map(async (p) => {
          try {
            const ds = await getDocumentStatus(p.id);
            docMap[p.id] = ds;
          } catch {
            // Not fetched yet
          }
          try {
            const ev = await getPaperEvidence(p.id);
            if (ev) {
              evMap[p.id] = ev;
            }
          } catch {
            // Not extracted yet
          }
        })
      );

      setDocStatuses(docMap);
      setEvidenceMap(evMap);
    } catch (err) {
      console.error('Failed to load screening data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [request.id]);

  // Trigger automated screening run
  const handleRunScreening = async () => {
    setIsScreening(true);
    try {
      const run = await createScreeningRun(request.id);
      setScreeningRun(run);
      const decList = await getScreeningResults(request.id);
      const decMap: Record<string, ScreeningDecision> = {};
      for (const d of decList) {
        decMap[d.paper_id] = d;
      }
      setDecisions(decMap);
    } catch (err: any) {
      alert(`Screening run failed: ${err.message || 'Unknown error'}`);
    } finally {
      setIsScreening(false);
    }
  };

  // Handle human override submit
  const handleSaveOverride = async (paperId: string) => {
    const decision = decisions[paperId];
    if (!decision) return;

    const newDecision = overrideSelection[paperId] || decision.decision;
    const notes = overrideNotes[paperId] || 'Human researcher override';

    try {
      const updated = await overrideScreeningDecision(paperId, newDecision, notes);
      setDecisions((prev) => ({ ...prev, [paperId]: updated }));
      setEditingOverride((prev) => ({ ...prev, [paperId]: false }));

      // Refresh dec list
      const decList = await getScreeningResults(request.id);
      const decMap: Record<string, ScreeningDecision> = {};
      for (const d of decList) {
        decMap[d.paper_id] = d;
      }
      setDecisions(decMap);
    } catch (err: any) {
      alert(`Failed to save override: ${err.message || 'Unknown error'}`);
    }
  };

  // Retrieve full-text document from OA/arXiv
  const handleRetrieveFullText = async (paperId: string) => {
    setRetrievingDocs((prev) => ({ ...prev, [paperId]: true }));
    try {
      await retrievePaperFullText(paperId);
      const ds = await getDocumentStatus(paperId);
      setDocStatuses((prev) => ({ ...prev, [paperId]: ds }));
    } catch (err: any) {
      alert(`Full-text retrieval failed: ${err.message || 'Unknown error'}`);
    } finally {
      setRetrievingDocs((prev) => ({ ...prev, [paperId]: false }));
    }
  };

  // Upload user PDF for a paper
  const handleFileUpload = async (paperId: string, e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadingDocs((prev) => ({ ...prev, [paperId]: true }));
    try {
      await uploadPaperPdf(paperId, file);
      const ds = await getDocumentStatus(paperId);
      setDocStatuses((prev) => ({ ...prev, [paperId]: ds }));
    } catch (err: any) {
      alert(`PDF upload failed: ${err.message || 'Unknown error'}`);
    } finally {
      setUploadingDocs((prev) => ({ ...prev, [paperId]: false }));
      const inputEl = fileInputRefs.current[paperId];
      if (inputEl) {
        inputEl.value = '';
      }
    }
  };

  // Trigger structured evidence extraction
  const handleExtractEvidence = async (paperId: string) => {
    setExtractingEvidence((prev) => ({ ...prev, [paperId]: true }));
    try {
      const ev = await extractPaperEvidence(paperId);
      setEvidenceMap((prev) => ({ ...prev, [paperId]: ev }));
    } catch (err: any) {
      alert(`Evidence extraction failed: ${err.message || 'Unknown error'}`);
    } finally {
      setExtractingEvidence((prev) => ({ ...prev, [paperId]: false }));
    }
  };

  // Derived metrics
  const totalPapers = papers.length;
  const screenedCount = Object.keys(decisions).length;
  const includedCount = Object.values(decisions).filter((d) => d.decision === 'included').length;
  const excludedCount = Object.values(decisions).filter((d) => d.decision === 'excluded').length;
  const needsReviewCount = Object.values(decisions).filter((d) => d.decision === 'needs_human_review').length;
  const fullTextCount = Object.values(docStatuses).filter((d) => d.has_document).length;
  const evidenceCount = Object.keys(evidenceMap).length;

  // Filter papers
  const filteredPapers = papers.filter((p) => {
    const dec = decisions[p.id];
    const doc = docStatuses[p.id];
    const hasEv = !!evidenceMap[p.id];

    if (activeTab === 'included' && dec?.decision !== 'included') return false;
    if (activeTab === 'excluded' && dec?.decision !== 'excluded') return false;
    if (activeTab === 'needs_human_review' && dec?.decision !== 'needs_human_review') return false;
    if (activeTab === 'has_doc' && !doc?.has_document) return false;
    if (activeTab === 'has_evidence' && !hasEv) return false;

    if (searchFilter.trim()) {
      const q = searchFilter.toLowerCase();
      const matchTitle = p.title.toLowerCase().includes(q);
      const matchAuthors = p.authors?.some((a) => a.toLowerCase().includes(q));
      if (!matchTitle && !matchAuthors) return false;
    }

    return true;
  });

  return (
    <div style={{ maxWidth: 1160, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Top Banner & Title */}
      <div className="card-dark" style={{ padding: '1.75rem 2rem' }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'flex-start', justifyContent: 'space-between', gap: '1rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.4rem' }}>
              <button
                onClick={onBackToCorpus}
                className="btn btn-sm"
                style={{
                  background: 'rgba(255,255,255,0.1)',
                  color: 'rgba(255,255,255,0.85)',
                  padding: '0.3rem 0.65rem',
                  fontSize: '0.74rem',
                  border: '1px solid rgba(255,255,255,0.15)',
                }}
              >
                <ArrowLeft size={13} />
                <span>Corpus View</span>
              </button>
              <span style={{ fontSize: '0.68rem', fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase', color: '#38bdf8' }}>
                Phase 2 · Paper Screening & Structured Evidence Extraction
              </span>
            </div>
            <h2 style={{ fontFamily: 'Sora, sans-serif', fontWeight: 800, fontSize: '1.35rem', color: '#fff', marginBottom: '0.4rem' }}>
              {request.topic}
            </h2>
            <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '0.75rem', fontSize: '0.78rem', color: 'rgba(255,255,255,0.65)' }}>
              <span>Domain: <strong style={{ color: '#fff' }}>{request.domain}</strong></span>
              <span>•</span>
              <span>Years: <strong style={{ color: '#fff' }}>{request.start_year}–{request.end_year}</strong></span>
              <span>•</span>
              <span>Objective: <strong style={{ color: '#fff' }}>{request.objective || 'General review'}</strong></span>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <button
              onClick={handleRunScreening}
              disabled={isScreening || papers.length === 0}
              className="btn btn-primary"
              style={{ padding: '0.6rem 1.25rem', fontSize: '0.86rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
            >
              {isScreening ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  <span>Screening Papers...</span>
                </>
              ) : (
                <>
                  <Sparkles size={16} />
                  <span>{screeningRun || screenedCount > 0 ? 'Re-run Screening' : 'Run Automated Screening'}</span>
                </>
              )}
            </button>

            {onProceedToGraph && (
              <button
                onClick={onProceedToGraph}
                className="btn"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.45rem',
                  fontSize: '0.82rem',
                  fontWeight: 700,
                  background: 'linear-gradient(135deg, #059669 0%, #10b981 100%)',
                  color: '#fff',
                  border: 'none',
                  padding: '0.65rem 1.15rem',
                  borderRadius: '0.5rem',
                  cursor: 'pointer',
                  boxShadow: '0 4px 14px rgba(16,185,129,0.35)',
                }}
              >
                <span>Explore Evidence Graph</span>
                <ArrowRight size={15} />
              </button>
            )}
          </div>
        </div>

        {/* Metric Cards Row */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '0.85rem', marginTop: '1.5rem' }}>
          <div style={{ background: 'rgba(255,255,255,0.06)', borderRadius: '0.65rem', padding: '0.9rem 1.1rem', border: '1px solid rgba(255,255,255,0.08)' }}>
            <div style={{ fontSize: '0.65rem', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.5)', marginBottom: '0.25rem' }}>
              Corpus Papers
            </div>
            <div style={{ fontSize: '1.65rem', fontWeight: 800, fontFamily: 'JetBrains Mono, monospace', color: '#fff' }}>
              {totalPapers}
            </div>
            <div style={{ fontSize: '0.68rem', color: 'rgba(255,255,255,0.4)', marginTop: '0.2rem' }}>
              {screenedCount} screened ({totalPapers > 0 ? Math.round((screenedCount / totalPapers) * 100) : 0}%)
            </div>
          </div>

          <div style={{ background: 'rgba(16,185,129,0.12)', borderRadius: '0.65rem', padding: '0.9rem 1.1rem', border: '1px solid rgba(52,211,153,0.3)' }}>
            <div style={{ fontSize: '0.65rem', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: '#6ee7b7', marginBottom: '0.25rem' }}>
              Included
            </div>
            <div style={{ fontSize: '1.65rem', fontWeight: 800, fontFamily: 'JetBrains Mono, monospace', color: '#a7f3d0' }}>
              {includedCount}
            </div>
            <div style={{ fontSize: '0.68rem', color: '#6ee7b7', marginTop: '0.2rem' }}>
              Passed criteria rules
            </div>
          </div>

          <div style={{ background: 'rgba(239,68,68,0.12)', borderRadius: '0.65rem', padding: '0.9rem 1.1rem', border: '1px solid rgba(248,113,113,0.3)' }}>
            <div style={{ fontSize: '0.65rem', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: '#fca5a5', marginBottom: '0.25rem' }}>
              Excluded
            </div>
            <div style={{ fontSize: '1.65rem', fontWeight: 800, fontFamily: 'JetBrains Mono, monospace', color: '#fecaca' }}>
              {excludedCount}
            </div>
            <div style={{ fontSize: '0.68rem', color: '#fca5a5', marginTop: '0.2rem' }}>
              Failed criteria rules
            </div>
          </div>

          <div style={{ background: 'rgba(245,158,11,0.12)', borderRadius: '0.65rem', padding: '0.9rem 1.1rem', border: '1px solid rgba(251,191,36,0.3)' }}>
            <div style={{ fontSize: '0.65rem', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: '#fde68a', marginBottom: '0.25rem' }}>
              Needs Review
            </div>
            <div style={{ fontSize: '1.65rem', fontWeight: 800, fontFamily: 'JetBrains Mono, monospace', color: '#fef3c7' }}>
              {needsReviewCount}
            </div>
            <div style={{ fontSize: '0.68rem', color: '#fde68a', marginTop: '0.2rem' }}>
              Flagged for triage
            </div>
          </div>

          <div style={{ background: 'rgba(56,189,248,0.12)', borderRadius: '0.65rem', padding: '0.9rem 1.1rem', border: '1px solid rgba(56,189,248,0.3)' }}>
            <div style={{ fontSize: '0.65rem', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: '#7dd3fc', marginBottom: '0.25rem' }}>
              Full Text Ready
            </div>
            <div style={{ fontSize: '1.65rem', fontWeight: 800, fontFamily: 'JetBrains Mono, monospace', color: '#bae6fd' }}>
              {fullTextCount}
            </div>
            <div style={{ fontSize: '0.68rem', color: '#7dd3fc', marginTop: '0.2rem' }}>
              PDF / XML parsed
            </div>
          </div>

          <div style={{ background: 'rgba(168,85,247,0.12)', borderRadius: '0.65rem', padding: '0.9rem 1.1rem', border: '1px solid rgba(192,132,252,0.3)' }}>
            <div style={{ fontSize: '0.65rem', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: '#d8b4fe', marginBottom: '0.25rem' }}>
              Evidence Records
            </div>
            <div style={{ fontSize: '1.65rem', fontWeight: 800, fontFamily: 'JetBrains Mono, monospace', color: '#e9d5ff' }}>
              {evidenceCount}
            </div>
            <div style={{ fontSize: '0.68rem', color: '#d8b4fe', marginTop: '0.2rem' }}>
              Findings & limitations
            </div>
          </div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="card" style={{ padding: '1rem 1.5rem', display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: '1rem' }}>
        {/* Filter Tabs */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
          {[
            { id: 'all', label: 'All Papers', count: totalPapers },
            { id: 'included', label: 'Included', count: includedCount },
            { id: 'excluded', label: 'Excluded', count: excludedCount },
            { id: 'needs_human_review', label: 'Needs Review', count: needsReviewCount },
            { id: 'has_doc', label: 'Full Text Ready', count: fullTextCount },
            { id: 'has_evidence', label: 'Evidence Ready', count: evidenceCount },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              style={{
                padding: '0.4rem 0.8rem',
                borderRadius: '0.45rem',
                fontSize: '0.76rem',
                fontWeight: 600,
                border: '1px solid',
                cursor: 'pointer',
                transition: 'all 0.15s ease',
                background: activeTab === tab.id ? '#4f46e5' : '#f8fafc',
                color: activeTab === tab.id ? '#fff' : '#64748b',
                borderColor: activeTab === tab.id ? '#4338ca' : '#e2e8f0',
              }}
            >
              {tab.label} ({tab.count})
            </button>
          ))}
        </div>

        {/* Search Field */}
        <div style={{ position: 'relative', width: 260 }}>
          <Search size={14} color="#94a3b8" style={{ position: 'absolute', left: 10, top: 10 }} />
          <input
            type="text"
            placeholder="Filter title or author..."
            value={searchFilter}
            onChange={(e) => setSearchFilter(e.target.value)}
            className="input"
            style={{ paddingLeft: '2rem', height: 34, fontSize: '0.78rem' }}
          />
        </div>
      </div>

      {/* Paper List with Screening Decisions & Actions */}
      {isLoading ? (
        <div style={{ textAlign: 'center', padding: '4rem 1rem' }}>
          <Loader2 size={32} className="animate-spin" color="#6366f1" style={{ margin: '0 auto 1rem' }} />
          <p style={{ color: '#64748b', fontSize: '0.88rem' }}>Loading paper corpus & screening records...</p>
        </div>
      ) : filteredPapers.length === 0 ? (
        <div className="card" style={{ padding: '3rem 1.5rem', textAlign: 'center' }}>
          <p style={{ color: '#64748b', fontSize: '0.9rem', marginBottom: '0.5rem' }}>No papers match the selected filter criteria.</p>
          <button
            onClick={() => { setActiveTab('all'); setSearchFilter(''); }}
            className="btn btn-sm btn-secondary"
          >
            Reset Filters
          </button>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {filteredPapers.map((paper) => {
            const dec = decisions[paper.id];
            const doc = docStatuses[paper.id];
            const ev = evidenceMap[paper.id];
            const isEditing = editingOverride[paper.id] || false;
            const isExpandedReason = expandedReasons[paper.id] || false;

            const isRetrieving = retrievingDocs[paper.id] || false;
            const isUploading = uploadingDocs[paper.id] || false;
            const isExtracting = extractingEvidence[paper.id] || false;

            // Decision color classes
            const decisionType = dec?.decision || 'unscreened';
            const sourceDb = paper.sources?.[0]?.source_database || 'academic';

            return (
              <div
                key={paper.id}
                className="card"
                style={{
                  padding: '1.25rem 1.5rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '1rem',
                  borderLeft: `4px solid ${
                    decisionType === 'included'
                      ? '#10b981'
                      : decisionType === 'excluded'
                      ? '#ef4444'
                      : decisionType === 'needs_human_review'
                      ? '#f59e0b'
                      : '#cbd5e1'
                  }`,
                }}
              >
                {/* Header row: Decision badge, Title, Metadata */}
                <div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: '0.75rem', marginBottom: '0.4rem' }}>
                    <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '0.5rem' }}>
                      {/* Decision Badge */}
                      <span
                        style={{
                          fontSize: '0.72rem',
                          fontWeight: 700,
                          padding: '0.2rem 0.65rem',
                          borderRadius: '100px',
                          textTransform: 'uppercase',
                          letterSpacing: '0.05em',
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '0.35rem',
                          background:
                            decisionType === 'included'
                              ? '#ecfdf5'
                              : decisionType === 'excluded'
                              ? '#fef2f2'
                              : decisionType === 'needs_human_review'
                              ? '#fffbeb'
                              : '#f1f5f9',
                          color:
                            decisionType === 'included'
                              ? '#065f46'
                              : decisionType === 'excluded'
                              ? '#991b1b'
                              : decisionType === 'needs_human_review'
                              ? '#92400e'
                              : '#475569',
                          border: `1px solid ${
                            decisionType === 'included'
                              ? '#a7f3d0'
                              : decisionType === 'excluded'
                              ? '#fecaca'
                              : decisionType === 'needs_human_review'
                              ? '#fde68a'
                              : '#cbd5e1'
                          }`,
                        }}
                      >
                        {decisionType === 'included' && <CheckCircle2 size={13} color="#10b981" />}
                        {decisionType === 'excluded' && <XCircle size={13} color="#ef4444" />}
                        {decisionType === 'needs_human_review' && <AlertTriangle size={13} color="#f59e0b" />}
                        <span>{decisionType.replace(/_/g, ' ')}</span>
                      </span>

                      {/* Automated vs Human Override badge */}
                      {dec && dec.is_human_override && (
                        <span
                          style={{
                            fontSize: '0.68rem',
                            fontWeight: 600,
                            padding: '0.15rem 0.5rem',
                            borderRadius: '100px',
                            background: '#eff6ff',
                            color: '#1d4ed8',
                            border: '1px solid #bfdbfe',
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '0.25rem',
                          }}
                        >
                          <UserCheck size={11} />
                          <span>Human Override (Original: {dec.original_decision})</span>
                        </span>
                      )}

                      {/* Confidence Score */}
                      {dec && dec.confidence_score !== undefined && (
                        <span style={{ fontSize: '0.7rem', color: '#64748b' }}>
                          Confidence: <strong style={{ fontFamily: 'JetBrains Mono, monospace' }}>{Math.round(dec.confidence_score * 100)}%</strong>
                        </span>
                      )}
                    </div>

                    {/* Paper source & year info */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.74rem', color: '#64748b' }}>
                      <span style={{ textTransform: 'capitalize', background: '#f1f5f9', padding: '0.15rem 0.45rem', borderRadius: '0.3rem', fontWeight: 600 }}>
                        {sourceDb.replace('_', ' ')}
                      </span>
                      <span>•</span>
                      <span>{paper.publication_year || 'Unknown Year'}</span>
                      {paper.doi && (
                        <>
                          <span>•</span>
                          <a
                            href={`https://doi.org/${paper.doi}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            style={{ color: '#4f46e5', display: 'inline-flex', alignItems: 'center', gap: '0.2rem' }}
                          >
                            <span>DOI</span>
                            <ExternalLink size={10} />
                          </a>
                        </>
                      )}
                    </div>
                  </div>

                  {/* Title */}
                  <h3 style={{ fontSize: '0.98rem', fontWeight: 700, color: '#1e293b', lineHeight: 1.35, marginBottom: '0.35rem' }}>
                    {paper.title}
                  </h3>

                  {/* Authors */}
                  <div style={{ fontSize: '0.76rem', color: '#64748b' }}>
                    {paper.authors && paper.authors.length > 0 ? paper.authors.slice(0, 4).join(', ') + (paper.authors.length > 4 ? ' et al.' : '') : 'Authors not listed'}
                  </div>
                </div>

                {/* Screening Criteria Evaluation Matrix */}
                {dec && (
                  <div style={{ background: '#f8fafc', padding: '0.75rem 1rem', borderRadius: '0.5rem', border: '1px solid #e2e8f0' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
                      <span style={{ fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', color: '#64748b' }}>
                        Evaluated Screening Criteria
                      </span>
                      <button
                        onClick={() => setExpandedReasons((prev) => ({ ...prev, [paper.id]: !isExpandedReason }))}
                        style={{ background: 'none', border: 'none', color: '#4f46e5', fontSize: '0.72rem', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}
                      >
                        <span>{isExpandedReason ? 'Hide details' : 'View explanation'}</span>
                        {isExpandedReason ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                      </button>
                    </div>

                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
                      {(dec.criteria_evaluated || []).map((critKey) => {
                        const passed = (dec.criteria_satisfied || []).includes(critKey);
                        return (
                          <div
                            key={critKey}
                            style={{
                              fontSize: '0.7rem',
                              padding: '0.2rem 0.5rem',
                              borderRadius: '0.35rem',
                              background: passed ? '#ecfdf5' : '#fef2f2',
                              color: passed ? '#047857' : '#b91c1c',
                              border: `1px solid ${passed ? '#a7f3d0' : '#fecaca'}`,
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '0.25rem',
                            }}
                          >
                            <span>{passed ? '✓' : '✗'}</span>
                            <span style={{ textTransform: 'capitalize' }}>{critKey.replace(/_/g, ' ')}</span>
                          </div>
                        );
                      })}
                    </div>

                    {/* Expandable Explanation & Notes */}
                    {isExpandedReason && (
                      <div style={{ marginTop: '0.65rem', paddingTop: '0.65rem', borderTop: '1px solid #e2e8f0', fontSize: '0.76rem', color: '#475569' }}>
                        <div style={{ marginBottom: '0.35rem' }}>
                          <strong style={{ color: '#1e293b' }}>Automated Assessment: </strong>
                          {dec.reason || 'Screened against search objective and constraints.'}
                        </div>
                        {dec.missing_information && dec.missing_information.length > 0 && (
                          <div style={{ color: '#b45309', marginBottom: '0.35rem' }}>
                            <strong>Missing Information: </strong>
                            {dec.missing_information.join(', ')}
                          </div>
                        )}
                        {dec.reviewer_notes && (
                          <div style={{ background: '#f0fdf4', padding: '0.4rem 0.6rem', borderRadius: '0.35rem', border: '1px solid #bbf7d0', color: '#166534', marginTop: '0.35rem' }}>
                            <strong>Reviewer Notes: </strong>
                            {dec.reviewer_notes}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}

                {/* Human Override Controls Bar */}
                {dec && (
                  <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: '0.5rem', paddingTop: '0.35rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      {!isEditing ? (
                        <button
                          onClick={() => {
                            setEditingOverride((prev) => ({ ...prev, [paper.id]: true }));
                            setOverrideSelection((prev) => ({ ...prev, [paper.id]: dec.decision }));
                          }}
                          className="btn btn-sm btn-secondary"
                          style={{ fontSize: '0.72rem', padding: '0.3rem 0.65rem' }}
                        >
                          <UserCheck size={12} />
                          <span>Modify Decision (Override)</span>
                        </button>
                      ) : (
                        <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '0.4rem' }}>
                          <select
                            value={overrideSelection[paper.id] || dec.decision}
                            onChange={(e) => setOverrideSelection((prev) => ({ ...prev, [paper.id]: e.target.value as any }))}
                            style={{ height: 28, fontSize: '0.74rem', padding: '0 0.5rem', borderRadius: '0.3rem', border: '1px solid #cbd5e1' }}
                          >
                            <option value="included">Include</option>
                            <option value="excluded">Exclude</option>
                            <option value="needs_human_review">Needs Review</option>
                          </select>

                          <input
                            type="text"
                            placeholder="Reason for override..."
                            value={overrideNotes[paper.id] ?? ''}
                            onChange={(e) => setOverrideNotes((prev) => ({ ...prev, [paper.id]: e.target.value }))}
                            style={{ height: 28, fontSize: '0.74rem', padding: '0 0.5rem', borderRadius: '0.3rem', border: '1px solid #cbd5e1', width: 180 }}
                          />

                          <button
                            onClick={() => handleSaveOverride(paper.id)}
                            className="btn btn-sm btn-primary"
                            style={{ fontSize: '0.72rem', padding: '0.25rem 0.6rem' }}
                          >
                            Save
                          </button>
                          <button
                            onClick={() => setEditingOverride((prev) => ({ ...prev, [paper.id]: false }))}
                            className="btn btn-sm btn-secondary"
                            style={{ fontSize: '0.72rem', padding: '0.25rem 0.6rem' }}
                          >
                            Cancel
                          </button>
                        </div>
                      )}
                    </div>

                    {/* Right side: Full-Text Document & Evidence Actions */}
                    <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '0.5rem' }}>
                      {/* Document Status Badge */}
                      <span
                        style={{
                          fontSize: '0.7rem',
                          fontWeight: 600,
                          padding: '0.2rem 0.55rem',
                          borderRadius: '0.3rem',
                          background: doc?.has_document ? '#f0fdf4' : '#f8fafc',
                          color: doc?.has_document ? '#15803d' : '#64748b',
                          border: `1px solid ${doc?.has_document ? '#bbf7d0' : '#e2e8f0'}`,
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '0.25rem',
                        }}
                      >
                        <FileText size={11} />
                        <span>
                          {doc?.has_document
                            ? `Full Text (${doc.page_count || 1}p)`
                            : 'Abstract Only'}
                        </span>
                      </span>

                      {/* Full-text Retrieve Button */}
                      {!doc?.has_document && (
                        <button
                          onClick={() => handleRetrieveFullText(paper.id)}
                          disabled={isRetrieving}
                          className="btn btn-sm btn-secondary"
                          style={{ fontSize: '0.72rem', padding: '0.3rem 0.6rem' }}
                          title="Attempt automated download from OpenAlex / arXiv legal open-access endpoints"
                        >
                          {isRetrieving ? (
                            <Loader2 size={12} className="animate-spin" />
                          ) : (
                            <DownloadCloud size={12} />
                          )}
                          <span>Fetch PDF</span>
                        </button>
                      )}

                      {/* PDF Upload Button */}
                      <input
                        type="file"
                        accept=".pdf"
                        ref={(el) => { fileInputRefs.current[paper.id] = el; }}
                        style={{ display: 'none' }}
                        onChange={(e) => handleFileUpload(paper.id, e)}
                      />
                      <button
                        onClick={() => fileInputRefs.current[paper.id]?.click()}
                        disabled={isUploading}
                        className="btn btn-sm btn-secondary"
                        style={{ fontSize: '0.72rem', padding: '0.3rem 0.6rem' }}
                        title="Upload local PDF file for extraction"
                      >
                        {isUploading ? (
                          <Loader2 size={12} className="animate-spin" />
                        ) : (
                          <UploadCloud size={12} />
                        )}
                        <span>Upload PDF</span>
                      </button>

                      {/* Evidence Extraction / Inspection Buttons */}
                      {ev ? (
                        <button
                          onClick={() => onInspectEvidence(ev, paper.title)}
                          className="btn btn-sm"
                          style={{
                            background: '#7c3aed',
                            color: '#fff',
                            fontSize: '0.72rem',
                            padding: '0.3rem 0.75rem',
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '0.3rem',
                            boxShadow: '0 1px 3px rgba(124,58,237,0.3)',
                          }}
                        >
                          <Eye size={12} />
                          <span>Inspect Evidence ({ev.findings?.length || 0}F / {ev.limitations?.length || 0}L)</span>
                        </button>
                      ) : (
                        <button
                          onClick={() => handleExtractEvidence(paper.id)}
                          disabled={isExtracting}
                          className="btn btn-sm btn-primary"
                          style={{ fontSize: '0.72rem', padding: '0.3rem 0.7rem' }}
                        >
                          {isExtracting ? (
                            <>
                              <Loader2 size={12} className="animate-spin" />
                              <span>Extracting...</span>
                            </>
                          ) : (
                            <>
                              <Sparkles size={12} />
                              <span>Extract Evidence</span>
                            </>
                          )}
                        </button>
                      )}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};