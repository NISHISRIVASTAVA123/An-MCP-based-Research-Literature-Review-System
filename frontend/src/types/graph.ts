export interface GraphNode {
  id: string;
  request_id: string;
  node_type: string;
  label: string;
  normalized_label: string;
  entity_key: string;
  source_paper_id?: string;
  evidence_passage_id?: string;
  properties: Record<string, any>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface GraphEdge {
  id: string;
  request_id: string;
  source_node_id: string;
  target_node_id: string;
  relationship_type: string;
  edge_key: string;
  source_paper_id?: string;
  evidence_passage_id?: string;
  properties: Record<string, any>;
  created_at: string;
}

export interface GraphStatistics {
  request_id: string;
  total_nodes: number;
  total_edges: number;
  nodes_by_type: Record<string, number>;
  relationships_by_type: Record<string, number>;
  papers_count: number;
  claims_count: number;
  findings_count: number;
  evidence_passages_count: number;
  methods_count: number;
  datasets_count: number;
  limitations_count: number;
  claims_with_evidence_percentage: number;
}

export interface EvidenceGraphData {
  request_id: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
  statistics: GraphStatistics;
}

export interface GraphBuildRun {
  id: string;
  request_id: string;
  run_number: number;
  trigger_type: string;
  status: string;
  total_nodes: number;
  total_edges: number;
  nodes_added: number;
  nodes_updated: number;
  edges_added: number;
  papers_processed: number;
  execution_time_seconds: number;
  summary: Record<string, any>;
  error_details?: string;
  created_at: string;
}

export interface GraphValidationRecord {
  id: string;
  request_id: string;
  build_run_id?: string;
  integrity_status: string;
  total_nodes: number;
  total_relationships: number;
  nodes_by_type: Record<string, number>;
  relationships_by_type: Record<string, number>;
  claims_with_evidence: number;
  claims_without_evidence: number;
  findings_with_passages: number;
  orphan_nodes_count: number;
  unresolved_entities_count: number;
  abstract_only_count: number;
  full_text_count: number;
  validation_details: Record<string, any>;
  created_at: string;
}

export interface ProvenanceChain {
  claim_id: string;
  claim_text: string;
  claim_type: string;
  verification_status: string;
  has_evidence_passage: boolean;
  evidence_passage_id?: string;
  exact_passage?: string;
  page_number?: number;
  section_heading?: string;
  paper_id: string;
  paper_title: string;
  paper_doi?: string;
  publication_year?: number;
  source_scope: string;
  document_id?: string;
  extraction_run_id?: string;
  extractor_backend?: string;
  research_request_id: string;
  is_provenance_complete: boolean;
  audit_notes?: string;
}
