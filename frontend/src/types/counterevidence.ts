export type CounterevidenceRelevance =
  | 'direct_counterevidence'
  | 'partial_counterevidence'
  | 'related_evidence'
  | 'not_relevant'
  | 'insufficient_information';

export type CounterevidenceImpact =
  | 'strongly_challenged'
  | 'partially_challenged'
  | 'weakly_challenged'
  | 'unchallenged'
  | 'inconclusive';

export type CounterevidenceLevel =
  | 'level_1_fulltext_passage'
  | 'level_2_abstract_supported'
  | 'level_3_citation_inferred'
  | 'level_4_metadata_only';

export interface CounterevidenceClaim {
  id: string;
  gap_id: string;
  claim_text: string;
  claim_type: string;
  claim_order: number;
  confidence_score: number;
  created_at: string;
}

export interface CounterevidenceQuery {
  id: string;
  claim_id?: string;
  gap_id: string;
  query_text: string;
  query_type: string;
  rationale?: string;
  results_count: number;
  created_at: string;
}

export interface CounterevidencePublication {
  id: string;
  gap_id: string;
  query_id?: string;
  title: string;
  authors?: string[];
  year?: number;
  venue?: string;
  doi?: string;
  url?: string;
  abstract?: string;
  source_provider: string;
  access_status: string;
  fulltext_available: boolean;
  discovery_tag: string;
  created_at: string;
}

export interface CounterevidenceEvidenceItem {
  id: string;
  assessment_id: string;
  publication_id: string;
  passage_text: string;
  page_number?: number;
  section_heading?: string;
  is_quote: boolean;
  verification_status: string;
  evidence_level: CounterevidenceLevel;
  created_at: string;
}

export interface CounterevidenceAssessment {
  id: string;
  gap_id: string;
  publication_id: string;
  claim_id?: string;
  relevance: CounterevidenceRelevance;
  assessment_notes?: string;
  evidence_level: CounterevidenceLevel;
  human_reviewed: boolean;
  human_reviewer_notes?: string;
  human_override_relevance?: CounterevidenceRelevance;
  publication?: CounterevidencePublication;
  evidence_passages: CounterevidenceEvidenceItem[];
  created_at: string;
  updated_at: string;
}

export interface CounterevidenceProfile {
  id: string;
  gap_id: string;
  total_queries_executed: number;
  total_publications_found: number;
  direct_counterevidence_count: number;
  partial_counterevidence_count: number;
  related_evidence_count: number;
  not_relevant_count: number;
  impact_assessment: CounterevidenceImpact;
  executive_summary?: string;
  unresolved_claims?: string[];
  limitations?: string[];
  created_at: string;
  updated_at: string;
}

export interface CounterevidenceSearchRun {
  id: string;
  gap_id?: string;
  scope_description?: string;
  total_gaps_searched: number;
  total_queries_executed: number;
  total_publications_found: number;
  status: string;
  error_message?: string;
  started_at: string;
  completed_at?: string;
  created_at: string;
}
