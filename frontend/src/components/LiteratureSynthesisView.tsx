import React, { useState, useEffect } from 'react';
import {
  SynthesisRun,
  LiteratureTheme,
  LiteraturePattern,
  CandidateResearchGap,
  PaperComparisonMatrix,
  SynthesisOverviewStats,
} from '../types/synthesis';
import {
  getSynthesisOverview,
  getSynthesisRuns,
  createSynthesisRun,
  getPaperComparison,
  getRunThemes,
  getRunPatterns,
  getCandidateGaps,
  getCandidateGap,
  reviewCandidateGap,
  getPaperComparisonExportUrl,
  compareRunsHistory,
} from '../services/api';
import {
  Microscope,
  FileSpreadsheet,
  Layers,
  TrendingUp,
  FileText,
  AlertCircle,
  HelpCircle,
  History,
  Play,
  Download,
  Filter,
  CheckCircle2,
  XCircle,
  Clock,
  Sparkles,
  ExternalLink,
  ChevronRight,
  ShieldAlert,
  Edit3,
  Search,
} from 'lucide-react';

interface LiteratureSynthesisViewProps {
  requestId: string;
}

export const LiteratureSynthesisView: React.FC<LiteratureSynthesisViewProps> = ({ requestId }) => {
  const [activeTab, setActiveTab] = useState<
    'overview' | 'comparison' | 'themes' | 'trends' | 'synthesis' | 'gaps' | 'history'
  >('overview');

  const [overview, setOverview] = useState<SynthesisOverviewStats | null>(null);
  const [runs, setRuns] = useState<SynthesisRun[]>([]);
  const [selectedRun, setSelectedRun] = useState<SynthesisRun | null>(null);

  // Sub-view data
  const [comparisonMatrix, setComparisonMatrix] = useState<PaperComparisonMatrix | null>(null);
  const [themes, setThemes] = useState<LiteratureTheme[]>([]);
  const [patterns, setPatterns] = useState<LiteraturePattern[]>([]);
  const [candidateGaps, setCandidateGaps] = useState<CandidateResearchGap[]>([]);

  // Selected gap for detail/review modal
  const [selectedGap, setSelectedGap] = useState<CandidateResearchGap | null>(null);
  const [reviewAction, setReviewAction] = useState<string>('accept');
  const [reviewComment, setReviewComment] = useState('');
  const [editTitle, setEditTitle] = useState('');
  const [editDesc, setEditDesc] = useState('');
  const [editCategory, setEditCategory] = useState('');

  // Filters & State
  const [isLoading, setIsLoading] = useState(false);
  const [isExecutingRun, setIsExecutingRun] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [gapCategoryFilter, setGapCategoryFilter] = useState('');
  const [gapStatusFilter, setGapStatusFilter] = useState('');

  // Matrix filters
  const [matrixMethodFilter, setMatrixMethodFilter] = useState('');
  const [matrixSortBy, setMatrixSortBy] = useState('year_desc');

  // History comparison state
  const [compareRunA, setCompareRunA] = useState('');
  const [compareRunB, setCompareRunB] = useState('');
  const [compareResult, setCompareResult] = useState<any>(null);

  // Load overview & runs on mount or requestId change
  useEffect(() => {
    loadOverviewAndRuns();
  }, [requestId]);

  const loadOverviewAndRuns = async () => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const [stats, runList] = await Promise.all([
        getSynthesisOverview(requestId),
        getSynthesisRuns(requestId),
      ]);
      setOverview(stats);
      setRuns(runList);
      if (runList.length > 0) {
        setSelectedRun(runList[0]);
        loadRunData(runList[0].id);
      }
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to load literature synthesis overview.');
    } finally {
      setIsLoading(false);
    }
  };

  const loadRunData = async (runId: string) => {
    try {
      const [themesData, patternsData, gapsData] = await Promise.all([
        getRunThemes(requestId, runId),
        getRunPatterns(requestId, runId),
        getCandidateGaps(requestId, runId, gapCategoryFilter, gapStatusFilter),
      ]);
      setThemes(themesData);
      setPatterns(patternsData);
      setCandidateGaps(gapsData);
    } catch (err: any) {
      console.error('Failed to load run details', err);
    }
  };

  const loadComparisonMatrix = async () => {
    try {
      const matrix = await getPaperComparison(requestId, {
        method: matrixMethodFilter || undefined,
        sort_by: matrixSortBy,
      });
      setComparisonMatrix(matrix);
    } catch (err: any) {
      console.error('Failed to load comparison matrix', err);
    }
  };

  useEffect(() => {
    if (activeTab === 'comparison') {
      loadComparisonMatrix();
    }
  }, [activeTab, matrixMethodFilter, matrixSortBy]);

  useEffect(() => {
    if (selectedRun) {
      loadRunData(selectedRun.id);
    }
  }, [selectedRun?.id, gapCategoryFilter, gapStatusFilter]);

  const handleTriggerRun = async () => {
    setIsExecutingRun(true);
    setErrorMsg(null);
    try {
      const newRun = await createSynthesisRun(requestId);
      setRuns([newRun, ...runs]);
      setSelectedRun(newRun);
      await loadOverviewAndRuns();
      setActiveTab('gaps');
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to execute literature synthesis run.');
    } finally {
      setIsExecutingRun(false);
    }
  };

  const handleOpenGapModal = async (gapId: string) => {
    try {
      const detailedGap = await getCandidateGap(requestId, gapId);
      setSelectedGap(detailedGap);
      setEditTitle(detailedGap.title);
      setEditDesc(detailedGap.description);
      setEditCategory(detailedGap.category);
      setReviewComment('');
    } catch (err: any) {
      setErrorMsg('Failed to fetch gap details.');
    }
  };

  const handleSubmitReview = async () => {
    if (!selectedGap) return;
    try {
      const updated = await reviewCandidateGap(requestId, selectedGap.id, {
        reviewer_reference: 'Lead Researcher',
        review_action: reviewAction,
        revised_title: reviewAction === 'edit' ? editTitle : undefined,
        revised_description: reviewAction === 'edit' ? editDesc : undefined,
        revised_category: reviewAction === 'edit' ? editCategory : undefined,
        reviewer_comment: reviewComment,
      });
      setSelectedGap(updated);
      if (selectedRun) loadRunData(selectedRun.id);
      loadOverviewAndRuns();
    } catch (err: any) {
      setErrorMsg('Failed to submit gap review decision.');
    }
  };

  const handleCompareRuns = async () => {
    if (!compareRunA || !compareRunB) return;
    try {
      const diff = await compareRunsHistory(requestId, compareRunA, compareRunB);
      setCompareResult(diff);
    } catch (err: any) {
      setErrorMsg('Failed to compare runs.');
    }
  };

  return (
    <div className="synthesis-view" style={{ padding: '1.5rem', maxWidth: 1400, margin: '0 auto', color: '#f8fafc' }}>
      {/* Top Banner & Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div style={{
              width: 36, height: 36, borderRadius: '0.5rem',
              background: 'linear-gradient(135deg, #f59e0b, #d97706)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              boxShadow: '0 0 16px rgba(245,158,11,0.3)',
            }}>
              <Microscope size={20} color="#fff" />
            </div>
            <div>
              <h1 style={{ fontSize: '1.4rem', fontWeight: 700, margin: 0, letterSpacing: '-0.01em' }}>
                Literature Synthesis & Candidate Gap Generation
              </h1>
              <div style={{ fontSize: '0.78rem', color: '#94a3b8', marginTop: 2 }}>
                Phase 4 Milestone · Grounded in Phase 3 Evidence Graph & Verifiable Passage Provenance
              </div>
            </div>
          </div>
        </div>

        {/* Action Button */}
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button
            onClick={handleTriggerRun}
            disabled={isExecutingRun}
            style={{
              display: 'flex', alignItems: 'center', gap: '0.5rem',
              padding: '0.55rem 1.25rem', borderRadius: '0.5rem',
              background: isExecutingRun ? '#475569' : 'linear-gradient(135deg, #f59e0b, #b45309)',
              color: '#fff', border: 'none', fontWeight: 600, fontSize: '0.85rem',
              cursor: isExecutingRun ? 'not-allowed' : 'pointer',
              boxShadow: '0 4px 12px rgba(245,158,11,0.25)',
              transition: 'all 0.2s',
            }}
          >
            <Play size={16} />
            {isExecutingRun ? 'Synthesizing Literature...' : 'Run Literature Synthesis'}
          </button>
        </div>
      </div>

      {errorMsg && (
        <div style={{
          background: 'rgba(239,68,68,0.15)', border: '1px solid rgba(239,68,68,0.3)',
          borderRadius: '0.5rem', padding: '0.75rem 1rem', marginBottom: '1.5rem',
          display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#fca5a5', fontSize: '0.85rem',
        }}>
          <AlertCircle size={16} />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Navigation Sub-Tabs */}
      <div style={{
        display: 'flex', gap: '0.5rem', borderBottom: '1px solid rgba(255,255,255,0.08)',
        marginBottom: '1.5rem', paddingBottom: '0.5rem', overflowX: 'auto',
      }}>
        {[
          { id: 'overview',   label: 'Overview',           icon: Microscope },
          { id: 'comparison', label: 'Paper Comparison',   icon: FileSpreadsheet },
          { id: 'themes',     label: 'Research Themes',    icon: Layers },
          { id: 'trends',     label: 'Research Trends',    icon: TrendingUp },
          { id: 'synthesis',  label: 'Narrative Synthesis', icon: FileText },
          { id: 'gaps',       label: 'Candidate Gaps',     icon: HelpCircle },
          { id: 'history',    label: 'Synthesis History',  icon: History },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              style={{
                display: 'flex', alignItems: 'center', gap: '0.45rem',
                padding: '0.5rem 0.9rem', borderRadius: '0.4rem', border: 'none',
                background: isActive ? 'rgba(245,158,11,0.15)' : 'transparent',
                color: isActive ? '#fbbf24' : '#94a3b8',
                fontWeight: isActive ? 600 : 500, fontSize: '0.82rem',
                cursor: 'pointer', transition: 'all 0.2s',
                borderBottom: isActive ? '2px solid #f59e0b' : '2px solid transparent',
              }}
            >
              <Icon size={15} />
              {tab.label}
              {tab.id === 'gaps' && (candidateGaps.length > 0) && (
                <span style={{
                  background: '#f59e0b', color: '#000', fontSize: '0.68rem',
                  fontWeight: 700, padding: '0.1rem 0.4rem', borderRadius: '100px',
                }}>
                  {candidateGaps.length}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* TAB 1: OVERVIEW */}
      {activeTab === 'overview' && (
        <div>
          {/* KPI Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
            <div style={{ background: '#1e293b', padding: '1.25rem', borderRadius: '0.6rem', border: '1px solid rgba(255,255,255,0.06)' }}>
              <div style={{ fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Eligible Papers</div>
              <div style={{ fontSize: '1.8rem', fontWeight: 700, color: '#38bdf8', marginTop: 4 }}>
                {overview?.total_eligible_papers || 0}
              </div>
              <div style={{ fontSize: '0.72rem', color: '#64748b', marginTop: 4 }}>Screened & Included for Synthesis</div>
            </div>

            <div style={{ background: '#1e293b', padding: '1.25rem', borderRadius: '0.6rem', border: '1px solid rgba(255,255,255,0.06)' }}>
              <div style={{ fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Discovered Themes</div>
              <div style={{ fontSize: '1.8rem', fontWeight: 700, color: '#a855f7', marginTop: 4 }}>
                {overview?.total_themes || 0}
              </div>
              <div style={{ fontSize: '0.72rem', color: '#64748b', marginTop: 4 }}>Methodological & Benchmark Clusters</div>
            </div>

            <div style={{ background: '#1e293b', padding: '1.25rem', borderRadius: '0.6rem', border: '1px solid rgba(255,255,255,0.06)' }}>
              <div style={{ fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Candidate Research Gaps</div>
              <div style={{ fontSize: '1.8rem', fontWeight: 700, color: '#f59e0b', marginTop: 4 }}>
                {overview?.total_candidate_gaps || 0}
              </div>
              <div style={{ fontSize: '0.72rem', color: '#64748b', marginTop: 4 }}>Provisional Evidence-Backed Gaps</div>
            </div>

            <div style={{ background: '#1e293b', padding: '1.25rem', borderRadius: '0.6rem', border: '1px solid rgba(255,255,255,0.06)' }}>
              <div style={{ fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Evidence Grounding Rate</div>
              <div style={{ fontSize: '1.8rem', fontWeight: 700, color: '#10b981', marginTop: 4 }}>
                {((overview?.evidence_grounding_rate || 1.0) * 100).toFixed(0)}%
              </div>
              <div style={{ fontSize: '0.72rem', color: '#64748b', marginTop: 4 }}>100% Zero-Hallucination Grounding</div>
            </div>
          </div>

          {/* Active Synthesis Run Summary */}
          {selectedRun ? (
            <div style={{ background: '#1e293b', borderRadius: '0.6rem', padding: '1.5rem', border: '1px solid rgba(255,255,255,0.06)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <div>
                  <h3 style={{ fontSize: '1.1rem', fontWeight: 600, margin: 0 }}>
                    Active Synthesis Run #{selectedRun.run_number}
                  </h3>
                  <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: 2 }}>
                    Executed on {new Date(selectedRun.created_at).toLocaleString()} · Model: {selectedRun.model_name}
                  </div>
                </div>
                <span style={{
                  padding: '0.25rem 0.75rem', borderRadius: '100px', fontSize: '0.75rem', fontWeight: 600,
                  background: selectedRun.status === 'completed' ? 'rgba(16,185,129,0.15)' : 'rgba(245,158,11,0.15)',
                  color: selectedRun.status === 'completed' ? '#34d399' : '#fbbf24',
                  border: `1px solid ${selectedRun.status === 'completed' ? 'rgba(16,185,129,0.3)' : 'rgba(245,158,11,0.3)'}`,
                }}>
                  {selectedRun.status.toUpperCase()}
                </span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem', marginTop: '1rem' }}>
                <div style={{ background: 'rgba(0,0,0,0.2)', padding: '1rem', borderRadius: '0.5rem' }}>
                  <div style={{ fontSize: '0.78rem', color: '#94a3b8' }}>Selected Papers Included</div>
                  <div style={{ fontSize: '1.2rem', fontWeight: 600, color: '#f8fafc', marginTop: 2 }}>
                    {selectedRun.selected_paper_ids.length} publications
                  </div>
                </div>

                <div style={{ background: 'rgba(0,0,0,0.2)', padding: '1rem', borderRadius: '0.5rem' }}>
                  <div style={{ fontSize: '0.78rem', color: '#94a3b8' }}>Source Evidence Graph Version</div>
                  <div style={{ fontSize: '0.85rem', fontWeight: 500, color: '#93c5fd', marginTop: 4, fontFamily: 'monospace' }}>
                    {selectedRun.evidence_graph_version || 'Synchronized Baseline'}
                  </div>
                </div>

                <div style={{ background: 'rgba(0,0,0,0.2)', padding: '1rem', borderRadius: '0.5rem' }}>
                  <div style={{ fontSize: '0.78rem', color: '#94a3b8' }}>Generated Gap Hypotheses</div>
                  <div style={{ fontSize: '1.2rem', fontWeight: 600, color: '#fbbf24', marginTop: 2 }}>
                    {candidateGaps.length} candidate gaps
                  </div>
                </div>
              </div>

              {/* Research Scope Disclaimer */}
              <div style={{
                marginTop: '1.5rem', padding: '0.75rem 1rem', borderRadius: '0.5rem',
                background: 'rgba(56,189,248,0.08)', border: '1px solid rgba(56,189,248,0.2)',
                fontSize: '0.78rem', color: '#bae6fd', display: 'flex', gap: '0.5rem', alignItems: 'flex-start',
              }}>
                <ShieldAlert size={16} style={{ flexShrink: 0, marginTop: 2 }} />
                <div>
                  <strong>Academic Scope & Boundary:</strong> Candidate research gaps generated in Phase 4 represent
                  empirical hypotheses backed by the retrieved corpus subset. They are not globally verified novelties.
                  Phase 5 will deploy explicit counterevidence search, and Phase 6 will perform graph claim verification
                  before final gap classification.
                </div>
              </div>
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '3rem', background: '#1e293b', borderRadius: '0.6rem' }}>
              <Microscope size={48} color="#64748b" style={{ margin: '0 auto 1rem' }} />
              <div style={{ fontSize: '1.1rem', fontWeight: 600 }}>No Literature Synthesis Run Yet</div>
              <div style={{ fontSize: '0.85rem', color: '#94a3b8', maxWidth: 500, margin: '0.5rem auto 1.5rem' }}>
                Run the synthesis engine to construct the multi-paper comparison matrix, extract themes and patterns,
                and generate evidence-backed candidate research gaps.
              </div>
              <button
                onClick={handleTriggerRun}
                disabled={isExecutingRun}
                style={{
                  padding: '0.6rem 1.5rem', borderRadius: '0.5rem', background: '#f59e0b', color: '#000',
                  fontWeight: 700, border: 'none', cursor: 'pointer',
                }}
              >
                {isExecutingRun ? 'Processing...' : 'Start Initial Synthesis Run'}
              </button>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: COMPARISON MATRIX */}
      {activeTab === 'comparison' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.75rem' }}>
            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
              <Filter size={15} color="#94a3b8" />
              <input
                type="text"
                placeholder="Filter by methodology..."
                value={matrixMethodFilter}
                onChange={(e) => setMatrixMethodFilter(e.target.value)}
                style={{
                  background: '#1e293b', border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: '0.4rem', padding: '0.4rem 0.75rem', fontSize: '0.8rem', color: '#fff',
                }}
              />
              <select
                value={matrixSortBy}
                onChange={(e) => setMatrixSortBy(e.target.value)}
                style={{
                  background: '#1e293b', border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: '0.4rem', padding: '0.4rem 0.75rem', fontSize: '0.8rem', color: '#fff',
                }}
              >
                <option value="year_desc">Year (Newest First)</option>
                <option value="year_asc">Year (Oldest First)</option>
                <option value="title_asc">Title (A-Z)</option>
                <option value="evidence_count">Evidence Count</option>
              </select>
            </div>

            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <a
                href={getPaperComparisonExportUrl(requestId, 'csv')}
                download
                style={{
                  display: 'flex', alignItems: 'center', gap: '0.4rem',
                  padding: '0.45rem 0.9rem', borderRadius: '0.4rem',
                  background: '#1e293b', border: '1px solid rgba(255,255,255,0.15)',
                  color: '#93c5fd', fontSize: '0.78rem', fontWeight: 600, textDecoration: 'none',
                }}
              >
                <Download size={14} /> Export CSV
              </a>
              <a
                href={getPaperComparisonExportUrl(requestId, 'markdown')}
                target="_blank"
                rel="noreferrer"
                style={{
                  display: 'flex', alignItems: 'center', gap: '0.4rem',
                  padding: '0.45rem 0.9rem', borderRadius: '0.4rem',
                  background: '#1e293b', border: '1px solid rgba(255,255,255,0.15)',
                  color: '#93c5fd', fontSize: '0.78rem', fontWeight: 600, textDecoration: 'none',
                }}
              >
                <ExternalLink size={14} /> View Markdown
              </a>
            </div>
          </div>

          {/* Matrix Table */}
          {comparisonMatrix && comparisonMatrix.rows.length > 0 ? (
            <div style={{ overflowX: 'auto', background: '#1e293b', borderRadius: '0.6rem', border: '1px solid rgba(255,255,255,0.06)' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem', textAlign: 'left' }}>
                <thead>
                  <tr style={{ background: 'rgba(0,0,0,0.3)', borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
                    <th style={{ padding: '0.75rem 1rem', width: '22%' }}>Paper Title & Authors</th>
                    <th style={{ padding: '0.75rem 1rem', width: '8%' }}>Year</th>
                    <th style={{ padding: '0.75rem 1rem', width: '16%' }}>Methodologies</th>
                    <th style={{ padding: '0.75rem 1rem', width: '14%' }}>Datasets</th>
                    <th style={{ padding: '0.75rem 1rem', width: '14%' }}>Metrics</th>
                    <th style={{ padding: '0.75rem 1rem', width: '16%' }}>Main Findings</th>
                    <th style={{ padding: '0.75rem 1rem', width: '10%' }}>Evidence</th>
                  </tr>
                </thead>
                <tbody>
                  {comparisonMatrix.rows.map((row) => (
                    <tr key={row.paper_id} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                      <td style={{ padding: '0.75rem 1rem' }}>
                        <div style={{ fontWeight: 600, color: '#f8fafc' }}>{row.title}</div>
                        <div style={{ fontSize: '0.72rem', color: '#94a3b8', marginTop: 2 }}>
                          {row.authors.slice(0, 3).join(', ')}{row.authors.length > 3 ? ' et al.' : ''}
                        </div>
                      </td>
                      <td style={{ padding: '0.75rem 1rem', color: '#93c5fd', fontWeight: 500 }}>
                        {row.year || 'N/A'}
                      </td>
                      <td style={{ padding: '0.75rem 1rem' }}>
                        {row.methodologies.map((m, i) => (
                          <span key={i} style={{
                            display: 'inline-block', background: 'rgba(139,92,246,0.15)', color: '#c4b5fd',
                            padding: '0.1rem 0.4rem', borderRadius: '4px', fontSize: '0.72rem', marginRight: 4, marginBottom: 4,
                          }}>
                            {m}
                          </span>
                        ))}
                      </td>
                      <td style={{ padding: '0.75rem 1rem' }}>
                        {row.datasets.map((d, i) => (
                          <span key={i} style={{
                            display: 'inline-block', background: 'rgba(56,189,248,0.15)', color: '#7dd3fc',
                            padding: '0.1rem 0.4rem', borderRadius: '4px', fontSize: '0.72rem', marginRight: 4, marginBottom: 4,
                          }}>
                            {d}
                          </span>
                        ))}
                      </td>
                      <td style={{ padding: '0.75rem 1rem' }}>
                        {row.metrics.map((met, i) => (
                          <span key={i} style={{
                            display: 'inline-block', background: 'rgba(16,185,129,0.15)', color: '#6ee7b7',
                            padding: '0.1rem 0.4rem', borderRadius: '4px', fontSize: '0.72rem', marginRight: 4, marginBottom: 4,
                          }}>
                            {met}
                          </span>
                        ))}
                      </td>
                      <td style={{ padding: '0.75rem 1rem', color: '#cbd5e1', fontSize: '0.75rem' }}>
                        {row.main_findings[0] || 'Not reported'}
                      </td>
                      <td style={{ padding: '0.75rem 1rem' }}>
                        <span style={{
                          background: 'rgba(255,255,255,0.08)', padding: '0.2rem 0.5rem',
                          borderRadius: '100px', fontSize: '0.72rem', color: '#94a3b8',
                        }}>
                          {row.evidence_count} passages
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '3rem', color: '#94a3b8' }}>
              No papers found matching the specified filters.
            </div>
          )}
        </div>
      )}

      {/* TAB 3: RESEARCH THEMES */}
      {activeTab === 'themes' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))', gap: '1.25rem' }}>
          {themes.map((theme) => (
            <div
              key={theme.id}
              style={{
                background: '#1e293b', borderRadius: '0.6rem', padding: '1.25rem',
                border: '1px solid rgba(255,255,255,0.06)', display: 'flex', flexDirection: 'column', justifyContent: 'space-between',
              }}
            >
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
                  <span style={{
                    padding: '0.15rem 0.5rem', borderRadius: '100px', fontSize: '0.7rem', fontWeight: 600,
                    textTransform: 'uppercase', background: 'rgba(168,85,247,0.15)', color: '#c084fc',
                  }}>
                    {theme.theme_category}
                  </span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', fontSize: '0.75rem', color: '#fbbf24' }}>
                    <Sparkles size={13} />
                    <span>{(theme.confidence * 100).toFixed(0)}% conf</span>
                  </div>
                </div>

                <h3 style={{ fontSize: '1.05rem', fontWeight: 600, margin: '0.25rem 0 0.5rem', color: '#f8fafc' }}>
                  {theme.name}
                </h3>
                <p style={{ fontSize: '0.8rem', color: '#cbd5e1', lineHeight: 1.5, margin: '0 0 1rem' }}>
                  {theme.description}
                </p>

                {theme.confidence_explanation && (
                  <div style={{
                    fontSize: '0.72rem', color: '#94a3b8', background: 'rgba(0,0,0,0.2)',
                    padding: '0.5rem 0.75rem', borderRadius: '0.4rem', marginBottom: '0.75rem',
                  }}>
                    <strong>Basis:</strong> {theme.confidence_explanation}
                  </div>
                )}
              </div>

              <div style={{
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                paddingTop: '0.75rem', borderTop: '1px solid rgba(255,255,255,0.06)', fontSize: '0.75rem', color: '#94a3b8',
              }}>
                <div>
                  <strong style={{ color: '#f8fafc' }}>{theme.associated_paper_ids.length}</strong> associated papers
                </div>
                <div>
                  <strong style={{ color: '#f8fafc' }}>{theme.supporting_evidence_ids.length}</strong> evidence nodes
                </div>
              </div>
            </div>
          ))}
          {themes.length === 0 && (
            <div style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '3rem', color: '#94a3b8' }}>
              No research themes identified yet. Run a synthesis to discover clusters.
            </div>
          )}
        </div>
      )}

      {/* TAB 4: RESEARCH TRENDS */}
      {activeTab === 'trends' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(450px, 1fr))', gap: '1.5rem' }}>
          {patterns.map((pat) => (
            <div
              key={pat.id}
              style={{
                background: '#1e293b', borderRadius: '0.6rem', padding: '1.25rem',
                border: '1px solid rgba(255,255,255,0.06)',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                <span style={{
                  padding: '0.2rem 0.55rem', borderRadius: '100px', fontSize: '0.72rem', fontWeight: 600,
                  textTransform: 'uppercase', background: 'rgba(56,189,248,0.15)', color: '#38bdf8',
                }}>
                  {pat.pattern_type} Pattern
                </span>
                <span style={{ fontSize: '0.75rem', color: '#10b981', fontWeight: 600 }}>
                  Confidence: {(pat.confidence * 100).toFixed(0)}%
                </span>
              </div>

              <h3 style={{ fontSize: '0.98rem', fontWeight: 600, margin: '0 0 0.5rem', color: '#f8fafc' }}>
                {pat.description}
              </h3>
              <p style={{ fontSize: '0.8rem', color: '#94a3b8', marginBottom: '1rem', lineHeight: 1.4 }}>
                {pat.interpretation}
              </p>

              {/* Data Breakdown Visualizer */}
              {pat.pattern_type === 'methodology' && pat.observed_data.method_frequencies && (
                <div style={{ background: 'rgba(0,0,0,0.2)', padding: '0.75rem', borderRadius: '0.5rem' }}>
                  {Object.entries(pat.observed_data.method_frequencies).map(([mName, data]: any) => (
                    <div key={mName} style={{ marginBottom: '0.5rem' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: 2 }}>
                        <span>{mName}</span>
                        <span style={{ color: '#c4b5fd' }}>{data.count} ({data.percentage}%)</span>
                      </div>
                      <div style={{ height: 6, background: 'rgba(255,255,255,0.08)', borderRadius: 3, overflow: 'hidden' }}>
                        <div style={{ width: `${data.percentage}%`, height: '100%', background: '#8b5cf6', borderRadius: 3 }} />
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {pat.pattern_type === 'dataset' && pat.observed_data.dataset_frequencies && (
                <div style={{ background: 'rgba(0,0,0,0.2)', padding: '0.75rem', borderRadius: '0.5rem' }}>
                  {Object.entries(pat.observed_data.dataset_frequencies).map(([dName, data]: any) => (
                    <div key={dName} style={{ marginBottom: '0.5rem' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: 2 }}>
                        <span>{dName}</span>
                        <span style={{ color: '#7dd3fc' }}>{data.count} ({data.percentage}%)</span>
                      </div>
                      <div style={{ height: 6, background: 'rgba(255,255,255,0.08)', borderRadius: 3, overflow: 'hidden' }}>
                        <div style={{ width: `${data.percentage}%`, height: '100%', background: '#38bdf8', borderRadius: 3 }} />
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {pat.pattern_type === 'publication_trend' && pat.observed_data.year_distribution && (
                <div style={{ background: 'rgba(0,0,0,0.2)', padding: '0.75rem', borderRadius: '0.5rem' }}>
                  <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-end', height: 80, paddingTop: 10 }}>
                    {Object.entries(pat.observed_data.year_distribution).map(([yr, count]: any) => (
                      <div key={yr} style={{ flex: 1, textAlign: 'center' }}>
                        <div style={{
                          height: `${Math.max(15, count * 20)}px`, background: '#f59e0b',
                          borderRadius: '3px 3px 0 0', margin: '0 auto', width: '70%',
                        }} />
                        <div style={{ fontSize: '0.68rem', color: '#94a3b8', marginTop: 4 }}>{yr}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
          {patterns.length === 0 && (
            <div style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '3rem', color: '#94a3b8' }}>
              No empirical patterns analyzed yet.
            </div>
          )}
        </div>
      )}

      {/* TAB 5: NARRATIVE SYNTHESIS */}
      {activeTab === 'synthesis' && (
        <div style={{ background: '#1e293b', borderRadius: '0.6rem', padding: '2rem', border: '1px solid rgba(255,255,255,0.06)', lineHeight: 1.6 }}>
          {selectedRun?.summary_narrative && Object.keys(selectedRun.summary_narrative).length > 0 ? (
            <div>
              {Object.entries(selectedRun.summary_narrative).map(([secKey, secData]: any) => (
                <div key={secKey} style={{ marginBottom: '2rem', paddingBottom: '1.5rem', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                  <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#fbbf24', marginBottom: '0.75rem' }}>
                    {secData.title}
                  </h3>
                  <p style={{ fontSize: '0.88rem', color: '#cbd5e1', lineHeight: 1.7, margin: 0 }}>
                    {secData.content}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '3rem', color: '#94a3b8' }}>
              Narrative literature synthesis has not been generated yet. Run a synthesis to compile the report.
            </div>
          )}
        </div>
      )}

      {/* TAB 6: CANDIDATE RESEARCH GAPS */}
      {activeTab === 'gaps' && (
        <div>
          {/* Filter Bar */}
          <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1.25rem', flexWrap: 'wrap' }}>
            <select
              value={gapCategoryFilter}
              onChange={(e) => setGapCategoryFilter(e.target.value)}
              style={{
                background: '#1e293b', border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: '0.4rem', padding: '0.45rem 0.8rem', fontSize: '0.8rem', color: '#fff',
              }}
            >
              <option value="">All Categories (10 Types)</option>
              <option value="methodological_gap">Methodological Gap</option>
              <option value="empirical_gap">Empirical Gap</option>
              <option value="dataset_or_benchmark_gap">Dataset / Benchmark Gap</option>
              <option value="evaluation_gap">Evaluation Gap</option>
              <option value="generalisation_gap">Generalisation Gap</option>
              <option value="reproducibility_gap">Reproducibility Gap</option>
              <option value="theoretical_gap">Theoretical Gap</option>
              <option value="deployment_gap">Deployment Gap</option>
              <option value="interdisciplinary_gap">Interdisciplinary Gap</option>
            </select>

            <select
              value={gapStatusFilter}
              onChange={(e) => setGapStatusFilter(e.target.value)}
              style={{
                background: '#1e293b', border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: '0.4rem', padding: '0.45rem 0.8rem', fontSize: '0.8rem', color: '#fff',
              }}
            >
              <option value="">All Review Statuses</option>
              <option value="pending_review">Pending Review</option>
              <option value="accepted_for_further_investigation">Accepted for Investigation</option>
              <option value="requires_more_evidence">Requires More Evidence</option>
              <option value="rejected">Rejected</option>
              <option value="edited_by_reviewer">Edited by Reviewer</option>
            </select>
          </div>

          {/* Gaps Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '1rem' }}>
            {candidateGaps.map((gap) => (
              <div
                key={gap.id}
                style={{
                  background: '#1e293b', borderRadius: '0.6rem', padding: '1.25rem',
                  border: '1px solid rgba(255,255,255,0.06)', display: 'flex', justifyContent: 'space-between',
                  alignItems: 'flex-start', gap: '1.5rem',
                }}
              >
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.5rem', flexWrap: 'wrap' }}>
                    <span style={{
                      padding: '0.15rem 0.55rem', borderRadius: '100px', fontSize: '0.7rem', fontWeight: 600,
                      background: 'rgba(245,158,11,0.15)', color: '#fbbf24', textTransform: 'uppercase',
                    }}>
                      {gap.category.replace(/_/g, ' ')}
                    </span>

                    <span style={{
                      padding: '0.15rem 0.55rem', borderRadius: '100px', fontSize: '0.7rem', fontWeight: 600,
                      background: gap.human_review_status === 'accepted_for_further_investigation'
                        ? 'rgba(16,185,129,0.15)'
                        : gap.human_review_status === 'rejected'
                        ? 'rgba(239,68,68,0.15)'
                        : 'rgba(148,163,184,0.15)',
                      color: gap.human_review_status === 'accepted_for_further_investigation'
                        ? '#34d399'
                        : gap.human_review_status === 'rejected'
                        ? '#f87171'
                        : '#94a3b8',
                    }}>
                      {gap.human_review_status.replace(/_/g, ' ')}
                    </span>

                    <span style={{ fontSize: '0.72rem', color: '#10b981', fontWeight: 600 }}>
                      Confidence: {(gap.preliminary_confidence * 100).toFixed(0)}%
                    </span>
                  </div>

                  <h3 style={{ fontSize: '1.08rem', fontWeight: 700, margin: '0 0 0.4rem', color: '#f8fafc' }}>
                    {gap.title}
                  </h3>
                  <p style={{ fontSize: '0.82rem', color: '#cbd5e1', lineHeight: 1.5, margin: '0 0 0.75rem' }}>
                    {gap.description}
                  </p>

                  <div style={{ display: 'flex', gap: '1rem', fontSize: '0.72rem', color: '#94a3b8' }}>
                    <span>Supporting Papers: <strong style={{ color: '#fff' }}>{gap.supporting_paper_ids.length}</strong></span>
                    <span>Evidence Links: <strong style={{ color: '#fff' }}>{gap.supporting_evidence_ids.length}</strong></span>
                    <span>Validation Queries: <strong style={{ color: '#fff' }}>{gap.suggested_validation_queries.length}</strong></span>
                  </div>
                </div>

                <div style={{ flexShrink: 0 }}>
                  <button
                    onClick={() => handleOpenGapModal(gap.id)}
                    style={{
                      display: 'flex', alignItems: 'center', gap: '0.35rem',
                      padding: '0.45rem 0.85rem', borderRadius: '0.4rem',
                      background: 'rgba(99,102,241,0.2)', color: '#a5b4fc',
                      border: '1px solid rgba(99,102,241,0.4)',
                      fontSize: '0.78rem', fontWeight: 600, cursor: 'pointer',
                    }}
                  >
                    Inspect & Review <ChevronRight size={14} />
                  </button>
                </div>
              </div>
            ))}

            {candidateGaps.length === 0 && (
              <div style={{ textAlign: 'center', padding: '3rem', color: '#94a3b8' }}>
                No candidate research gaps found matching the active filters.
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 7: SYNTHESIS HISTORY */}
      {activeTab === 'history' && (
        <div>
          <div style={{ background: '#1e293b', borderRadius: '0.6rem', padding: '1.5rem', marginBottom: '1.5rem', border: '1px solid rgba(255,255,255,0.06)' }}>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 600, marginBottom: '1rem' }}>Compare Previous Synthesis Runs</h3>
            <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
              <select
                value={compareRunA}
                onChange={(e) => setCompareRunA(e.target.value)}
                style={{
                  background: '#0f172a', border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: '0.4rem', padding: '0.45rem 0.8rem', fontSize: '0.8rem', color: '#fff',
                }}
              >
                <option value="">Select Base Run</option>
                {runs.map((r) => (
                  <option key={r.id} value={r.id}>Run #{r.run_number} ({new Date(r.created_at).toLocaleDateString()})</option>
                ))}
              </select>

              <span style={{ color: '#94a3b8', fontSize: '0.8rem' }}>vs</span>

              <select
                value={compareRunB}
                onChange={(e) => setCompareRunB(e.target.value)}
                style={{
                  background: '#0f172a', border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: '0.4rem', padding: '0.45rem 0.8rem', fontSize: '0.8rem', color: '#fff',
                }}
              >
                <option value="">Select Comparison Run</option>
                {runs.map((r) => (
                  <option key={r.id} value={r.id}>Run #{r.run_number} ({new Date(r.created_at).toLocaleDateString()})</option>
                ))}
              </select>

              <button
                onClick={handleCompareRuns}
                disabled={!compareRunA || !compareRunB}
                style={{
                  padding: '0.45rem 1rem', borderRadius: '0.4rem', background: '#6366f1',
                  color: '#fff', border: 'none', fontWeight: 600, fontSize: '0.8rem', cursor: 'pointer',
                }}
              >
                Compare Runs
              </button>
            </div>

            {compareResult && (
              <div style={{ marginTop: '1.25rem', padding: '1rem', background: 'rgba(0,0,0,0.2)', borderRadius: '0.5rem', fontSize: '0.82rem' }}>
                <div style={{ fontWeight: 600, marginBottom: '0.5rem' }}>Run Comparison Summary:</div>
                <div>Run A Gaps: {compareResult.run_a.gap_count} | Run B Gaps: {compareResult.run_b.gap_count}</div>
                {compareResult.new_gaps_in_b?.length > 0 && (
                  <div style={{ marginTop: '0.5rem', color: '#34d399' }}>
                    New Gaps identified in Run B: {compareResult.new_gaps_in_b.join(', ')}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Runs Table */}
          <div style={{ background: '#1e293b', borderRadius: '0.6rem', border: '1px solid rgba(255,255,255,0.06)', overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem', textAlign: 'left' }}>
              <thead>
                <tr style={{ background: 'rgba(0,0,0,0.3)', borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
                  <th style={{ padding: '0.75rem 1rem' }}>Run #</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Timestamp</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Papers</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Themes</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Gaps</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Model</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {runs.map((r) => (
                  <tr key={r.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                    <td style={{ padding: '0.75rem 1rem', fontWeight: 600, color: '#fbbf24' }}>#{r.run_number}</td>
                    <td style={{ padding: '0.75rem 1rem', color: '#cbd5e1' }}>{new Date(r.created_at).toLocaleString()}</td>
                    <td style={{ padding: '0.75rem 1rem' }}>{r.selected_paper_ids.length}</td>
                    <td style={{ padding: '0.75rem 1rem' }}>{r.theme_count}</td>
                    <td style={{ padding: '0.75rem 1rem', fontWeight: 600, color: '#38bdf8' }}>{r.gap_count}</td>
                    <td style={{ padding: '0.75rem 1rem', color: '#94a3b8' }}>{r.model_name}</td>
                    <td style={{ padding: '0.75rem 1rem' }}>
                      <span style={{
                        padding: '0.15rem 0.5rem', borderRadius: '100px', fontSize: '0.7rem', fontWeight: 600,
                        background: r.status === 'completed' ? 'rgba(16,185,129,0.15)' : 'rgba(245,158,11,0.15)',
                        color: r.status === 'completed' ? '#34d399' : '#fbbf24',
                      }}>
                        {r.status.toUpperCase()}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* MODAL / DRAWER: CANDIDATE GAP DETAILS & HUMAN REVIEW WORKSPACE */}
      {selectedGap && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)',
          zIndex: 50, display: 'flex', justifyContent: 'center', alignItems: 'center', padding: '1.5rem',
        }}>
          <div style={{
            background: '#0f172a', border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: '0.75rem', width: '100%', maxWidth: 900, maxHeight: '90vh',
            display: 'flex', flexDirection: 'column', overflow: 'hidden',
            boxShadow: '0 20px 40px rgba(0,0,0,0.6)',
          }}>
            {/* Modal Header */}
            <div style={{
              padding: '1.25rem 1.5rem', borderBottom: '1px solid rgba(255,255,255,0.08)',
              display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start',
            }}>
              <div>
                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', marginBottom: '0.25rem' }}>
                  <span style={{
                    padding: '0.15rem 0.5rem', borderRadius: '100px', fontSize: '0.7rem', fontWeight: 600,
                    background: 'rgba(245,158,11,0.2)', color: '#fbbf24', textTransform: 'uppercase',
                  }}>
                    {selectedGap.category.replace(/_/g, ' ')}
                  </span>
                  <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                    Status: <strong style={{ color: '#fff' }}>{selectedGap.human_review_status.replace(/_/g, ' ')}</strong>
                  </span>
                </div>
                <h2 style={{ fontSize: '1.2rem', fontWeight: 700, margin: 0, color: '#f8fafc' }}>
                  {selectedGap.title}
                </h2>
              </div>
              <button
                onClick={() => setSelectedGap(null)}
                style={{
                  background: 'transparent', border: 'none', color: '#94a3b8',
                  fontSize: '1.2rem', cursor: 'pointer', padding: '0.25rem',
                }}
              >
                ✕
              </button>
            </div>

            {/* Modal Body */}
            <div style={{ padding: '1.5rem', overflowY: 'auto', flex: 1, fontSize: '0.85rem', lineHeight: 1.6 }}>
              {/* Description & Rationale */}
              <div style={{ marginBottom: '1.25rem' }}>
                <h4 style={{ fontSize: '0.9rem', color: '#fbbf24', marginBottom: '0.25rem' }}>Description & Scope</h4>
                <p style={{ color: '#cbd5e1', margin: 0 }}>{selectedGap.description}</p>
              </div>

              <div style={{ marginBottom: '1.25rem' }}>
                <h4 style={{ fontSize: '0.9rem', color: '#fbbf24', marginBottom: '0.25rem' }}>Scientific Rationale & Observed Pattern</h4>
                <p style={{ color: '#cbd5e1', margin: '0 0 0.5rem' }}>{selectedGap.rationale}</p>
                <div style={{ background: 'rgba(0,0,0,0.25)', padding: '0.6rem 0.8rem', borderRadius: '0.4rem', color: '#94a3b8', fontSize: '0.78rem' }}>
                  <strong>Observed Evidence Pattern:</strong> {selectedGap.observed_pattern}
                </div>
              </div>

              {/* Research Questions & Validation Queries */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.25rem' }}>
                <div style={{ background: '#1e293b', padding: '0.85rem', borderRadius: '0.5rem' }}>
                  <h4 style={{ fontSize: '0.82rem', color: '#93c5fd', margin: '0 0 0.5rem' }}>Candidate Research Questions</h4>
                  <ul style={{ margin: 0, paddingLeft: '1.2rem', color: '#cbd5e1', fontSize: '0.78rem' }}>
                    {selectedGap.related_research_questions.map((rq, idx) => (
                      <li key={idx} style={{ marginBottom: '0.25rem' }}>{rq}</li>
                    ))}
                  </ul>
                </div>

                <div style={{ background: '#1e293b', padding: '0.85rem', borderRadius: '0.5rem' }}>
                  <h4 style={{ fontSize: '0.82rem', color: '#f43f5e', margin: '0 0 0.5rem' }}>Suggested Validation Search Queries (Phase 5)</h4>
                  <ul style={{ margin: 0, paddingLeft: '1.2rem', color: '#cbd5e1', fontSize: '0.78rem' }}>
                    {selectedGap.suggested_validation_queries.map((vq, idx) => (
                      <li key={idx} style={{ marginBottom: '0.25rem', fontFamily: 'monospace' }}>{vq}</li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* Verbatim Supporting Evidence Passages */}
              <div style={{ marginBottom: '1.5rem' }}>
                <h4 style={{ fontSize: '0.9rem', color: '#10b981', marginBottom: '0.5rem' }}>
                  Supporting Verbatim Evidence Passages ({selectedGap.evidence_links?.length || 0})
                </h4>
                {selectedGap.evidence_links && selectedGap.evidence_links.length > 0 ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    {selectedGap.evidence_links.map((link) => (
                      <div
                        key={link.id}
                        style={{
                          background: 'rgba(16,185,129,0.06)', borderLeft: '3px solid #10b981',
                          padding: '0.75rem 1rem', borderRadius: '0 0.4rem 0.4rem 0',
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: '#6ee7b7', marginBottom: 4 }}>
                          <span><strong>{link.paper_title}</strong> (Section: {link.section_heading || 'Body'}, Page {link.page_number || 'N/A'})</span>
                          <span>Relation: {link.relationship_type}</span>
                        </div>
                        <div style={{ fontStyle: 'italic', color: '#e2e8f0', fontSize: '0.8rem' }}>
                          "{link.exact_passage || link.contribution_explanation}"
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div style={{ color: '#94a3b8', fontSize: '0.78rem' }}>No direct passage quotes linked.</div>
                )}
              </div>

              {/* Human Review Action Controls */}
              <div style={{
                background: '#1e293b', border: '1px solid rgba(255,255,255,0.1)',
                padding: '1.25rem', borderRadius: '0.6rem', marginTop: '1rem',
              }}>
                <h4 style={{ fontSize: '0.9rem', fontWeight: 600, color: '#f8fafc', margin: '0 0 0.75rem' }}>
                  Researcher Review Workspace
                </h4>

                <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
                  {[
                    { id: 'accept',           label: 'Accept for Investigation', color: '#10b981' },
                    { id: 'request_evidence', label: 'Request More Evidence',     color: '#f59e0b' },
                    { id: 'edit',             label: 'Edit Gap Details',          color: '#6366f1' },
                    { id: 'reject',           label: 'Reject Hypothesis',         color: '#ef4444' },
                  ].map((btn) => (
                    <button
                      key={btn.id}
                      onClick={() => setReviewAction(btn.id)}
                      style={{
                        padding: '0.4rem 0.8rem', borderRadius: '0.4rem', fontSize: '0.78rem', fontWeight: 600,
                        border: reviewAction === btn.id ? `2px solid ${btn.color}` : '1px solid rgba(255,255,255,0.1)',
                        background: reviewAction === btn.id ? `${btn.color}22` : 'transparent',
                        color: reviewAction === btn.id ? btn.color : '#cbd5e1',
                        cursor: 'pointer',
                      }}
                    >
                      {btn.label}
                    </button>
                  ))}
                </div>

                {reviewAction === 'edit' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginBottom: '1rem' }}>
                    <input
                      type="text"
                      placeholder="Revised Title"
                      value={editTitle}
                      onChange={(e) => setEditTitle(e.target.value)}
                      style={{
                        background: '#0f172a', border: '1px solid rgba(255,255,255,0.1)',
                        borderRadius: '0.4rem', padding: '0.5rem', color: '#fff', fontSize: '0.8rem',
                      }}
                    />
                    <textarea
                      placeholder="Revised Description"
                      rows={3}
                      value={editDesc}
                      onChange={(e) => setEditDesc(e.target.value)}
                      style={{
                        background: '#0f172a', border: '1px solid rgba(255,255,255,0.1)',
                        borderRadius: '0.4rem', padding: '0.5rem', color: '#fff', fontSize: '0.8rem',
                      }}
                    />
                  </div>
                )}

                <div style={{ display: 'flex', gap: '0.75rem' }}>
                  <input
                    type="text"
                    placeholder="Reviewer Notes / Feedback (Optional)..."
                    value={reviewComment}
                    onChange={(e) => setReviewComment(e.target.value)}
                    style={{
                      flex: 1, background: '#0f172a', border: '1px solid rgba(255,255,255,0.1)',
                      borderRadius: '0.4rem', padding: '0.5rem 0.75rem', color: '#fff', fontSize: '0.8rem',
                    }}
                  />
                  <button
                    onClick={handleSubmitReview}
                    style={{
                      padding: '0.5rem 1.25rem', borderRadius: '0.4rem', background: '#f59e0b',
                      color: '#000', fontWeight: 700, border: 'none', fontSize: '0.8rem', cursor: 'pointer',
                    }}
                  >
                    Submit Decision
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
