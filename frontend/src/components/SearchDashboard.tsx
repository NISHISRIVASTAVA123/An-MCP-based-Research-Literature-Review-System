import React, { useState, useEffect } from 'react';
import {
  ResearchRequest,
  Paper,
  PaperListResponse,
  SearchExecutionSummary,
} from '../types';
import { listPapers, getExportUrl } from '../services/api';
import {
  Search,
  Download,
  Filter,
  FileText,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  BookOpen,
  Layers,
  Database,
  Calendar,
  Sparkles,
  ArrowUpDown,
  FileSpreadsheet,
} from 'lucide-react';

interface SearchDashboardProps {
  request: ResearchRequest;
  onModifyStrategy: () => void;
  onSelectPaper: (paper: Paper) => void;
  lastExecution?: SearchExecutionSummary;
  onProceedToScreening?: () => void;
}

const DB_COLORS: Record<string, { bg: string; color: string; border: string }> = {
  openalex: { bg: '#e0f2fe', color: '#0369a1', border: '#bae6fd' },
  semantic_scholar: { bg: '#f3e8ff', color: '#6d28d9', border: '#ddd6fe' },
  crossref: { bg: '#fef3c7', color: '#92400e', border: '#fde68a' },
  arxiv: { bg: '#fee2e2', color: '#991b1b', border: '#fecaca' },
};

