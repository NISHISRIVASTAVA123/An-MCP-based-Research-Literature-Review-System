# Literature Synthesis Architecture (Phase 4)

## 1. Architectural Mission

The Literature Synthesis Engine integrates structured representations from Phase 1 (bibliographic metadata), Phase 2 (structured extraction records), and Phase 3 (knowledge graph entities and typed edges) into an academically coherent, multi-perspective literature review.

The primary objective is to move beyond superficial paper summaries and provide **cross-cutting comparative synthesis**:
1. Mapping the methodological landscape across retrieved studies.
2. Characterizing empirical benchmarks, datasets, and performance indicators.
3. Contrasting reported findings, noting consensus and contextual divergence.
4. Synthesizing author-reported limitations and future research agendas.
5. Identifying underexplored intersections in the retrieved literature.
6. Formulating evidence-grounded candidate research gaps.

---

## 2. Component Pipeline

The literature synthesis pipeline operates through a staged, coordinated sequence orchestrated by `SynthesisOrchestrator`:

```mermaid
sequenceDiagram
    participant Client as User / Autonomous Agent
    participant Orch as SynthesisOrchestrator
    participant Gate as EvidenceRetrievalService
    participant Mat as ComparisonMatrixService
    participant Thm as ResearchThemeService
    participant Pat as PatternAnalysisService
    participant Eng as LiteratureSynthesisEngine
    participant Gap as CandidateResearchGapGenerator
    participant Repo as SynthesisRepository

    Client->>Orch: execute_synthesis_run(request_id, config)
    Orch->>Gate: get_eligible_papers_for_request(request_id)
    Note over Gate: Strictly excludes Phase 2 rejected papers
    Gate-->>Orch: eligible_papers
    Orch->>Repo: create_synthesis_run(status="in_progress")
    
    Orch->>Thm: identify_themes(request_id, selected_paper_ids)
    Thm-->>Orch: themes_data
    Orch->>Repo: create_literature_themes(run.id, themes_data)
    
    Orch->>Pat: analyze_patterns(request_id, selected_paper_ids)
    Pat-->>Orch: patterns_data
    Orch->>Repo: create_literature_patterns(run.id, patterns_data)
    
    Orch->>Eng: generate_synthesis(request_id, selected_paper_ids)
    Eng-->>Orch: summary_narrative (9 academic sections)
    
    Orch->>Gap: generate_candidate_gaps(request_id, run.id, selected_paper_ids)
    Note over Gap: Validates paper & passage IDs against SQLite
    Gap-->>Orch: candidate_gaps
    
    Orch->>Repo: update_synthesis_run_status(run.id, "completed")
    Orch-->>Client: SynthesisRunResponse
```

---

## 3. Narrative Synthesis Structure

The engine generates both structured JSON data and a publication-ready narrative structured into 9 academic sections:

1. **Executive Summary**: Overview of literature collection, time window, and primary paradigms.
2. **Methodological Landscape**: Comparative analysis of algorithmic approaches, model families, and architectures.
3. **Empirical Benchmarks & Datasets**: Benchmark dataset frequencies, domain distributions, and data modality trends.
4. **Evaluation Metrics & Protocols**: Distribution of performance metrics and evaluation rigor across papers.
5. **Reported Findings & Convergent Evidence**: Primary empirical discoveries, consistent outcomes, and areas of high confidence.
6. **Contradictions, Variations & Contextual Divergence**: Divergent findings explained through differing datasets, hyperparameters, or evaluation scopes.
7. **Author-Reported Limitations**: Synthesis of explicit limitations reported by authors (scalability, compute latency, distribution shift).
8. **Future Research Directions**: Author-proposed future work directions mapped across studies.
9. **Synthesis Discussion & Scope Boundaries**: Critical analysis of underexplored areas strictly qualified by retrieved collection coverage.
