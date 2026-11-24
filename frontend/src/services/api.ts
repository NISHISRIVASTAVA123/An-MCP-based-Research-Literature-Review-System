import {
  ResearchRequest,
  ResearchRequestCreate,
  ResearchRequestSummary,
  SearchStrategy,
  StrategyQuery,
  PaperListResponse,
  Paper,
  SearchExecutionResult,
  SearchExecutionSummary,
} from '../types';

const API_BASE = '/api';

export async function createResearchRequest(payload: ResearchRequestCreate): Promise<ResearchRequest> {
  const res = await fetch(`${API_BASE}/research-requests`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to create request' }));
    throw new Error(err.detail || 'Failed to create request');
  }
  return res.json();
}

export async function listResearchRequests(): Promise<ResearchRequestSummary[]> {
  const res = await fetch(`${API_BASE}/research-requests`);
  if (!res.ok) throw new Error('Failed to fetch request history');
  return res.json();
}

export async function getResearchRequest(id: string): Promise<ResearchRequest> {
  const res = await fetch(`${API_BASE}/research-requests/${id}`);
  if (!res.ok) throw new Error('Failed to load request');
  return res.json();
}

export async function deleteResearchRequest(id: string): Promise<void> {
  const res = await fetch(`${API_BASE}/research-requests/${id}`, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error('Failed to delete request');
}

export async function generateSearchStrategy(requestId: string): Promise<SearchStrategy> {
  const res = await fetch(`${API_BASE}/research-requests/${requestId}/strategy`, {
    method: 'POST',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to generate search strategy' }));
    throw new Error(err.detail || 'Failed to generate search strategy');
  }
  return res.json();
}

export async function getSearchStrategy(requestId: string): Promise<SearchStrategy | null> {
  const res = await fetch(`${API_BASE}/research-requests/${requestId}/strategy`);
  if (res.status === 404) return null;
  if (!res.ok) throw new Error('Failed to load strategy');
  return res.json();
}

export async function updateSearchStrategy(
  requestId: string,
  payload: { queries: StrategyQuery[]; concepts?: string[]; keywords?: string[] }
): Promise<SearchStrategy> {
  const res = await fetch(`${API_BASE}/research-requests/${requestId}/strategy`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to update strategy');
  return res.json();
}

export async function executeSearch(
  requestId: string,
  maxPapersPerProvider?: number
): Promise<SearchExecutionResult> {
  const res = await fetch(`${API_BASE}/research-requests/${requestId}/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ max_papers_per_provider: maxPapersPerProvider }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Search execution failed' }));
    throw new Error(err.detail || 'Search execution failed');
  }
  return res.json();
}

export async function getSearchHistory(requestId: string): Promise<SearchExecutionSummary[]> {
  const res = await fetch(`${API_BASE}/research-requests/${requestId}/search-history`);
  if (!res.ok) throw new Error('Failed to fetch search history');
  return res.json();
}

export async function listPapers(
  requestId: string,
  params: {
    query?: string;
    year_from?: number;
    year_to?: number;
    source_database?: string;
    has_abstract_only?: boolean;
    has_pdf_only?: boolean;
    sort_by?: string;
    sort_order?: string;
    page?: number;
    page_size?: number;
  }
): Promise<PaperListResponse> {
  const searchParams = new URLSearchParams();
  if (params.query) searchParams.append('query', params.query);
  if (params.year_from) searchParams.append('year_from', params.year_from.toString());
  if (params.year_to) searchParams.append('year_to', params.year_to.toString());
  if (params.source_database) searchParams.append('source_database', params.source_database);
  if (params.has_abstract_only) searchParams.append('has_abstract_only', 'true');
  if (params.has_pdf_only) searchParams.append('has_pdf_only', 'true');
  if (params.sort_by) searchParams.append('sort_by', params.sort_by);
  if (params.sort_order) searchParams.append('sort_order', params.sort_order);
  if (params.page) searchParams.append('page', params.page.toString());
  if (params.page_size) searchParams.append('page_size', params.page_size.toString());

  const res = await fetch(`${API_BASE}/research-requests/${requestId}/papers?${searchParams.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch papers');
  return res.json();
}

export async function getPaperDetails(paperId: string): Promise<Paper> {
  const res = await fetch(`${API_BASE}/papers/${paperId}`);
  if (!res.ok) throw new Error('Failed to fetch paper details');
  return res.json();
}

export function getExportUrl(requestId: string, format: 'csv' | 'json'): string {
  return `${API_BASE}/research-requests/${requestId}/export?format=${format}`;
}


// --- Phase 2: Paper Screening & Evidence Extraction API ---

import {
  ScreeningRun,
  ScreeningDecision,
  DocumentStatus,
  DocumentRetrieveResponse,
  EvidenceRecord,
  EvidencePassage,
} from '../types';

export async function createScreeningRun(requestId: string): Promise<ScreeningRun> {
  const res = await fetch(`${API_BASE}/research-requests/${requestId}/screening-runs`, {
    method: 'POST',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to execute screening run' }));
    throw new Error(err.detail || 'Failed to execute screening run');
  }
  return res.json();
}

export async function listScreeningRuns(requestId: string): Promise<ScreeningRun[]> {
  const res = await fetch(`${API_BASE}/research-requests/${requestId}/screening-runs`);
  if (!res.ok) throw new Error('Failed to load screening runs');
  return res.json();
}

export async function getScreeningResults(
  requestId: string,
  runId?: string,
  decision?: string
): Promise<ScreeningDecision[]> {
  const params = new URLSearchParams();
  if (runId) params.append('run_id', runId);
  if (decision) params.append('decision', decision);
  const res = await fetch(`${API_BASE}/research-requests/${requestId}/screening-results?${params.toString()}`);
  if (!res.ok) throw new Error('Failed to load screening results');
  return res.json();
}

export async function overrideScreeningDecision(
  paperId: string,
  decision: 'included' | 'excluded' | 'needs_human_review',
  reviewerNotes: string
): Promise<ScreeningDecision> {
  const res = await fetch(`${API_BASE}/papers/${paperId}/screening-decision`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ decision, reviewer_notes: reviewerNotes }),
  });
  if (!res.ok) throw new Error('Failed to override screening decision');
  return res.json();
}

export async function retrievePaperFullText(paperId: string): Promise<DocumentRetrieveResponse> {
  const res = await fetch(`${API_BASE}/papers/${paperId}/retrieve-full-text`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to retrieve full text');
  return res.json();
}

export async function uploadPaperPdf(paperId: string, file: File): Promise<DocumentRetrieveResponse> {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${API_BASE}/papers/${paperId}/upload-pdf`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) throw new Error('Failed to upload PDF');
  return res.json();
}

export async function getDocumentStatus(paperId: string): Promise<DocumentStatus> {
  const res = await fetch(`${API_BASE}/papers/${paperId}/document-status`);
  if (!res.ok) throw new Error('Failed to fetch document status');
  return res.json();
}

export async function extractPaperEvidence(paperId: string, backend?: string): Promise<EvidenceRecord> {
  const params = new URLSearchParams();
  if (backend) params.append('backend', backend);
  const res = await fetch(`${API_BASE}/papers/${paperId}/extract-evidence?${params.toString()}`, {
    method: 'POST',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to extract evidence' }));
    throw new Error(err.detail || 'Failed to extract evidence');
  }
  return res.json();
}

export async function getPaperEvidence(paperId: string): Promise<EvidenceRecord | null> {
  const res = await fetch(`${API_BASE}/papers/${paperId}/evidence`);
  if (!res.ok) throw new Error('Failed to fetch paper evidence');
  return res.json();
}

export async function getEvidencePassages(paperId: string): Promise<EvidencePassage[]> {
  const res = await fetch(`${API_BASE}/papers/${paperId}/evidence-passages`);
  if (!res.ok) throw new Error('Failed to fetch evidence passages');
  return res.json();
}

export async function updateEvidencePassage(
  passageId: string,
  payload: {
    verification_status: string;
    statement?: string;
    verbatim_passage?: string;
    user_notes?: string;
  }
): Promise<EvidencePassage> {
  const res = await fetch(`${API_BASE}/evidence/passages/${passageId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to update evidence passage');
  return res.json();
}

// -------------------------------------------------------------
// Phase 3: Evidence Graph API Methods
// -------------------------------------------------------------

import {
  EvidenceGraphData,
  GraphStatistics,
  GraphBuildRun,
  GraphValidationRecord,
  ProvenanceChain,
} from '../types/graph';

export async function buildEvidenceGraph(requestId: string): Promise<GraphBuildRun> {
  const res = await fetch(`${API_BASE}/research-requests/${requestId}/evidence-graph/build`, {
    method: 'POST',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to build evidence graph' }));
    throw new Error(err.detail || 'Failed to build evidence graph');
  }
  return res.json();
}

export async function synchronizeEvidenceGraph(requestId: string): Promise<GraphBuildRun> {
  const res = await fetch(`${API_BASE}/research-requests/${requestId}/evidence-graph/synchronize`, {
    method: 'POST',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to synchronize evidence graph' }));
    throw new Error(err.detail || 'Failed to synchronize evidence graph');
  }
  return res.json();
}

export async function getEvidenceGraph(
  requestId: string,
  nodeType?: string,
  paperId?: string
): Promise<EvidenceGraphData> {
  const params = new URLSearchParams();
  if (nodeType) params.append('node_type', nodeType);
  if (paperId) params.append('paper_id', paperId);
  const res = await fetch(`${API_BASE}/research-requests/${requestId}/evidence-graph?${params.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch evidence graph');
  return res.json();
}

export async function getGraphStatistics(requestId: string): Promise<GraphStatistics> {
  const res = await fetch(`${API_BASE}/research-requests/${requestId}/evidence-graph/statistics`);
  if (!res.ok) throw new Error('Failed to fetch graph statistics');
  return res.json();
}

export async function getGraphValidation(requestId: string): Promise<GraphValidationRecord> {
  const res = await fetch(`${API_BASE}/research-requests/${requestId}/evidence-graph/validation`);
  if (!res.ok) throw new Error('Failed to fetch graph validation report');
  return res.json();
}

export async function getGraphBuildHistory(requestId: string): Promise<GraphBuildRun[]> {
  const res = await fetch(`${API_BASE}/research-requests/${requestId}/evidence-graph/build-history`);
  if (!res.ok) throw new Error('Failed to fetch graph build history');
  return res.json();
}

export async function getClaimProvenance(claimId: string): Promise<ProvenanceChain> {
  const res = await fetch(`${API_BASE}/evidence-graph/claims/${claimId}/provenance`);
  if (!res.ok) throw new Error('Failed to fetch claim provenance trace');
  return res.json();
}

