export interface ResearchQuestion {
  id?: string;
  question_text: string;
  order_index?: number;
}

export interface ResearchRequestCreate {
  topic: string;
  objective: string;
  domain: string;
  start_year: number;
  end_year: number;
  max_papers: number;
  citation_style: string;
  research_questions: string[];
  inclusion_criteria: string[];
  exclusion_criteria: string[];
  preferred_databases: string[];
  publication_types: string[];
  specific_dois: string[];
}

export interface ResearchRequest {
  id: string;
  topic: string;
  objective: string;
  domain: string;
  start_year: number;
  end_year: number;
  max_papers: number;
  citation_style: string;
  inclusion_criteria: string[];
  exclusion_criteria: string[];
  preferred_databases: string[];
  publication_types: string[];
  specific_dois: string[];
  created_at: string;
  updated_at: string;
  questions: ResearchQuestion[];
  has_strategy: boolean;
  has_retrieved_papers: boolean;
  total_papers_count: number;
}

export interface ResearchRequestSummary {
  id: string;
  topic: string;
  objective: string;
  domain: string;
  start_year: number;
  end_year: number;
  max_papers: number;
  created_at: string;
  updated_at: string;
  total_papers: number;
  total_questions: number;
  has_strategy: boolean;
}

export interface StrategyQuery {
  id?: string;
  target_database: string;
  query_text: string;
  is_enabled: boolean;
  order_index?: number;
}

export interface SearchStrategy {
  id: string;
  request_id: string;
  concepts: string[];
  keywords: string[];
  synonyms: Record<string, string[]>;
  query_combinations: string[];
  queries: StrategyQuery[];
  created_at: string;
  updated_at: string;
}

export interface PaperSource {
  id: string;
  paper_id: string;
  source_database: string;
  external_source_id?: string;
  source_url?: string;
  raw_metadata: Record<string, any>;
  retrieved_at: string;
}

export interface Paper {
  id: string;
  request_id: string;
  title: string;
  normalized_title: string;
  authors: string[];
  abstract?: string;
  publication_year?: number;
  publication_date?: string;
  doi?: string;
  url?: string;
  pdf_url?: string;
  venue?: string;
  publication_type?: string;
  keywords: string[];
  citation_count?: number;
  has_abstract: boolean;
  has_pdf: boolean;
  has_doi: boolean;
  is_open_access: boolean;
  created_at: string;
  sources: PaperSource[];
}

export interface PaperListResponse {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  items: Paper[];
}

export interface ProviderStatus {
  status: "success" | "failed" | "rate_limited" | "running";
  retrieved_count: number;
  error?: string;
}

export interface SearchExecutionResult {
  execution_id: string;
  status: string;
  total_raw_retrieved: number;
  total_unique_papers: number;
  total_duplicates_removed: number;
  new_papers_saved: number;
  papers_updated: number;
  provider_statuses: Record<string, ProviderStatus>;
  queries_executed: string[];
}

export interface SearchExecutionSummary {
  id: string;
  request_id: string;
  executed_at: string;
  status: string;
  total_raw_retrieved: number;
  total_unique_papers: number;
  total_duplicates_removed: number;
  provider_statuses: Record<string, ProviderStatus>;
  queries_executed: string[];
}

