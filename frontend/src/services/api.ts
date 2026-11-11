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

