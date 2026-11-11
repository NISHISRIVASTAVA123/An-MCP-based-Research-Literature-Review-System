import React, { useState, useEffect } from 'react';
import {
  ResearchRequest,
  Paper,
  PaperListResponse,
  SearchExecutionSummary,
} from '../types';
import { listPapers, getExportUrl, getSearchHistory } from '../services/api';
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
  Sparkles,
  BookOpen,
} from 'lucide-react';

interface SearchDashboardProps {
  request: ResearchRequest;
  onModifyStrategy: () => void;
  onSelectPaper: (paper: Paper) => void;
  lastExecution?: SearchExecutionSummary;
}

export const SearchDashboard: React.FC<SearchDashboardProps> = ({
  request,
  onModifyStrategy,
  onSelectPaper,
  lastExecution,
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
  }, [request.id, searchTerm, selectedDb, yearFrom, yearTo, hasAbstractOnly, hasPdfOnly, sortBy, sortOrder, page, pageSize]);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header & Metrics Summary */}
      <div className="academic-card p-6 bg-white border border-slate-200">
        <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4 border-b border-slate-100 pb-5 mb-5">
          <div>
            <div className="flex items-center gap-2 text-indigo-600 text-xs font-semibold uppercase tracking-wider mb-1">
              <BookOpen className="h-4 w-4" />
              <span>Academic Literature Retrieval Dashboard</span>
            </div>
            <h2 className="text-xl font-bold font-serif text-slate-900">{request.topic}</h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Domain: {request.domain} • Scope: {request.start_year}–{request.end_year} • Citation: {request.citation_style}
            </p>
          </div>

          <div className="flex items-center gap-2.5">
            <button
              onClick={onModifyStrategy}
              className="btn-secondary text-xs py-2 px-3 flex items-center gap-1.5"
            >
              <RotateCcw className="h-3.5 w-3.5" />
              <span>Search Strategy</span>
            </button>

            {/* Export buttons */}
            <a
              href={getExportUrl(request.id, 'csv')}
              download
              className="btn-secondary text-xs py-2 px-3 flex items-center gap-1.5 text-slate-700 hover:text-indigo-600"
              title="Export all collected papers as CSV with provenance metadata"
            >
              <Download className="h-3.5 w-3.5" />
              <span>Export CSV</span>
            </a>

            <a
              href={getExportUrl(request.id, 'json')}
              download
              className="btn-primary text-xs py-2 px-3.5 flex items-center gap-1.5 shadow-xs"
              title="Export complete normalized corpus as JSON"
            >
              <Download className="h-3.5 w-3.5" />
              <span>Export JSON</span>
            </a>
          </div>
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200/80">
            <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
              Raw Records Retrieved
            </span>
            <span className="text-2xl font-bold text-slate-800 font-mono">
              {lastExecution?.total_raw_retrieved ?? (papersData?.total || 0)}
            </span>
          </div>

          <div className="p-3.5 rounded-lg bg-indigo-50/60 border border-indigo-100">
            <span className="text-[11px] font-semibold text-indigo-700 uppercase tracking-wider block">
              Unique Canonical Papers
            </span>
            <span className="text-2xl font-bold text-indigo-900 font-mono">
              {papersData?.total || 0}
            </span>
          </div>

          <div className="p-3.5 rounded-lg bg-emerald-50/60 border border-emerald-100">
            <span className="text-[11px] font-semibold text-emerald-700 uppercase tracking-wider block">
              Duplicates Merged
            </span>
            <span className="text-2xl font-bold text-emerald-800 font-mono">
              {lastExecution?.total_duplicates_removed ?? 0}
            </span>
          </div>

          <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200/80">
            <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
              Retrieval Status
            </span>
            <div className="flex items-center gap-1.5 mt-1">
              <span className="h-2.5 w-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
              <span className="text-xs font-semibold text-slate-700 capitalize">
                {lastExecution?.status || 'Active'}
              </span>
            </div>
          </div>
        </div>

        {/* Provider Breakdown Badges */}
        {lastExecution?.provider_statuses && (
          <div className="mt-4 pt-3 border-t border-slate-100 flex flex-wrap items-center gap-2">
            <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider mr-1">
              Providers:
            </span>
            {Object.entries(lastExecution.provider_statuses).map(([prov, st]) => (
              <span
                key={prov}
                className={`badge ${
                  st.status === 'success'
                    ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                    : 'bg-amber-50 text-amber-800 border-amber-200'
                }`}
                title={st.error || 'Provider healthy'}
              >
                {st.status === 'success' ? (
                  <CheckCircle2 className="h-3 w-3 text-emerald-600 mr-1" />
                ) : (
                  <AlertTriangle className="h-3 w-3 text-amber-600 mr-1" />
                )}
                <span className="capitalize">{prov}:</span> {st.retrieved_count}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Filter and Search Controls */}
      <div className="academic-card p-4 bg-white space-y-3">
        <div className="grid grid-cols-1 sm:grid-cols-12 gap-3 items-center">
          {/* Search Input */}
          <div className="sm:col-span-5 relative">
            <Search className="h-4 w-4 text-slate-400 absolute left-3 top-3" />
            <input
              type="text"
              placeholder="Filter by title, abstract keyword, or DOI..."
              className="input-base pl-9 text-xs"
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setPage(1);
              }}
            />
          </div>

          {/* Database Filter */}
          <div className="sm:col-span-3">
            <select
              className="input-base text-xs"
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
          <div className="sm:col-span-2">
            <select
              className="input-base text-xs"
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
            >
              <option value="year">Sort: Year</option>
              <option value="title">Sort: Title</option>
              <option value="citations">Sort: Citations</option>
            </select>
          </div>

          <div className="sm:col-span-2">
            <select
              className="input-base text-xs"
              value={sortOrder}
              onChange={(e) => setSortOrder(e.target.value)}
            >
              <option value="desc">Descending</option>
              <option value="asc">Ascending</option>
            </select>
          </div>
        </div>

        {/* Checkbox Toggles */}
        <div className="flex flex-wrap items-center gap-4 pt-2 text-xs text-slate-600 border-t border-slate-100">
          <label className="flex items-center gap-1.5 cursor-pointer">
            <input
              type="checkbox"
              checked={hasAbstractOnly}
              onChange={(e) => {
                setHasAbstractOnly(e.target.checked);
                setPage(1);
              }}
              className="rounded border-slate-300 text-indigo-600 h-3.5 w-3.5"
            />
            <span>Has Abstract Only</span>
          </label>

          <label className="flex items-center gap-1.5 cursor-pointer">
            <input
              type="checkbox"
              checked={hasPdfOnly}
              onChange={(e) => {
                setHasPdfOnly(e.target.checked);
                setPage(1);
              }}
              className="rounded border-slate-300 text-indigo-600 h-3.5 w-3.5"
            />
            <span>Has PDF Only</span>
          </label>

          <span className="text-slate-300">|</span>
          <span className="text-[11px] text-slate-400 font-mono">
            Showing {papersData?.items.length || 0} of {papersData?.total || 0} papers
          </span>
        </div>
      </div>

      {/* Papers List */}
      <div className="space-y-3">
        {isLoading ? (
          <div className="academic-card p-12 text-center text-slate-500">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mb-3"></div>
            <p className="text-sm font-medium">Loading normalized literature corpus...</p>
          </div>
        ) : !papersData || papersData.items.length === 0 ? (
          <div className="academic-card p-12 text-center text-slate-500">
            <BookOpen className="h-8 w-8 text-slate-300 mx-auto mb-2" />
            <p className="text-sm font-medium text-slate-700">No papers match your filter criteria.</p>
            <p className="text-xs text-slate-400 mt-1">Try clearing filters or running a broader search query.</p>
          </div>
        ) : (
          papersData.items.map((paper) => {
            const isExpanded = expandedAbstracts[paper.id];
            return (
              <div
                key={paper.id}
                className="academic-card p-5 hover:border-indigo-200 transition-all bg-white"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="space-y-1.5 flex-1">
                    {/* Title */}
                    <h3
                      onClick={() => onSelectPaper(paper)}
                      className="text-base font-bold font-serif text-slate-900 hover:text-indigo-600 cursor-pointer transition-colors"
                    >
                      {paper.title}
                    </h3>

                    {/* Authors & Meta */}
                    <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-600">
                      <span className="font-medium text-slate-700">
                        {paper.authors.length > 0 ? paper.authors.join(', ') : 'Unknown Authors'}
                      </span>
                      {paper.publication_year && (
                        <>
                          <span className="text-slate-300">•</span>
                          <span className="font-mono">{paper.publication_year}</span>
                        </>
                      )}
                      {paper.venue && (
                        <>
                          <span className="text-slate-300">•</span>
                          <span className="italic text-slate-500">{paper.venue}</span>
                        </>
                      )}
                      {paper.citation_count !== undefined && paper.citation_count > 0 && (
                        <>
                          <span className="text-slate-300">•</span>
                          <span className="text-emerald-700 font-semibold">
                            {paper.citation_count} citations
                          </span>
                        </>
                      )}
                    </div>

                    {/* Badges / Provenance */}
                    <div className="flex flex-wrap items-center gap-2 pt-1">
                      {paper.sources.map((src, i) => (
                        <span key={i} className={`badge badge-${src.source_database}`}>
                          {src.source_database}
                        </span>
                      ))}

                      {paper.doi && (
                        <a
                          href={`https://doi.org/${paper.doi}`}
                          target="_blank"
                          rel="noreferrer"
                          className="badge bg-slate-100 text-slate-700 border border-slate-200 font-mono hover:text-indigo-600"
                        >
                          DOI: {paper.doi}
                          <ExternalLink className="h-2.5 w-2.5 ml-1" />
                        </a>
                      )}

                      {paper.pdf_url && (
                        <a
                          href={paper.pdf_url}
                          target="_blank"
                          rel="noreferrer"
                          className="badge bg-emerald-50 text-emerald-800 border border-emerald-200 hover:bg-emerald-100"
                        >
                          <FileText className="h-3 w-3 mr-1" />
                          PDF Available
                          <ExternalLink className="h-2.5 w-2.5 ml-1" />
                        </a>
                      )}

                      {paper.publication_type && (
                        <span className="badge bg-slate-50 text-slate-500 border border-slate-200">
                          {paper.publication_type}
                        </span>
                      )}
                    </div>

                    {/* Abstract Preview */}
                    {paper.abstract && (
                      <div className="pt-2 text-xs text-slate-600">
                        <p className={isExpanded ? '' : 'line-clamp-2'}>
                          {paper.abstract}
                        </p>
                        <button
                          onClick={() => toggleAbstract(paper.id)}
                          className="text-[11px] font-semibold text-indigo-600 hover:text-indigo-800 mt-1 flex items-center gap-0.5"
                        >
                          {isExpanded ? (
                            <>
                              <span>Show Less</span>
                              <ChevronUp className="h-3 w-3" />
                            </>
                          ) : (
                            <>
                              <span>Read Abstract</span>
                              <ChevronDown className="h-3 w-3" />
                            </>
                          )}
                        </button>
                      </div>
                    )}
                  </div>

                  <button
                    onClick={() => onSelectPaper(paper)}
                    className="p-2 text-slate-400 hover:text-indigo-600 rounded-md hover:bg-slate-50 transition-colors text-xs font-medium"
                    title="View full metadata & provenance"
                  >
                    View Details
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Pagination Bar */}
      {papersData && papersData.total_pages > 1 && (
        <div className="academic-card p-4 bg-white flex items-center justify-between text-xs">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="btn-secondary py-1.5 px-3 disabled:opacity-40"
          >
            Previous
          </button>
          <span className="font-mono text-slate-600">
            Page {page} of {papersData.total_pages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(papersData.total_pages, p + 1))}
            disabled={page === papersData.total_pages}
            className="btn-secondary py-1.5 px-3 disabled:opacity-40"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
};