export const SearchDashboard: React.FC<SearchDashboardProps> = ({
  request,
  onModifyStrategy,
  onSelectPaper,
  lastExecution,
  onProceedToScreening,
}) => {
  const [papersData, setPapersData] = useState<PaperListResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Filters & Sorting state
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDb, setSelectedDb] = useState('');
  const [yearFrom, setYearFrom] = useState<number | undefined>(undefined);
  const [yearTo, setYearTo] = useState<number | undefined>(undefined);
  const [hasAbstractOnly, setHasAbstractOnly] = useState(false);
  const [hasPdfOnly, setHasPdfOnly] = useState(false);
  const [sortBy, setSortBy] = useState('year');
  const [sortOrder, setSortOrder] = useState('desc');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(15);

  // Expanded abstracts tracker
  const [expandedAbstracts, setExpandedAbstracts] = useState<Record<string, boolean>>({});

  const toggleAbstract = (id: string) => {
    setExpandedAbstracts((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const loadPapers = async () => {
    setIsLoading(true);
    try {
      const data = await listPapers(request.id, {
        query: searchTerm || undefined,
        source_database: selectedDb || undefined,
        year_from: yearFrom,
        year_to: yearTo,
        has_abstract_only: hasAbstractOnly || undefined,
        has_pdf_only: hasPdfOnly || undefined,
        sort_by: sortBy,
        sort_order: sortOrder,
        page,
        page_size: pageSize,
      });
      setPapersData(data);
    } catch (err) {
      console.error('Failed to load papers:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadPapers();
  }, [
    request.id,
    searchTerm,
    selectedDb,
    yearFrom,
    yearTo,
    hasAbstractOnly,
    hasPdfOnly,
    sortBy,
    sortOrder,
    page,
    pageSize,
  ]);

  const rawCount = lastExecution?.total_raw_retrieved ?? (papersData?.total || 0);
  const uniqueCount = papersData?.total || 0;
  const dupesCount = lastExecution?.total_duplicates_removed ?? 0;

  return (
    <div style={{ maxWidth: 1080, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Top Banner / Review Overview */}
      <div className="card-dark" style={{ padding: '1.75rem 2rem' }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'flex-start', justifyContent: 'space-between', gap: '1rem' }}>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.4rem' }}>
              <div style={{ padding: '0.3rem', borderRadius: '0.4rem', background: 'rgba(129,140,248,.2)' }}>
                <BookOpen size={16} color="#a5b4fc" />
              </div>
              <span style={{ fontSize: '0.68rem', fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase', color: '#a5b4fc' }}>
                Step 3 · Literature Corpus Dashboard (Phase 1)
              </span>
            </div>
            <h2 style={{ fontFamily: 'Sora, sans-serif', fontWeight: 800, fontSize: '1.35rem', color: '#fff', marginBottom: '0.4rem' }}>
              {request.topic}
            </h2>
            <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '0.75rem', fontSize: '0.78rem', color: 'rgba(255,255,255,0.6)' }}>
              <span>Domain: <strong style={{ color: '#fff' }}>{request.domain}</strong></span>
              <span>•</span>
              <span>Timeframe: <strong style={{ color: '#fff' }}>{request.start_year}–{request.end_year}</strong></span>
              <span>•</span>
              <span>Citation: <strong style={{ color: '#fff' }}>{request.citation_style}</strong></span>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexShrink: 0 }}>
            {onProceedToScreening && (
              <button
                onClick={onProceedToScreening}
                className="btn btn-sm"
                style={{
                  background: 'linear-gradient(135deg, #0284c7, #0369a1)',
                  color: '#fff',
                  border: 'none',
                  fontWeight: 700,
                  boxShadow: '0 2px 8px rgba(2, 132, 199, 0.4)',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.4rem',
                }}
              >
                <Sparkles size={13} color="#7dd3fc" />
                <span>Screening & Evidence (Phase 2) →</span>
              </button>
            )}

            <button
              onClick={onModifyStrategy}
              className="btn btn-sm"
              style={{
                background: 'rgba(255,255,255,0.1)',
                color: 'rgba(255,255,255,0.85)',
                border: '1px solid rgba(255,255,255,0.15)',
              }}
            >
              <RotateCcw size={13} />
              <span>Modify Strategy</span>
            </button>

            <a
              href={getExportUrl(request.id, 'csv')}
              download
              className="btn btn-sm"
              style={{
                background: 'rgba(255,255,255,0.1)',
                color: '#34d399',
                border: '1px solid rgba(52,211,153,0.3)',
              }}
              title="Download normalized corpus as CSV with citation and source metadata"
            >
              <FileSpreadsheet size={13} />
              <span>Export CSV</span>
            </a>

            <a
              href={getExportUrl(request.id, 'json')}
              download
              className="btn btn-sm btn-primary"
              style={{ padding: '0.45rem 1rem' }}
              title="Export complete canonical corpus in JSON format"
            >
              <Download size={13} />
              <span>Export JSON</span>
            </a>
          </div>
        </div>

        {/* 4 Metrics Cards Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginTop: '1.5rem' }}>
          <div style={{ background: 'rgba(255,255,255,0.06)', borderRadius: '0.75rem', padding: '1rem 1.25rem', border: '1px solid rgba(255,255,255,0.08)' }}>
            <div style={{ fontSize: '0.68rem', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.45)', marginBottom: '0.35rem' }}>
              Raw Retrieved
            </div>
            <div style={{ fontSize: '1.85rem', fontWeight: 800, fontFamily: 'JetBrains Mono, monospace', color: '#fff' }}>
              {rawCount}
            </div>
            <div style={{ fontSize: '0.68rem', color: 'rgba(255,255,255,0.4)', marginTop: '0.2rem' }}>
              All queries across APIs
            </div>
          </div>

          <div style={{ background: 'rgba(99,102,241,0.15)', borderRadius: '0.75rem', padding: '1rem 1.25rem', border: '1px solid rgba(129,140,248,0.3)' }}>
            <div style={{ fontSize: '0.68rem', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: '#a5b4fc', marginBottom: '0.35rem' }}>
              Canonical Papers
            </div>
            <div style={{ fontSize: '1.85rem', fontWeight: 800, fontFamily: 'JetBrains Mono, monospace', color: '#e0e7ff' }}>
              {uniqueCount}
            </div>
            <div style={{ fontSize: '0.68rem', color: '#a5b4fc', marginTop: '0.2rem' }}>
              Unique deduplicated works
            </div>
          </div>

          <div style={{ background: 'rgba(16,185,129,0.12)', borderRadius: '0.75rem', padding: '1rem 1.25rem', border: '1px solid rgba(52,211,153,0.3)' }}>
            <div style={{ fontSize: '0.68rem', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: '#6ee7b7', marginBottom: '0.35rem' }}>
              Duplicates Merged
            </div>
            <div style={{ fontSize: '1.85rem', fontWeight: 800, fontFamily: 'JetBrains Mono, monospace', color: '#a7f3d0' }}>
              {dupesCount}
            </div>
            <div style={{ fontSize: '0.68rem', color: '#6ee7b7', marginTop: '0.2rem' }}>
              Title & DOI normalization
            </div>
          </div>

          <div style={{ background: 'rgba(255,255,255,0.06)', borderRadius: '0.75rem', padding: '1rem 1.25rem', border: '1px solid rgba(255,255,255,0.08)' }}>
            <div style={{ fontSize: '0.68rem', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.45)', marginBottom: '0.35rem' }}>
              Corpus Status
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.35rem' }}>
              <span className="status-dot success" />
              <span style={{ fontSize: '1.15rem', fontWeight: 700, color: '#34d399', textTransform: 'capitalize' }}>
                {lastExecution?.status || 'Active'}
              </span>
            </div>
            <div style={{ fontSize: '0.68rem', color: 'rgba(255,255,255,0.4)', marginTop: '0.45rem' }}>
              Persisted in SQLite database
            </div>
          </div>
        </div>

        {/* Provider Breakdown Badges */}
        {lastExecution?.provider_statuses && (
          <div style={{ marginTop: '1.25rem', paddingTop: '1rem', borderTop: '1px solid rgba(255,255,255,0.08)', display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.4)', marginRight: '0.25rem' }}>
              Academic Sources:
            </span>
            {Object.entries(lastExecution.provider_statuses).map(([prov, st]) => {
              const isSuccess = st.status === 'success';
              return (
                <div
                  key={prov}
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '0.35rem',
                    padding: '0.25rem 0.65rem',
                    borderRadius: '100px',
                    fontSize: '0.72rem',
                    fontWeight: 600,
                    background: isSuccess ? 'rgba(16,185,129,0.18)' : 'rgba(245,158,11,0.18)',
                    color: isSuccess ? '#6ee7b7' : '#fcd34d',
                    border: `1px solid ${isSuccess ? 'rgba(52,211,153,0.3)' : 'rgba(251,191,36,0.3)'}`,
                  }}
                  title={st.error || 'Provider healthy'}
                >
                  {isSuccess ? <CheckCircle2 size={12} color="#34d399" /> : <AlertTriangle size={12} color="#fbbf24" />}
                  <span style={{ textTransform: 'capitalize' }}>{prov.replace('_', ' ')}:</span>
                  <span style={{ fontFamily: 'JetBrains Mono, monospace', fontWeight: 700 }}>{st.retrieved_count}</span>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Filter and Search Controls */}
      <div className="card" style={{ padding: '1.25rem 1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'minmax(220px, 1.8fr) 1.2fr 1fr 1fr', gap: '0.75rem', alignItems: 'center' }}>
          {/* Search Input */}
          <div style={{ position: 'relative' }}>
            <Search size={15} color="#94a3b8" style={{ position: 'absolute', left: 11, top: 11 }} />
            <input
              type="text"
              placeholder="Search by title, keyword, or DOI..."
              className="input"
              style={{ paddingLeft: 34, fontSize: '0.82rem' }}
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setPage(1);
              }}
            />
          </div>

          {/* Database Filter */}
          <div>
            <select
              className="input"
              style={{ fontSize: '0.82rem' }}
              value={selectedDb}
              onChange={(e) => {
                setSelectedDb(e.target.value);
                setPage(1);
              }}
            >
              <option value="">All Databases</option>
              <option value="openalex">OpenAlex</option>
              <option value="semantic_scholar">Semantic Scholar</option>
              <option value="crossref">Crossref</option>
              <option value="arxiv">arXiv Preprints</option>
            </select>
          </div>

          {/* Sort By */}
          <div>
            <select
              className="input"
              style={{ fontSize: '0.82rem' }}
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
            >
              <option value="year">Sort: Publication Year</option>
              <option value="citations">Sort: Citations</option>
              <option value="title">Sort: Title</option>
            </select>
          </div>

          {/* Sort Order */}
          <div>
            <select
              className="input"
              style={{ fontSize: '0.82rem' }}
              value={sortOrder}
              onChange={(e) => setSortOrder(e.target.value)}
            >
              <option value="desc">Descending</option>
              <option value="asc">Ascending</option>
            </select>
          </div>
        </div>

        {/* Checkbox Toggles & Results summary */}
        <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: '0.75rem', paddingTop: '0.75rem', borderTop: '1px solid #f1f5f9', fontSize: '0.8rem', color: '#475569' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', cursor: 'pointer', userSelect: 'none' }}>
              <input
                type="checkbox"
                checked={hasAbstractOnly}
                onChange={(e) => {
                  setHasAbstractOnly(e.target.checked);
                  setPage(1);
                }}
                style={{ accentColor: '#6366f1', width: 15, height: 15 }}
              />
              <span style={{ fontWeight: 500 }}>Has Abstract</span>
            </label>

            <label style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', cursor: 'pointer', userSelect: 'none' }}>
              <input
                type="checkbox"
                checked={hasPdfOnly}
                onChange={(e) => {
                  setHasPdfOnly(e.target.checked);
                  setPage(1);
                }}
                style={{ accentColor: '#6366f1', width: 15, height: 15 }}
              />
              <span style={{ fontWeight: 500 }}>Has PDF Access</span>
            </label>
          </div>

          <div style={{ fontSize: '0.75rem', color: '#94a3b8', fontFamily: 'JetBrains Mono, monospace' }}>
            Showing <strong>{papersData?.items.length || 0}</strong> of <strong>{papersData?.total || 0}</strong> papers
          </div>
        </div>
      </div>

      {/* Papers List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
        {isLoading ? (
          <div className="card" style={{ padding: '3.5rem', textAlign: 'center', color: '#64748b' }}>
            <div className="spinner" style={{ margin: '0 auto 1rem' }} />
            <p style={{ fontWeight: 600, fontSize: '0.9rem', color: '#1e293b' }}>Filtering normalized literature corpus...</p>
            <p style={{ fontSize: '0.78rem', color: '#94a3b8', marginTop: '0.25rem' }}>Querying normalized SQLite repositories</p>
          </div>
        ) : !papersData || papersData.items.length === 0 ? (
          <div className="card" style={{ padding: '3.5rem', textAlign: 'center', color: '#64748b' }}>
            <BookOpen size={36} color="#cbd5e1" style={{ margin: '0 auto 0.75rem' }} />
            <p style={{ fontWeight: 700, fontSize: '0.95rem', color: '#1e293b' }}>No papers match your search criteria.</p>
            <p style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: '0.25rem' }}>Try clearing filters or running a broader search strategy query.</p>
          </div>
        ) : (
          papersData.items.map((paper) => {
            const isExpanded = expandedAbstracts[paper.id];
            const primarySource = paper.sources[0]?.source_database || 'openalex';
            const borderClass =
              paper.sources.length > 1
                ? 'paper-card-border-multiple'
                : `paper-card-border-${primarySource}`;

            return (
              <div
                key={paper.id}
                className={`card ${borderClass}`}
                style={{ padding: '1.25rem 1.5rem', display: 'flex', flexDirection: 'column', gap: '0.65rem' }}
              >
                {/* Title & View Details button */}
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '1rem' }}>
                  <h3
                    onClick={() => onSelectPaper(paper)}
                    style={{
                      fontFamily: 'Sora, sans-serif',
                      fontSize: '1rem',
                      fontWeight: 700,
                      color: '#0f172a',
                      cursor: 'pointer',
                      lineHeight: 1.4,
                      transition: 'color 0.15s',
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.color = '#4f46e5')}
                    onMouseLeave={(e) => (e.currentTarget.style.color = '#0f172a')}
                  >
                    {paper.title}
                  </h3>

                  <button
                    onClick={() => onSelectPaper(paper)}
                    className="btn btn-secondary btn-sm"
                    style={{ flexShrink: 0, padding: '0.35rem 0.75rem', fontSize: '0.75rem' }}
                    title="Inspect complete metadata and provenance"
                  >
                    Inspect Details
                  </button>
                </div>

                {/* Authors, Year, Venue, Citation count */}
                <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '0.5rem', fontSize: '0.78rem', color: '#475569' }}>
                  <span style={{ fontWeight: 600, color: '#1e293b' }}>
                    {paper.authors.length > 0 ? paper.authors.join(', ') : 'Unknown Authors'}
                  </span>
                  {paper.publication_year && (
                    <>
                      <span style={{ color: '#cbd5e1' }}>•</span>
                      <span style={{ fontFamily: 'JetBrains Mono, monospace', fontWeight: 500 }}>{paper.publication_year}</span>
                    </>
                  )}
                  {paper.venue && (
                    <>
                      <span style={{ color: '#cbd5e1' }}>•</span>
                      <span style={{ fontStyle: 'italic', color: '#64748b' }}>{paper.venue}</span>
                    </>
                  )}
                  {paper.citation_count !== undefined && paper.citation_count > 0 && (
                    <>
                      <span style={{ color: '#cbd5e1' }}>•</span>
                      <span style={{ color: '#059669', fontWeight: 700, background: '#ecfdf5', padding: '0.1rem 0.45rem', borderRadius: '100px', fontSize: '0.72rem' }}>
                        {paper.citation_count} citations
                      </span>
                    </>
                  )}
                </div>

                {/* Badges / Provenance */}
                <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '0.4rem', paddingTop: '0.2rem' }}>
                  {paper.sources.map((src, i) => {
                    const dbStyle = DB_COLORS[src.source_database] || { bg: '#f1f5f9', color: '#475569', border: '#e2e8f0' };
                    return (
                      <span
                        key={i}
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '0.25rem',
                          padding: '0.15rem 0.55rem',
                          borderRadius: '100px',
                          fontSize: '0.7rem',
                          fontWeight: 700,
                          background: dbStyle.bg,
                          color: dbStyle.color,
                          border: `1px solid ${dbStyle.border}`,
                        }}
                      >
                        {src.source_database}
                      </span>
                    );
                  })}

                  {paper.doi && (
                    <a
                      href={`https://doi.org/${paper.doi}`}
                      target="_blank"
                      rel="noreferrer"
                      className="badge badge-neutral"
                      style={{ fontFamily: 'JetBrains Mono, monospace', textDecoration: 'none' }}
                    >
                      DOI: {paper.doi}
                      <ExternalLink size={10} style={{ marginLeft: 3 }} />
                    </a>
                  )}

                  {paper.pdf_url && (
                    <a
                      href={paper.pdf_url}
                      target="_blank"
                      rel="noreferrer"
                      className="badge badge-success"
                      style={{ textDecoration: 'none' }}
                    >
                      <FileText size={11} style={{ marginRight: 2 }} />
                      PDF Available
                      <ExternalLink size={10} style={{ marginLeft: 3 }} />
                    </a>
                  )}

                  {paper.publication_type && (
                    <span className="badge badge-neutral" style={{ textTransform: 'capitalize' }}>
                      {paper.publication_type}
                    </span>
                  )}
                </div>

                {/* Abstract Preview */}
                {paper.abstract && (
                  <div style={{ paddingTop: '0.35rem', fontSize: '0.8rem', color: '#475569', lineHeight: 1.55 }}>
                    <p className={isExpanded ? '' : 'line-clamp-2'}>
                      {paper.abstract}
                    </p>
                    <button
                      onClick={() => toggleAbstract(paper.id)}
                      style={{
                        background: 'none',
                        border: 'none',
                        color: '#4f46e5',
                        fontWeight: 600,
                        fontSize: '0.74rem',
                        cursor: 'pointer',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '0.2rem',
                        marginTop: '0.35rem',
                        padding: 0,
                      }}
                    >
                      {isExpanded ? (
                        <><span>Show Less</span><ChevronUp size={13} /></>
                      ) : (
                        <><span>Read Full Abstract</span><ChevronDown size={13} /></>
                      )}
                    </button>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Pagination Bar */}
      {papersData && papersData.total_pages > 1 && (
        <div className="card" style={{ padding: '0.9rem 1.25rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.82rem' }}>
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="btn btn-secondary btn-sm"
          >
            Previous
          </button>
          <span style={{ fontFamily: 'JetBrains Mono, monospace', color: '#64748b', fontWeight: 600 }}>
            Page {page} of {papersData.total_pages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(papersData.total_pages, p + 1))}
            disabled={page === papersData.total_pages}
            className="btn btn-secondary btn-sm"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
};
