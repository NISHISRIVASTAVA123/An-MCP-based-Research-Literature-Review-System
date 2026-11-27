import React, { useState, useEffect } from 'react';
import {
  CandidateResearchGap,
  SynthesisRun,
} from '../types/synthesis';
import {
  CounterevidenceClaim,
  CounterevidenceQuery,
  CounterevidencePublication,
  CounterevidenceAssessment,
  CounterevidenceEvidenceItem,
  CounterevidenceProfile,
  CounterevidenceSearchRun,
  CounterevidenceRelevance,
} from '../types/counterevidence';
import {
  getSynthesisRuns,
  getCandidateGaps,
  searchCounterevidenceForGap,
  searchCounterevidenceForAllGaps,
  getCounterevidenceRuns,
  getGapCounterevidenceClaims,
  getGapCounterevidenceQueries,
  getGapCounterevidencePublications,
  getGapCounterevidenceAssessments,
  reviewCounterevidenceAssessment,
  getGapCounterevidenceEvidence,
  getGapCounterevidenceProfile,
  rebuildGapCounterevidenceProfile,
} from '../services/api';
import {
  ShieldAlert,
  ShieldCheck,
  Search,
  FileText,
  AlertCircle,
  HelpCircle,
  Play,
  Filter,
  CheckCircle2,
  XCircle,
  Clock,
  Sparkles,
  ExternalLink,
  ChevronRight,
  Edit3,
  Layers,
  FileSearch,
  BookOpen,
  ArrowRight,
  Database,
} from 'lucide-react';

interface CounterevidenceViewProps {
  requestId: string;
}

