export interface SynthesisRun {
  id: str;
  research_request_id: string;
  run_number: number;
  status: 'pending' | 'retrieving_evidence' | 'building_comparison' | 'identifying_themes' | 'analysing_patterns' | 'generating_synthesis' | 'generating_candidate_gaps' | 'completed' | 'partially_completed' | 'failed' | 'cancelled';
  selected_paper_ids: string[];
  evidence_graph_version?: string;
  synthesis_configuration: Record<string, any>;
  prompt_version?: string;
  model_provider?: string;
  model_name?: string;
  summary_narrative: Record<string, any>;
  execution_started_at?: string;
  execution_completed_at?: string;
  error_details?: string;
  theme_count: number;
  pattern_count: number;
  gap_count: number;
  created_at: string;
  updated_at: string;
}

type str = string;

export interface LiteratureTheme {
  id: string;
  synthesis_run_id: string;
  name: string;
  description: string;
  theme_category: 'methodological' | 'empirical' | 'application' | 'theoretical' | 'evaluation' | string;
  related_concepts: string[];
  associated_paper_ids: string[];
  supporting_claim_ids: string[];
  supporting_evidence_ids: string[];
  frequency: number;
  confidence: number;
  confidence_explanation?: string;
  known_limitations?: string;
  created_at: string;
}

export interface LiteraturePattern {
  id: string;
  synthesis_run_id: string;
  pattern_type: 'methodology' | 'dataset' | 'model' | 'evaluation' | 'cross_limitation' | 'publication_trend' | string;
  description: string;
  observed_data: Record<string, any>;
  related_paper_ids: string[];
  related_evidence_ids: string[];
  interpretation: string;
  confidence: number;
  limitations?: string;
  created_at: string;
}

export interface GapEvidenceLink {
  id: string;
  candidate_gap_id: string;
  evidence_id?: string;
  claim_id?: string;
  paper_id: string;
  paper_title?: string;
  relationship_type: string;
  contribution_explanation: string;
  relevance_score: number;
  exact_passage?: string;
  section_heading?: string;
  page_number?: number;
  created_at: string;
}

export interface HumanReviewRecord {
  id: string;
  candidate_gap_id: string;
  reviewer_reference: string;
  review_action: 'accept' | 'reject' | 'request_evidence' | 'edit' | string;
  original_value: Record<string, any>;
  revised_value: Record<string, any>;
  reviewer_comment?: string;
  created_at: string;
}

export interface CandidateResearchGap {
  id: string;
  synthesis_run_id: string;
  research_request_id: string;
  title: string;
  description: string;
  category: 'methodological_gap' | 'empirical_gap' | 'dataset_or_benchmark_gap' | 'evaluation_gap' | 'generalisation_gap' | 'reproducibility_gap' | 'theoretical_gap' | 'deployment_gap' | 'interdisciplinary_gap' | 'unclassified' | string;
  research_domain: string;
  related_research_questions: string[];
  rationale: string;
  observed_pattern: string;
  scope: string;
  preliminary_confidence: number;
  confidence_explanation: string;
  assumptions: string[];
  known_limitations: string[];
  potential_counterexamples: string[];
  unresolved_questions: string[];
  suggested_validation_queries: string[];
  supporting_paper_ids: string[];
  supporting_claim_ids: string[];
  supporting_finding_ids: string[];
  supporting_limitation_ids: string[];
  supporting_evidence_ids: string[];
  generation_status: 'provisional' | 'evidence_grounded' | 'weak_evidence' | 'flagged' | string;
  human_review_status: 'pending_review' | 'accepted_for_further_investigation' | 'rejected' | 'requires_more_evidence' | 'edited_by_reviewer' | string;
  created_at: string;
  updated_at: string;
  evidence_links?: GapEvidenceLink[];
  review_records?: HumanReviewRecord[];
}

export interface PaperComparisonRow {
  paper_id: string;
  title: string;
  authors: string[];
  year?: number;
  venue?: string;
  research_objectives: string[];
  research_questions: string[];
  methodologies: string[];
  models: string[];
  datasets: string[];
  metrics: string[];
  experimental_setup?: string;
  main_findings: string[];
  reported_limitations: string[];
  future_directions: string[];
  evidence_count: number;
}

export interface PaperComparisonMatrix {
  request_id: string;
  total_papers: number;
  columns: string[];
  rows: PaperComparisonRow[];
}

export interface SynthesisOverviewStats {
  request_id: string;
  total_eligible_papers: number;
  latest_run_id?: string;
  latest_run_status?: string;
  total_themes: number;
  total_patterns: number;
  total_candidate_gaps: number;
  gaps_by_category: Record<string, number>;
  gaps_by_review_status: Record<string, number>;
  evidence_grounding_rate: number;
}
