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


// --- Phase 2: Paper Screening & Evidence Extraction Types ---

export interface ScreeningDecision {
  id: string;
  run_id: string;
  paper_id: string;
  paper_title?: string;
  paper_authors: string[];
  paper_year?: number;
  paper_venue?: string;
  has_abstract: boolean;
  has_pdf: boolean;
  decision: "included" | "excluded" | "needs_human_review";
  stage: string;
  reason: string;
  criteria_evaluated: string[];
  criteria_satisfied: string[];
  criteria_unsatisfied: string[];
  missing_information: string[];
  confidence_score?: number;
  screening_method: string;
  is_human_override: boolean;
  original_decision?: string;
  reviewer_notes?: string;
  reviewed_at?: string;
  created_at: string;
}

export interface ScreeningRun {
  id: string;
  request_id: string;
  run_number: number;
  criteria_snapshot: Record<string, any>;
  total_papers: number;
  included_count: number;
  excluded_count: number;
  review_needed_count: number;
  executed_at: string;
}

export interface DocumentStatus {
  paper_id: string;
  has_document: boolean;
  document_id?: string;
  source_type?: string;
  file_size_bytes: number;
  page_count: number;
  extraction_status: string;
  section_headings: string[];
  total_characters_extracted: number;
  error_details?: string;
  retrieved_at?: string;
}

export interface DocumentRetrieveResponse {
  paper_id: string;
  success: boolean;
  document_id?: string;
  source_type: string;
  source_url?: string;
  extraction_status: string;
  page_count: number;
  message: string;
}

export interface EvidencePassage {
  id: string;
  paper_id: string;
  category: string;
  statement: string;
  verbatim_passage?: string;
  page_number?: number;
  section_heading?: string;
  char_start?: number;
  char_end?: number;
  verification_status: "machine_extracted" | "user_verified" | "flagged_incorrect" | "unsupported_needs_review";
  user_notes?: string;
  created_at: string;
}

export interface EvidenceRecord {
  id: string;
  paper_id: string;
  extraction_run_id: string;
  source_scope: "full_text" | "abstract_only";
  extractor_backend: string;
  research_objective: {
    problem_statement: string;
    motivation?: string;
    significance?: string;
    supporting_passage?: string;
    page_number?: number;
    section_heading?: string;
  };
  methodology: {
    items: Array<{
      approach_name: string;
      approach_type: string;
      description?: string;
      baselines_compared: string[];
      experimental_setup?: string;
      supporting_passage?: string;
      page_number?: number;
      section_heading?: string;
    }>;
  };
  datasets: Array<{
    dataset_name: string;
    source_or_origin?: string;
    reported_sample_size?: string;
    train_test_split?: string;
    modality?: string;
    supporting_passage?: string;
    page_number?: number;
    section_heading?: string;
  }>;
  evaluation_metrics: Array<{
    metric_name: string;
    reported_value: string;
    comparator_baseline_value?: string;
    experimental_context?: string;
    supporting_passage?: string;
    page_number?: number;
    section_heading?: string;
  }>;
  findings: Array<{
    finding_statement: string;
    percentage_gain_or_delta?: string;
    is_statistically_tested?: boolean;
    supporting_passage?: string;
    page_number?: number;
    section_heading?: string;
  }>;
  limitations: Array<{
    limitation_text: string;
    limitation_type: string;
    aspect?: string;
    supporting_passage?: string;
    page_number?: number;
    section_heading?: string;
  }>;
  future_work: Array<{
    direction_text: string;
    potential_impact?: string;
    supporting_passage?: string;
    page_number?: number;
    section_heading?: string;
  }>;
  contributions: string[];
  uncertainties: string[];
  is_human_edited: boolean;
  human_notes?: string;
  passages: EvidencePassage[];
  created_at: string;
  updated_at: string;
}

export * from './counterevidence';