export const CounterevidenceView: React.FC<CounterevidenceViewProps> = ({ requestId }) => {
  const [activeTab, setActiveTab] = useState<'profile' | 'claims_queries' | 'publications' | 'evidence'>('profile');
  const [gaps, setGaps] = useState<CandidateResearchGap[]>([]);
  const [selectedGap, setSelectedGap] = useState<CandidateResearchGap | null>(null);

  // Phase 5 Data for selected gap
  const [profile, setProfile] = useState<CounterevidenceProfile | null>(null);
  const [claims, setClaims] = useState<CounterevidenceClaim[]>([]);
  const [queries, setQueries] = useState<CounterevidenceQuery[]>([]);
  const [assessments, setAssessments] = useState<CounterevidenceAssessment[]>([]);
  const [evidenceItems, setEvidenceItems] = useState<CounterevidenceEvidenceItem[]>([]);
  const [runs, setRuns] = useState<CounterevidenceSearchRun[]>([]);

  // UI state
  const [isLoading, setIsLoading] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [relevanceFilter, setRelevanceFilter] = useState<string>('all');

  // Review Modal state
  const [reviewModalAssessment, setReviewModalAssessment] = useState<CounterevidenceAssessment | null>(null);
  const [reviewNotes, setReviewNotes] = useState('');
  const [overrideRelevance, setOverrideRelevance] = useState<CounterevidenceRelevance>('direct_counterevidence');

  useEffect(() => {
    loadGapsAndRuns();
  }, [requestId]);

  useEffect(() => {
    if (selectedGap) {
      loadGapCounterevidenceData(selectedGap.id);
    }
  }, [selectedGap]);

  const loadGapsAndRuns = async () => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      // 1. Get synthesis runs to load candidate gaps
      const synthRuns = await getSynthesisRuns(requestId);
      if (synthRuns.length > 0) {
        const candidateGaps = await getCandidateGaps(requestId, synthRuns[0].id);
        setGaps(candidateGaps);
        if (candidateGaps.length > 0 && !selectedGap) {
          setSelectedGap(candidateGaps[0]);
        }
      }
      // 2. Load counterevidence search runs
      const cRuns = await getCounterevidenceRuns();
      setRuns(cRuns);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to load initial gap data.');
    } finally {
      setIsLoading(false);
    }
  };

  const loadGapCounterevidenceData = async (gapId: string) => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const [prof, clms, qrs, asmts, evd] = await Promise.all([
        getGapCounterevidenceProfile(gapId),
        getGapCounterevidenceClaims(gapId),
        getGapCounterevidenceQueries(gapId),
        getGapCounterevidenceAssessments(gapId),
        getGapCounterevidenceEvidence(gapId),
      ]);
      setProfile(prof);
      setClaims(clms);
      setQueries(qrs);
      setAssessments(asmts);
      setEvidenceItems(evd);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to load counterevidence data for this gap.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRunSearchForGap = async () => {
    if (!selectedGap) return;
    setIsSearching(true);
    setErrorMsg(null);
    setSuccessMsg(null);
    try {
      const prof = await searchCounterevidenceForGap(selectedGap.id, {
        max_queries: 4,
        max_results_per_query: 5,
        download_fulltext: true,
      });
      setProfile(prof);
      await loadGapCounterevidenceData(selectedGap.id);
      setSuccessMsg(`Counterevidence search completed for gap: "${selectedGap.title}"`);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to execute counterevidence search.');
    } finally {
      setIsSearching(false);
    }
  };

  const handleRunBatchSearch = async () => {
    if (gaps.length === 0) return;
    setIsSearching(true);
    setErrorMsg(null);
    setSuccessMsg(null);
    try {
      const run = await searchCounterevidenceForAllGaps({
        gap_ids: gaps.map((g) => g.id),
        scope_description: `Batch counterevidence search across ${gaps.length} candidate gaps`,
      });
      setSuccessMsg(`Batch counterevidence search triggered. Found publications across gaps.`);
      if (selectedGap) {
        await loadGapCounterevidenceData(selectedGap.id);
      }
      const cRuns = await getCounterevidenceRuns();
      setRuns(cRuns);
    } catch (err: any) {
      setErrorMsg(err.message || 'Batch search failed.');
    } finally {
      setIsSearching(false);
    }
  };

  const handleRebuildProfile = async () => {
    if (!selectedGap) return;
    setIsLoading(true);
    try {
      const updatedProf = await rebuildGapCounterevidenceProfile(selectedGap.id);
      setProfile(updatedProf);
      setSuccessMsg('Profile recalculated successfully.');
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to recalculate profile.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleOpenReviewModal = (assessment: CounterevidenceAssessment) => {
    setReviewModalAssessment(assessment);
    setReviewNotes(assessment.human_reviewer_notes || '');
    setOverrideRelevance(assessment.human_override_relevance || assessment.relevance);
  };

  const handleSubmitReview = async () => {
    if (!reviewModalAssessment || !selectedGap) return;
    setIsLoading(true);
    try {
      await reviewCounterevidenceAssessment(reviewModalAssessment.id, {
        reviewer_notes: reviewNotes,
        override_relevance: overrideRelevance,
      });
      setReviewModalAssessment(null);
      await loadGapCounterevidenceData(selectedGap.id);
      setSuccessMsg('Review recorded and counterevidence profile updated.');
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to submit review.');
    } finally {
      setIsLoading(false);
    }
  };

  // Badges & styling helpers
  const getImpactBadge = (impact?: string) => {
    switch (impact) {
      case 'strongly_challenged':
        return <span className="badge badge-danger"><ShieldAlert size={12} className="inline mr-1" /> Strongly Challenged</span>;
      case 'partially_challenged':
        return <span className="badge badge-warning"><AlertCircle size={12} className="inline mr-1" /> Partially Challenged</span>;
      case 'weakly_challenged':
        return <span className="badge badge-info"><AlertCircle size={12} className="inline mr-1" /> Weakly Challenged</span>;
      case 'unchallenged':
        return <span className="badge badge-success"><ShieldCheck size={12} className="inline mr-1" /> Unchallenged (Resilient)</span>;
      case 'inconclusive':
      default:
        return <span className="badge badge-secondary"><HelpCircle size={12} className="inline mr-1" /> Inconclusive</span>;
    }
  };

  const getRelevanceBadge = (rel: CounterevidenceRelevance) => {
    switch (rel) {
      case 'direct_counterevidence':
        return <span style={{ padding: '0.2rem 0.6rem', borderRadius: '999px', fontSize: '0.75rem', fontWeight: 600, background: 'rgba(239,68,68,0.2)', color: '#f87171', border: '1px solid rgba(239,68,68,0.4)' }}>Direct Counterevidence</span>;
      case 'partial_counterevidence':
        return <span style={{ padding: '0.2rem 0.6rem', borderRadius: '999px', fontSize: '0.75rem', fontWeight: 600, background: 'rgba(245,158,11,0.2)', color: '#fbbf24', border: '1px solid rgba(245,158,11,0.4)' }}>Partial Counterevidence</span>;
      case 'related_evidence':
        return <span style={{ padding: '0.2rem 0.6rem', borderRadius: '999px', fontSize: '0.75rem', fontWeight: 600, background: 'rgba(59,130,246,0.2)', color: '#60a5fa', border: '1px solid rgba(59,130,246,0.4)' }}>Related Evidence</span>;
      case 'not_relevant':
        return <span style={{ padding: '0.2rem 0.6rem', borderRadius: '999px', fontSize: '0.75rem', fontWeight: 600, background: 'rgba(100,116,139,0.2)', color: '#94a3b8', border: '1px solid rgba(100,116,139,0.4)' }}>Not Relevant</span>;
      case 'insufficient_information':
      default:
        return <span style={{ padding: '0.2rem 0.6rem', borderRadius: '999px', fontSize: '0.75rem', fontWeight: 600, background: 'rgba(148,163,184,0.15)', color: '#cbd5e1', border: '1px solid rgba(148,163,184,0.3)' }}>Insufficient Info</span>;
    }
  };

  const getLevelBadge = (level: string) => {
    switch (level) {
      case 'level_1_fulltext_passage':
        return <span style={{ padding: '0.15rem 0.5rem', borderRadius: '4px', fontSize: '0.7rem', fontWeight: 600, background: 'rgba(16,185,129,0.15)', color: '#34d399', border: '1px solid rgba(16,185,129,0.3)' }}>Level 1: Full-Text Ground Truth</span>;
      case 'level_2_abstract_supported':
        return <span style={{ padding: '0.15rem 0.5rem', borderRadius: '4px', fontSize: '0.7rem', fontWeight: 600, background: 'rgba(245,158,11,0.15)', color: '#fbbf24', border: '1px solid rgba(245,158,11,0.3)' }}>Level 2: Abstract Only (Unverified)</span>;
      case 'level_3_citation_inferred':
        return <span style={{ padding: '0.15rem 0.5rem', borderRadius: '4px', fontSize: '0.7rem', fontWeight: 600, background: 'rgba(99,102,241,0.15)', color: '#818cf8', border: '1px solid rgba(99,102,241,0.3)' }}>Level 3: Citation Inferred</span>;
      default:
        return <span style={{ padding: '0.15rem 0.5rem', borderRadius: '4px', fontSize: '0.7rem', fontWeight: 600, background: 'rgba(148,163,184,0.15)', color: '#94a3b8', border: '1px solid rgba(148,163,184,0.3)' }}>Level 4: Metadata Only</span>;
    }
  };

  const filteredAssessments = assessments.filter((a) => {
    if (relevanceFilter === 'all') return true;
    const currentRel = a.human_override_relevance || a.relevance;
    return currentRel === relevanceFilter;
  });

  return (
    <div className="view-container" style={{ padding: '1.5rem', maxWidth: '1440px', margin: '0 auto' }}>
      {/* Header Banner */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(30, 27, 75, 0.9) 0%, rgba(67, 24, 75, 0.7) 100%)',
        borderRadius: '1rem',
        padding: '1.75rem',
        marginBottom: '1.5rem',
        border: '1px solid rgba(244, 63, 94, 0.25)',
        boxShadow: '0 8px 32px rgba(0,0,0,0.3)',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
              <div style={{
                background: 'linear-gradient(135deg, #f43f5e, #be123c)',
                padding: '0.5rem',
                borderRadius: '0.5rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}>
                <ShieldAlert size={22} color="#fff" />
              </div>
              <h1 style={{ fontSize: '1.45rem', fontWeight: 800, color: '#fff', margin: 0, letterSpacing: '-0.02em' }}>
                Phase 5: Explicit Counterevidence Retrieval & Verification
              </h1>
              <span style={{
                fontSize: '0.7rem',
                fontWeight: 700,
                background: 'rgba(244, 63, 94, 0.2)',
                color: '#fb7185',
                padding: '0.2rem 0.6rem',
                borderRadius: '999px',
                border: '1px solid rgba(244, 63, 94, 0.4)',
              }}>
                GAP RESILIENCE ENGINE
              </span>
            </div>
            <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: '0.88rem', margin: 0, maxWidth: '850px' }}>
              Deconstructs candidate research gaps into empirical sub-claims, executes adversarial multi-angle queries across academic databases, and tests candidate gaps against verifiable passage-level ground truth to eliminate hallucinated or pre-addressed gaps.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
            <button
              onClick={handleRunBatchSearch}
              disabled={isSearching || gaps.length === 0}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '0.65rem 1.1rem',
                borderRadius: '0.5rem',
                background: 'linear-gradient(135deg, #f43f5e 0%, #e11d48 100%)',
                color: '#fff',
                fontWeight: 600,
                fontSize: '0.84rem',
                border: 'none',
                cursor: isSearching ? 'not-allowed' : 'pointer',
                opacity: isSearching ? 0.6 : 1,
                boxShadow: '0 4px 14px rgba(244,63,94,0.35)',
              }}
            >
              {isSearching ? <Clock size={16} className="animate-spin" /> : <Play size={16} />}
              Search Counterevidence for All Gaps ({gaps.length})
            </button>
          </div>
        </div>

        {/* Status / Alert Messages */}
        {errorMsg && (
          <div style={{ marginTop: '1rem', padding: '0.75rem 1rem', background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: '0.5rem', color: '#fca5a5', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <AlertCircle size={16} />
            <span>{errorMsg}</span>
          </div>
        )}
        {successMsg && (
          <div style={{ marginTop: '1rem', padding: '0.75rem 1rem', background: 'rgba(16, 185, 129, 0.15)', border: '1px solid rgba(16, 185, 129, 0.3)', borderRadius: '0.5rem', color: '#6ee7b7', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <CheckCircle2 size={16} />
            <span>{successMsg}</span>
          </div>
        )}
      </div>

      {/* Main Layout Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '1.5rem', alignItems: 'start' }}>
        {/* Left Column: Gap List */}
        <div style={{
          background: 'rgba(15, 23, 42, 0.75)',
          borderRadius: '0.75rem',
          border: '1px solid rgba(255,255,255,0.08)',
          padding: '1.25rem',
          backdropFilter: 'blur(12px)',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <div style={{ fontSize: '0.75rem', fontWeight: 700, letterSpacing: '0.08em', color: 'rgba(255,255,255,0.45)', textTransform: 'uppercase' }}>
              Candidate Research Gaps ({gaps.length})
            </div>
          </div>

          {gaps.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '2rem 1rem', color: 'rgba(255,255,255,0.4)', fontSize: '0.85rem' }}>
              No candidate gaps found. Please execute Phase 4 Literature Synthesis first.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem', maxHeight: '720px', overflowY: 'auto' }}>
              {gaps.map((gap) => {
                const isSelected = selectedGap?.id === gap.id;
                return (
                  <div
                    key={gap.id}
                    onClick={() => setSelectedGap(gap)}
                    style={{
                      padding: '0.85rem 1rem',
                      borderRadius: '0.5rem',
                      background: isSelected ? 'rgba(244, 63, 94, 0.15)' : 'rgba(255,255,255,0.03)',
                      border: isSelected ? '1px solid rgba(244, 63, 94, 0.5)' : '1px solid rgba(255,255,255,0.05)',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
                      <span style={{ fontSize: '0.7rem', fontWeight: 600, color: '#f43f5e', textTransform: 'uppercase' }}>
                        {gap.category.replace(/_/g, ' ')}
                      </span>
                      <span style={{ fontSize: '0.65rem', color: 'rgba(255,255,255,0.4)' }}>
                        Conf: {((gap.preliminary_confidence || 0) * 100).toFixed(0)}%
                      </span>
                    </div>
                    <div style={{ fontSize: '0.84rem', fontWeight: 600, color: '#fff', lineHeight: 1.35, marginBottom: '0.35rem' }}>
                      {gap.title}
                    </div>
                    <div style={{ fontSize: '0.72rem', color: 'rgba(255,255,255,0.5)', overflow: 'hidden', textOverflow: 'ellipsis', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' }}>
                      {gap.description}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Right Column: Selected Gap Details & Counterevidence Workspace */}
        {selectedGap ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            {/* Selected Gap Header Card */}
            <div style={{
              background: 'rgba(15, 23, 42, 0.85)',
              borderRadius: '0.75rem',
              border: '1px solid rgba(255,255,255,0.08)',
              padding: '1.5rem',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem', marginBottom: '0.75rem' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.35rem' }}>
                    <span style={{ fontSize: '0.72rem', fontWeight: 700, color: '#f43f5e', background: 'rgba(244,63,94,0.15)', padding: '0.15rem 0.5rem', borderRadius: '4px' }}>
                      {selectedGap.category.toUpperCase()}
                    </span>
                    <span style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.45)' }}>
                      Gap ID: {selectedGap.id.slice(0, 8)}...
                    </span>
                  </div>
                  <h2 style={{ fontSize: '1.2rem', fontWeight: 700, color: '#fff', margin: 0 }}>
                    {selectedGap.title}
                  </h2>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <button
                    onClick={handleRunSearchForGap}
                    disabled={isSearching}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.45rem',
                      padding: '0.55rem 0.95rem',
                      borderRadius: '0.45rem',
                      background: 'rgba(244, 63, 94, 0.2)',
                      border: '1px solid rgba(244, 63, 94, 0.4)',
                      color: '#fb7185',
                      fontWeight: 600,
                      fontSize: '0.8rem',
                      cursor: isSearching ? 'not-allowed' : 'pointer',
                    }}
                  >
                    {isSearching ? <Clock size={14} className="animate-spin" /> : <Search size={14} />}
                    Run Search For This Gap
                  </button>

                  <button
                    onClick={handleRebuildProfile}
                    disabled={isLoading}
                    title="Recalculate impact profile from current assessments"
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.45rem',
                      padding: '0.55rem 0.95rem',
                      borderRadius: '0.45rem',
                      background: 'rgba(255, 255, 255, 0.05)',
                      border: '1px solid rgba(255, 255, 255, 0.1)',
                      color: 'rgba(255,255,255,0.8)',
                      fontWeight: 500,
                      fontSize: '0.8rem',
                      cursor: 'pointer',
                    }}
                  >
                    <Sparkles size={14} />
                    Rebuild Profile
                  </button>
                </div>
              </div>

              <p style={{ fontSize: '0.85rem', color: 'rgba(255,255,255,0.75)', lineHeight: 1.5, margin: '0 0 1rem 0' }}>
                {selectedGap.description}
              </p>

              {/* Resilience Status Summary Banner */}
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '0.85rem 1.25rem',
                background: 'rgba(0,0,0,0.3)',
                borderRadius: '0.5rem',
                border: '1px solid rgba(255,255,255,0.06)',
                flexWrap: 'wrap',
                gap: '0.75rem',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <span style={{ fontSize: '0.78rem', color: 'rgba(255,255,255,0.5)', fontWeight: 600 }}>
                    Gap Resilience Impact:
                  </span>
                  {getImpactBadge(profile?.impact_assessment)}
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem', fontSize: '0.78rem', color: 'rgba(255,255,255,0.6)' }}>
                  <span>Queries: <strong style={{ color: '#fff' }}>{profile?.total_queries_executed || queries.length}</strong></span>
                  <span>Discovered: <strong style={{ color: '#fff' }}>{profile?.total_publications_found || assessments.length}</strong></span>
                  <span>Direct Counter: <strong style={{ color: '#f87171' }}>{profile?.direct_counterevidence_count || 0}</strong></span>
                  <span>Partial: <strong style={{ color: '#fbbf24' }}>{profile?.partial_counterevidence_count || 0}</strong></span>
                  <span>Related: <strong style={{ color: '#60a5fa' }}>{profile?.related_evidence_count || 0}</strong></span>
                </div>
              </div>
            </div>

            {/* Navigation Tabs */}
            <div style={{ display: 'flex', gap: '0.5rem', borderBottom: '1px solid rgba(255,255,255,0.08)', paddingBottom: '0.5rem' }}>
              {[
                { id: 'profile', label: 'Resilience Profile & Audit', icon: ShieldAlert, count: profile ? 1 : 0 },
                { id: 'claims_queries', label: 'Decomposed Claims & Queries', icon: Layers, count: queries.length },
                { id: 'publications', label: 'Counterevidence Publications', icon: BookOpen, count: assessments.length },
                { id: 'evidence', label: 'Passage Ground Truth Inspector', icon: FileSearch, count: evidenceItems.length },
              ].map((tab) => {
                const isActive = activeTab === tab.id;
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id as any)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.5rem',
                      padding: '0.55rem 1rem',
                      borderRadius: '0.4rem',
                      background: isActive ? 'rgba(244, 63, 94, 0.15)' : 'transparent',
                      border: isActive ? '1px solid rgba(244, 63, 94, 0.35)' : '1px solid transparent',
                      color: isActive ? '#fb7185' : 'rgba(255,255,255,0.6)',
                      fontSize: '0.82rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                    }}
                  >
                    <Icon size={15} />
                    {tab.label}
                    {tab.count > 0 && (
                      <span style={{
                        fontSize: '0.68rem',
                        padding: '0.1rem 0.4rem',
                        borderRadius: '999px',
                        background: isActive ? 'rgba(244, 63, 94, 0.3)' : 'rgba(255,255,255,0.1)',
                        color: isActive ? '#fff' : 'rgba(255,255,255,0.7)',
                      }}>
                        {tab.count}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>

            {/* TAB CONTENT 1: Resilience Profile & Audit */}
            {activeTab === 'profile' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                <div style={{
                  background: 'rgba(15, 23, 42, 0.75)',
                  borderRadius: '0.75rem',
                  border: '1px solid rgba(255,255,255,0.08)',
                  padding: '1.5rem',
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                    <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#fff', margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <ShieldCheck size={18} color="#f43f5e" />
                      Executive Counterevidence Synthesis
                    </h3>
                    {getImpactBadge(profile?.impact_assessment)}
                  </div>

                  <p style={{ fontSize: '0.88rem', color: 'rgba(255,255,255,0.8)', lineHeight: 1.6, marginBottom: '1.25rem' }}>
                    {profile?.executive_summary || 'No counterevidence search has been executed for this gap yet. Click "Run Search For This Gap" to decompose claims and search.'}
                  </p>

                  {/* Summary Breakdown Grid */}
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginBottom: '1.5rem' }}>
                    <div style={{ padding: '1rem', borderRadius: '0.5rem', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.2)' }}>
                      <div style={{ fontSize: '0.72rem', color: '#f87171', fontWeight: 600, textTransform: 'uppercase' }}>Direct Counter</div>
                      <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#fff', marginTop: '0.25rem' }}>{profile?.direct_counterevidence_count || 0}</div>
                      <div style={{ fontSize: '0.7rem', color: 'rgba(255,255,255,0.45)', marginTop: '0.25rem' }}>Directly refutes gap claim</div>
                    </div>
                    <div style={{ padding: '1rem', borderRadius: '0.5rem', background: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.2)' }}>
                      <div style={{ fontSize: '0.72rem', color: '#fbbf24', fontWeight: 600, textTransform: 'uppercase' }}>Partial Counter</div>
                      <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#fff', marginTop: '0.25rem' }}>{profile?.partial_counterevidence_count || 0}</div>
                      <div style={{ fontSize: '0.7rem', color: 'rgba(255,255,255,0.45)', marginTop: '0.25rem' }}>Partially addresses aspects</div>
                    </div>
                    <div style={{ padding: '1rem', borderRadius: '0.5rem', background: 'rgba(59,130,246,0.1)', border: '1px solid rgba(59,130,246,0.2)' }}>
                      <div style={{ fontSize: '0.72rem', color: '#60a5fa', fontWeight: 600, textTransform: 'uppercase' }}>Related Evidence</div>
                      <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#fff', marginTop: '0.25rem' }}>{profile?.related_evidence_count || 0}</div>
                      <div style={{ fontSize: '0.7rem', color: 'rgba(255,255,255,0.45)', marginTop: '0.25rem' }}>Related topic or baseline</div>
                    </div>
                    <div style={{ padding: '1rem', borderRadius: '0.5rem', background: 'rgba(100,116,139,0.1)', border: '1px solid rgba(100,116,139,0.2)' }}>
                      <div style={{ fontSize: '0.72rem', color: '#94a3b8', fontWeight: 600, textTransform: 'uppercase' }}>Not Relevant</div>
                      <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#fff', marginTop: '0.25rem' }}>{profile?.not_relevant_count || 0}</div>
                      <div style={{ fontSize: '0.7rem', color: 'rgba(255,255,255,0.45)', marginTop: '0.25rem' }}>Off-target query noise</div>
                    </div>
                  </div>

                  {/* Two column: Unresolved Claims & Limitations */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem' }}>
                    <div style={{ padding: '1.25rem', background: 'rgba(0,0,0,0.25)', borderRadius: '0.5rem', border: '1px solid rgba(255,255,255,0.06)' }}>
                      <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#34d399', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                        <CheckCircle2 size={15} /> Still Unresolved Claims (Genuine Novelty)
                      </div>
                      {profile?.unresolved_claims && profile.unresolved_claims.length > 0 ? (
                        <ul style={{ margin: 0, paddingLeft: '1.2rem', fontSize: '0.82rem', color: 'rgba(255,255,255,0.75)', lineHeight: 1.5 }}>
                          {profile.unresolved_claims.map((claim, idx) => (
                            <li key={idx} style={{ marginBottom: '0.4rem' }}>{claim}</li>
                          ))}
                        </ul>
                      ) : (
                        <div style={{ fontSize: '0.8rem', color: 'rgba(255,255,255,0.4)' }}>No unresolved claims registered.</div>
                      )}
                    </div>

                    <div style={{ padding: '1.25rem', background: 'rgba(0,0,0,0.25)', borderRadius: '0.5rem', border: '1px solid rgba(255,255,255,0.06)' }}>
                      <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#fbbf24', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                        <AlertCircle size={15} /> Literature Limitations & Verification Caveats
                      </div>
                      {profile?.limitations && profile.limitations.length > 0 ? (
                        <ul style={{ margin: 0, paddingLeft: '1.2rem', fontSize: '0.82rem', color: 'rgba(255,255,255,0.75)', lineHeight: 1.5 }}>
                          {profile.limitations.map((lim, idx) => (
                            <li key={idx} style={{ marginBottom: '0.4rem' }}>{lim}</li>
                          ))}
                        </ul>
                      ) : (
                        <div style={{ fontSize: '0.8rem', color: 'rgba(255,255,255,0.4)' }}>No limitations identified.</div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* TAB CONTENT 2: Decomposed Claims & Queries */}
            {activeTab === 'claims_queries' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                {/* Decomposed Claims */}
                <div style={{
                  background: 'rgba(15, 23, 42, 0.75)',
                  borderRadius: '0.75rem',
                  border: '1px solid rgba(255,255,255,0.08)',
                  padding: '1.5rem',
                }}>
                  <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#fff', margin: '0 0 1rem 0', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <Layers size={18} color="#f43f5e" />
                    Decomposed Empirical Claims ({claims.length})
                  </h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    {claims.map((claim, idx) => (
                      <div key={claim.id} style={{ padding: '1rem', borderRadius: '0.5rem', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                          <span style={{ fontSize: '0.72rem', fontWeight: 700, color: '#f43f5e', textTransform: 'uppercase' }}>
                            Claim #{idx + 1} · {claim.claim_type.replace(/_/g, ' ')}
                          </span>
                          <span style={{ fontSize: '0.7rem', color: 'rgba(255,255,255,0.4)' }}>
                            Confidence: {(claim.confidence_score * 100).toFixed(0)}%
                          </span>
                        </div>
                        <div style={{ fontSize: '0.85rem', color: '#fff', fontWeight: 500 }}>
                          "{claim.claim_text}"
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Adversarial Multi-Angle Queries */}
                <div style={{
                  background: 'rgba(15, 23, 42, 0.75)',
                  borderRadius: '0.75rem',
                  border: '1px solid rgba(255,255,255,0.08)',
                  padding: '1.5rem',
                }}>
                  <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#fff', margin: '0 0 1rem 0', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <Search size={18} color="#f43f5e" />
                    Adversarial Retrieval Queries ({queries.length})
                  </h3>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem' }}>
                    {queries.map((q) => (
                      <div key={q.id} style={{ padding: '1rem', borderRadius: '0.5rem', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                          <span style={{ fontSize: '0.7rem', fontWeight: 700, color: '#38bdf8', textTransform: 'uppercase' }}>
                            {q.query_type.replace(/_/g, ' ')}
                          </span>
                          <span style={{ fontSize: '0.7rem', color: 'rgba(255,255,255,0.45)' }}>
                            {q.results_count} results
                          </span>
                        </div>
                        <div style={{ fontSize: '0.84rem', color: '#fff', fontFamily: 'monospace', background: 'rgba(0,0,0,0.3)', padding: '0.4rem 0.6rem', borderRadius: '4px', marginBottom: '0.4rem' }}>
                          {q.query_text}
                        </div>
                        {q.rationale && (
                          <div style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.5)' }}>
                            Rationale: {q.rationale}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* TAB CONTENT 3: Discovered Publications */}
            {activeTab === 'publications' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                <div style={{
                  background: 'rgba(15, 23, 42, 0.75)',
                  borderRadius: '0.75rem',
                  border: '1px solid rgba(255,255,255,0.08)',
                  padding: '1.25rem',
                }}>
                  {/* Filter Toolbar */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '0.75rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <Filter size={15} color="rgba(255,255,255,0.5)" />
                      <span style={{ fontSize: '0.78rem', color: 'rgba(255,255,255,0.6)', fontWeight: 600 }}>Filter Relevance:</span>
                      {['all', 'direct_counterevidence', 'partial_counterevidence', 'related_evidence', 'not_relevant'].map((f) => (
                        <button
                          key={f}
                          onClick={() => setRelevanceFilter(f)}
                          style={{
                            padding: '0.3rem 0.65rem',
                            borderRadius: '4px',
                            fontSize: '0.74rem',
                            fontWeight: 600,
                            background: relevanceFilter === f ? 'rgba(244,63,94,0.2)' : 'rgba(255,255,255,0.05)',
                            border: relevanceFilter === f ? '1px solid rgba(244,63,94,0.4)' : '1px solid transparent',
                            color: relevanceFilter === f ? '#fb7185' : 'rgba(255,255,255,0.6)',
                            cursor: 'pointer',
                          }}
                        >
                          {f === 'all' ? 'All' : f.replace(/_/g, ' ')}
                        </button>
                      ))}
                    </div>
                    <span style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.45)' }}>
                      Showing {filteredAssessments.length} of {assessments.length} publications
                    </span>
                  </div>

                  {/* Publications List */}
                  {filteredAssessments.length === 0 ? (
                    <div style={{ textAlign: 'center', padding: '3rem 1rem', color: 'rgba(255,255,255,0.4)', fontSize: '0.85rem' }}>
                      No publications matching this relevance filter.
                    </div>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                      {filteredAssessments.map((asmt) => {
                        const pub = asmt.publication;
                        const effectiveRel = asmt.human_override_relevance || asmt.relevance;
                        return (
                          <div
                            key={asmt.id}
                            style={{
                              padding: '1.25rem',
                              borderRadius: '0.5rem',
                              background: 'rgba(255,255,255,0.02)',
                              border: '1px solid rgba(255,255,255,0.06)',
                              display: 'flex',
                              flexDirection: 'column',
                              gap: '0.75rem',
                            }}
                          >
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '1rem' }}>
                              <div style={{ flex: 1 }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.35rem', flexWrap: 'wrap' }}>
                                  {getRelevanceBadge(effectiveRel)}
                                  {getLevelBadge(asmt.evidence_level)}
                                  {pub?.fulltext_available ? (
                                    <span style={{ fontSize: '0.68rem', background: 'rgba(16,185,129,0.2)', color: '#34d399', padding: '0.15rem 0.45rem', borderRadius: '4px' }}>Full-Text Available</span>
                                  ) : (
                                    <span style={{ fontSize: '0.68rem', background: 'rgba(245,158,11,0.2)', color: '#fbbf24', padding: '0.15rem 0.45rem', borderRadius: '4px' }}>Abstract-Only</span>
                                  )}
                                  {asmt.human_reviewed && (
                                    <span style={{ fontSize: '0.68rem', background: 'rgba(168,85,247,0.2)', color: '#c084fc', padding: '0.15rem 0.45rem', borderRadius: '4px' }}>Human Verified</span>
                                  )}
                                </div>
                                <h4 style={{ fontSize: '0.95rem', fontWeight: 600, color: '#fff', margin: 0 }}>
                                  {pub?.title || 'Unknown Publication Title'}
                                </h4>
                                <div style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.5)', marginTop: '0.25rem' }}>
                                  {pub?.authors?.join(', ') || 'Unknown Authors'} · {pub?.year || 'N/A'} · {pub?.venue || pub?.source_provider || 'Academic Database'}
                                </div>
                              </div>

                              <button
                                onClick={() => handleOpenReviewModal(asmt)}
                                style={{
                                  display: 'flex',
                                  alignItems: 'center',
                                  gap: '0.35rem',
                                  padding: '0.45rem 0.75rem',
                                  borderRadius: '0.4rem',
                                  background: 'rgba(255,255,255,0.06)',
                                  border: '1px solid rgba(255,255,255,0.1)',
                                  color: 'rgba(255,255,255,0.8)',
                                  fontSize: '0.75rem',
                                  cursor: 'pointer',
                                }}
                              >
                                <Edit3 size={13} />
                                Human Audit
                              </button>
                            </div>

                            {/* Assessment notes */}
                            {asmt.assessment_notes && (
                              <div style={{ fontSize: '0.82rem', color: 'rgba(255,255,255,0.7)', background: 'rgba(0,0,0,0.25)', padding: '0.75rem', borderRadius: '0.4rem', borderLeft: '3px solid #f43f5e' }}>
                                <strong style={{ color: '#fff' }}>Assessment Rationale: </strong>
                                {asmt.assessment_notes}
                              </div>
                            )}

                            {/* Human reviewer notes if any */}
                            {asmt.human_reviewed && asmt.human_reviewer_notes && (
                              <div style={{ fontSize: '0.8rem', color: '#e9d5ff', background: 'rgba(168,85,247,0.1)', padding: '0.6rem', borderRadius: '0.4rem', borderLeft: '3px solid #c084fc' }}>
                                <strong>Human Auditor Notes: </strong>
                                {asmt.human_reviewer_notes}
                              </div>
                            )}

                            {/* Extracted Evidence Passages for this publication */}
                            {asmt.evidence_passages && asmt.evidence_passages.length > 0 && (
                              <div style={{ marginTop: '0.25rem' }}>
                                <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', marginBottom: '0.4rem' }}>
                                  Verified Evidence Passages ({asmt.evidence_passages.length})
                                </div>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                                  {asmt.evidence_passages.map((evItem) => (
                                    <div key={evItem.id} style={{ fontSize: '0.8rem', fontStyle: 'italic', background: 'rgba(0,0,0,0.3)', padding: '0.65rem 0.85rem', borderRadius: '0.4rem', border: '1px solid rgba(255,255,255,0.05)', color: '#e2e8f0' }}>
                                      "{evItem.passage_text}"
                                      <div style={{ fontStyle: 'normal', fontSize: '0.7rem', color: 'rgba(255,255,255,0.4)', marginTop: '0.3rem', display: 'flex', gap: '0.75rem' }}>
                                        <span>Section: {evItem.section_heading || 'N/A'}</span>
                                        <span>Page: {evItem.page_number || 'N/A'}</span>
                                        <span>Status: {evItem.verification_status}</span>
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* TAB CONTENT 4: Passage Ground Truth Inspector */}
            {activeTab === 'evidence' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                <div style={{
                  background: 'rgba(15, 23, 42, 0.75)',
                  borderRadius: '0.75rem',
                  border: '1px solid rgba(255,255,255,0.08)',
                  padding: '1.5rem',
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                    <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#fff', margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <FileSearch size={18} color="#f43f5e" />
                      Granular Ground-Truth Passage Inspector ({evidenceItems.length})
                    </h3>
                  </div>

                  <p style={{ fontSize: '0.85rem', color: 'rgba(255,255,255,0.6)', margin: '0 0 1.25rem 0' }}>
                    Every passage below anchors a counterevidence claim to verbatim source text from retrieved papers. Level 1 indicates full-text quotes with verified page and section coordinates.
                  </p>

                  {evidenceItems.length === 0 ? (
                    <div style={{ textAlign: 'center', padding: '3rem 1rem', color: 'rgba(255,255,255,0.4)', fontSize: '0.85rem' }}>
                      No passage-level ground truth stored for this gap yet. Run a counterevidence search with full-text retrieval enabled.
                    </div>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
                      {evidenceItems.map((item) => (
                        <div
                          key={item.id}
                          style={{
                            padding: '1rem',
                            borderRadius: '0.5rem',
                            background: 'rgba(255,255,255,0.02)',
                            border: '1px solid rgba(255,255,255,0.06)',
                          }}
                        >
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                            {getLevelBadge(item.evidence_level)}
                            <div style={{ fontSize: '0.7rem', color: 'rgba(255,255,255,0.4)', display: 'flex', gap: '0.75rem' }}>
                              <span>Section: <strong style={{ color: '#fff' }}>{item.section_heading || 'Main text'}</strong></span>
                              <span>Page: <strong style={{ color: '#fff' }}>{item.page_number || 'N/A'}</strong></span>
                              <span>Status: <strong style={{ color: '#34d399' }}>{item.verification_status}</strong></span>
                            </div>
                          </div>
                          <div style={{ fontSize: '0.85rem', color: '#f1f5f9', fontStyle: item.is_quote ? 'italic' : 'normal', lineHeight: 1.5, background: 'rgba(0,0,0,0.3)', padding: '0.75rem', borderRadius: '0.4rem', borderLeft: '3px solid #38bdf8' }}>
                            "{item.passage_text}"
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div style={{
            background: 'rgba(15, 23, 42, 0.75)',
            borderRadius: '0.75rem',
            border: '1px solid rgba(255,255,255,0.08)',
            padding: '3rem',
            textAlign: 'center',
            color: 'rgba(255,255,255,0.4)',
          }}>
            Select a candidate research gap on the left to inspect its counterevidence profile.
          </div>
        )}
      </div>

      {/* Human Review Modal */}
      {reviewModalAssessment && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0,0,0,0.75)',
          backdropFilter: 'blur(8px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 100,
          padding: '1.5rem',
        }}>
          <div style={{
            background: '#0f172a',
            borderRadius: '0.75rem',
            border: '1px solid rgba(255,255,255,0.15)',
            padding: '1.75rem',
            maxWidth: '600px',
            width: '100%',
            boxShadow: '0 20px 40px rgba(0,0,0,0.5)',
          }}>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#fff', margin: '0 0 0.5rem 0' }}>
              Human Auditor Review
            </h3>
            <p style={{ fontSize: '0.82rem', color: 'rgba(255,255,255,0.6)', margin: '0 0 1.25rem 0' }}>
              Override the automated counterevidence classification or add scholarly audit notes.
            </p>

            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: 'rgba(255,255,255,0.7)', marginBottom: '0.4rem' }}>
                Classification Override
              </label>
              <select
                value={overrideRelevance}
                onChange={(e) => setOverrideRelevance(e.target.value as CounterevidenceRelevance)}
                style={{
                  width: '100%',
                  padding: '0.6rem',
                  borderRadius: '0.4rem',
                  background: 'rgba(255,255,255,0.05)',
                  border: '1px solid rgba(255,255,255,0.15)',
                  color: '#fff',
                  fontSize: '0.85rem',
                }}
              >
                <option value="direct_counterevidence">Direct Counterevidence</option>
                <option value="partial_counterevidence">Partial Counterevidence</option>
                <option value="related_evidence">Related Evidence</option>
                <option value="not_relevant">Not Relevant</option>
                <option value="insufficient_information">Insufficient Information</option>
              </select>
            </div>

            <div style={{ marginBottom: '1.25rem' }}>
              <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: 'rgba(255,255,255,0.7)', marginBottom: '0.4rem' }}>
                Auditor Scholarly Notes
              </label>
              <textarea
                value={reviewNotes}
                onChange={(e) => setReviewNotes(e.target.value)}
                placeholder="Enter justification for override or notes on publication claims..."
                rows={4}
                style={{
                  width: '100%',
                  padding: '0.6rem',
                  borderRadius: '0.4rem',
                  background: 'rgba(255,255,255,0.05)',
                  border: '1px solid rgba(255,255,255,0.15)',
                  color: '#fff',
                  fontSize: '0.85rem',
                  resize: 'vertical',
                }}
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
              <button
                onClick={() => setReviewModalAssessment(null)}
                style={{
                  padding: '0.55rem 1rem',
                  borderRadius: '0.4rem',
                  background: 'transparent',
                  border: '1px solid rgba(255,255,255,0.2)',
                  color: 'rgba(255,255,255,0.8)',
                  fontSize: '0.82rem',
                  cursor: 'pointer',
                }}
              >
                Cancel
              </button>
              <button
                onClick={handleSubmitReview}
                disabled={isLoading}
                style={{
                  padding: '0.55rem 1.15rem',
                  borderRadius: '0.4rem',
                  background: 'linear-gradient(135deg, #f43f5e 0%, #e11d48 100%)',
                  border: 'none',
                  color: '#fff',
                  fontWeight: 600,
                  fontSize: '0.82rem',
                  cursor: isLoading ? 'not-allowed' : 'pointer',
                }}
              >
                Save Audit
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
