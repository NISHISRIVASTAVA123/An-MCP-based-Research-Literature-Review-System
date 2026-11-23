import React, { useState } from 'react';
import { ResearchRequestCreate } from '../types';
import {
  Plus, Trash2, Search, Layers, Calendar, Database, Settings2,
  ChevronDown, ChevronUp, Sparkles, BookOpen,
} from 'lucide-react';

interface ResearchFormProps {
  onSubmit: (data: ResearchRequestCreate) => void;
  isLoading: boolean;
}

const DOMAINS = [
  'Artificial Intelligence',
  'Natural Language Processing (NLP)',
  'Machine Learning & Deep Learning',
  'Computer Vision',
  'Cybersecurity & Privacy',
  'Healthcare & Biomedical Informatics',
  'Data Science & Analytics',
  'Software Engineering',
  'Robotics & Autonomous Systems',
  'Human-Computer Interaction',
];

const DB_OPTIONS = [
  { id: 'openalex',         label: 'OpenAlex',         desc: '240M+ works, open access', color: '#0369a1', bg: '#e0f2fe' },
  { id: 'semantic_scholar', label: 'Semantic Scholar',  desc: '220M papers with AI features', color: '#6d28d9', bg: '#f3e8ff' },
  { id: 'crossref',         label: 'Crossref',          desc: '150M+ DOI-registered works', color: '#92400e', bg: '#fef3c7' },
  { id: 'arxiv',            label: 'arXiv Preprints',   desc: '2.3M+ STEM preprints', color: '#991b1b', bg: '#fee2e2' },
];

export const ResearchForm: React.FC<ResearchFormProps> = ({ onSubmit, isLoading }) => {
  const [topic, setTopic] = useState('Explainable AI for Fake News Detection');
  const [objective, setObjective] = useState(
    'Identify limitations and verification gaps in existing explainable fake news and misinformation detection approaches.'
  );
  const [domain, setDomain] = useState('Artificial Intelligence');
  const [customDomain, setCustomDomain] = useState('');
  const [startYear, setStartYear] = useState(2018);
  const [endYear, setEndYear] = useState(2026);
  const [maxPapers, setMaxPapers] = useState(25);
  const [citationStyle, setCitationStyle] = useState('IEEE');
  const [questions, setQuestions] = useState<string[]>([
    'What explanation mechanisms (e.g. SHAP, LIME, attention maps) are prevalent in fake news models?',
    'Are existing explanation methods robust against adversarial misinformation perturbations?',
  ]);
  const [preferredDbs, setPreferredDbs] = useState<string[]>(['openalex', 'semantic_scholar', 'crossref', 'arxiv']);
  const [inclusionCriteria, setInclusionCriteria] = useState('Peer-reviewed or archived scientific works; Focus on text or multimodal fake news');
  const [exclusionCriteria, setExclusionCriteria] = useState('Non-English publications; Purely non-technical opinion pieces');
  const [specificDois, setSpecificDois] = useState('');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const addQuestion = () => setQuestions([...questions, '']);
  const updateQuestion = (i: number, v: string) => { const q = [...questions]; q[i] = v; setQuestions(q); };
  const removeQuestion = (i: number) => setQuestions(questions.filter((_, idx) => idx !== i));
  const toggleDb = (db: string) => {
    if (preferredDbs.includes(db)) {
      if (preferredDbs.length > 1) setPreferredDbs(preferredDbs.filter((d) => d !== db));
    } else {
      setPreferredDbs([...preferredDbs, db]);
    }
  };

  const validate = (): boolean => {
    const errs: Record<string, string> = {};
    if (!topic.trim()) errs.topic = 'Research topic is required.';
    if (!objective.trim() || objective.trim().length < 10) errs.objective = 'Objective must be at least 10 characters.';
    if (startYear > endYear) errs.years = `Start year (${startYear}) cannot be later than end year (${endYear}).`;
    if (maxPapers < 5 || maxPapers > 100) errs.maxPapers = 'Max papers must be between 5 and 100.';
    if (preferredDbs.length === 0) errs.databases = 'Select at least one database.';
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    const finalDomain = domain === 'Other' && customDomain.trim() ? customDomain.trim() : domain;
    onSubmit({
      topic: topic.trim(),
      objective: objective.trim(),
      domain: finalDomain,
      start_year: Number(startYear),
      end_year: Number(endYear),
      max_papers: Number(maxPapers),
      citation_style: citationStyle,
      research_questions: questions.map((q) => q.trim()).filter(Boolean),
      inclusion_criteria: inclusionCriteria.split(';').map((s) => s.trim()).filter(Boolean),
      exclusion_criteria: exclusionCriteria.split(';').map((s) => s.trim()).filter(Boolean),
      preferred_databases: preferredDbs,
      publication_types: ['journal', 'conference', 'review', 'preprint'],
      specific_dois: specificDois.split('\n').map((s) => s.trim()).filter(Boolean),
    });
  };

  /* ---- Helper renderers ---- */
  const FieldLabel = ({ children, required }: { children: React.ReactNode; required?: boolean }) => (
    <label style={{
      display: 'block', fontSize: '0.72rem', fontWeight: 700,
      letterSpacing: '0.07em', textTransform: 'uppercase', color: '#475569', marginBottom: '0.5rem',
    }}>
      {children} {required && <span style={{ color: '#f43f5e' }}>*</span>}
    </label>
  );

  const ErrorMsg = ({ msg }: { msg?: string }) =>
    msg ? <p style={{ fontSize: '0.76rem', color: '#f43f5e', marginTop: '0.3rem', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>⚠ {msg}</p> : null;

  return (
    <form onSubmit={handleSubmit} style={{ maxWidth: 800, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>

      {/* Hero section */}
      <div className="card-dark" style={{ padding: '1.75rem 2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.6rem' }}>
          <div style={{
            padding: '0.4rem', borderRadius: '0.5rem',
            background: 'rgba(129,140,248,.2)', display: 'inline-flex',
          }}>
            <Layers size={18} color="#a5b4fc" />
          </div>
          <span style={{ fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase', color: '#a5b4fc' }}>
            Step 1 · Define Research Request
          </span>
        </div>
        <h2 style={{ fontFamily: 'Sora, Inter, sans-serif', fontWeight: 800, fontSize: '1.45rem', color: '#fff', marginBottom: '0.4rem' }}>
          What do you want to research?
        </h2>
        <p style={{ fontSize: '0.85rem', color: 'rgba(255,255,255,0.55)', maxWidth: 540 }}>
          Define your research topic and objectives. The system will generate a tailored search strategy and retrieve papers from multiple academic databases.
        </p>
      </div>

      {/* Core fields */}
      <div className="card" style={{ padding: '1.75rem 2rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', paddingBottom: '1rem', borderBottom: '1px solid #f1f5f9' }}>
          <BookOpen size={16} color="#6366f1" />
          <span style={{ fontWeight: 700, fontSize: '0.9rem', color: '#1e293b' }}>Core Research Details</span>
        </div>

        {/* Topic */}
        <div>
          <FieldLabel required>Research Topic</FieldLabel>
          <input
            type="text"
            className="input"
            style={{ fontSize: '1rem', fontWeight: 600 }}
            placeholder="e.g. Explainable AI for Fake News Detection"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
          />
          <ErrorMsg msg={errors.topic} />
        </div>

        {/* Objective */}
        <div>
          <FieldLabel required>Research Objective & Scope</FieldLabel>
          <textarea
            rows={3}
            className="input"
            placeholder="State the primary goal of your literature review..."
            value={objective}
            onChange={(e) => setObjective(e.target.value)}
          />
          <ErrorMsg msg={errors.objective} />
        </div>

        {/* Research Questions */}
        <div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
            <FieldLabel>Research Questions</FieldLabel>
            <button type="button" onClick={addQuestion} style={{
              display: 'flex', alignItems: 'center', gap: '0.3rem',
              fontSize: '0.78rem', fontWeight: 600, color: '#6366f1',
              background: '#eef2ff', border: '1px solid #c7d2fe',
              borderRadius: '0.4rem', padding: '0.3rem 0.7rem', cursor: 'pointer',
            }}>
              <Plus size={13} /> Add Question
            </button>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {questions.map((q, idx) => (
              <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span style={{
                  minWidth: 36, height: 28, borderRadius: '0.4rem',
                  background: '#eef2ff', color: '#6366f1',
                  fontSize: '0.7rem', fontWeight: 800,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontFamily: 'JetBrains Mono, monospace',
                }}>RQ{idx + 1}</span>
                <input
                  type="text"
                  className="input"
                  style={{ fontSize: '0.84rem' }}
                  placeholder="e.g. What datasets are standardly evaluated?"
                  value={q}
                  onChange={(e) => updateQuestion(idx, e.target.value)}
                />
                {questions.length > 1 && (
                  <button type="button" onClick={() => removeQuestion(idx)} style={{
                    padding: '0.4rem', background: 'none', border: 'none',
                    cursor: 'pointer', color: '#94a3b8', borderRadius: '0.4rem',
                    transition: 'color 0.15s',
                  }}
                    onMouseEnter={(e) => e.currentTarget.style.color = '#f43f5e'}
                    onMouseLeave={(e) => e.currentTarget.style.color = '#94a3b8'}
                  >
                    <Trash2 size={15} />
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Scope Configuration */}
      <div className="card" style={{ padding: '1.75rem 2rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', paddingBottom: '1rem', borderBottom: '1px solid #f1f5f9' }}>
          <Settings2 size={16} color="#6366f1" />
          <span style={{ fontWeight: 700, fontSize: '0.9rem', color: '#1e293b' }}>Search Configuration</span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem' }}>
          {/* Domain */}
          <div>
            <FieldLabel>Scientific Domain</FieldLabel>
            <select className="input" value={domain} onChange={(e) => setDomain(e.target.value)}>
              {DOMAINS.map((d) => <option key={d}>{d}</option>)}
              <option value="Other">Other (Custom)...</option>
            </select>
            {domain === 'Other' && (
              <input type="text" className="input" style={{ marginTop: '0.5rem', fontSize: '0.84rem' }}
                placeholder="Enter domain name..." value={customDomain} onChange={(e) => setCustomDomain(e.target.value)} />
            )}
          </div>

          {/* Year range */}
          <div>
            <FieldLabel>Publication Timeframe</FieldLabel>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <input type="number" className="input" style={{ textAlign: 'center' }}
                value={startYear} min={1990} max={2030}
                onChange={(e) => setStartYear(Number(e.target.value))} />
              <span style={{ color: '#94a3b8', fontWeight: 700, fontSize: '0.8rem', flexShrink: 0 }}>to</span>
              <input type="number" className="input" style={{ textAlign: 'center' }}
                value={endYear} min={1990} max={2030}
                onChange={(e) => setEndYear(Number(e.target.value))} />
            </div>
            <ErrorMsg msg={errors.years} />
          </div>
        </div>

        {/* Databases */}
        <div>
          <FieldLabel>Target Academic Databases</FieldLabel>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.65rem' }}>
            {DB_OPTIONS.map((db) => {
              const isSelected = preferredDbs.includes(db.id);
              return (
                <label key={db.id} style={{
                  display: 'flex', alignItems: 'center', gap: '0.65rem',
                  padding: '0.75rem 1rem', borderRadius: '0.65rem', cursor: 'pointer',
                  border: `1.5px solid ${isSelected ? db.color + '55' : '#e2e8f0'}`,
                  background: isSelected ? db.bg + 'aa' : '#fff',
                  transition: 'all 0.15s', userSelect: 'none',
                }}>
                  <input type="checkbox" checked={isSelected} onChange={() => toggleDb(db.id)}
                    style={{ accentColor: db.color, width: 15, height: 15, flexShrink: 0 }} />
                  <div>
                    <div style={{ fontSize: '0.82rem', fontWeight: 600, color: '#1e293b' }}>{db.label}</div>
                    <div style={{ fontSize: '0.68rem', color: '#64748b' }}>{db.desc}</div>
                  </div>
                </label>
              );
            })}
          </div>
          <ErrorMsg msg={errors.databases} />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem' }}>
          {/* Max papers */}
          <div>
            <FieldLabel>Max Papers per Search</FieldLabel>
            <input type="number" className="input" value={maxPapers}
              min={5} max={100} onChange={(e) => setMaxPapers(Number(e.target.value))} />
            <ErrorMsg msg={errors.maxPapers} />
          </div>
          {/* Citation style */}
          <div>
            <FieldLabel>Citation Format</FieldLabel>
            <select className="input" value={citationStyle} onChange={(e) => setCitationStyle(e.target.value)}>
              <option>IEEE</option>
              <option>APA</option>
              <option>Harvard</option>
              <option>ACM</option>
            </select>
          </div>
        </div>
      </div>

      {/* Advanced / Optional */}
      <div className="card" style={{ overflow: 'hidden' }}>
        <button type="button" onClick={() => setShowAdvanced(!showAdvanced)}
          style={{
            width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            padding: '1rem 1.75rem', background: 'none', border: 'none', cursor: 'pointer',
            fontWeight: 600, fontSize: '0.85rem', color: '#475569',
          }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Settings2 size={15} />
            Advanced Options (Inclusion/Exclusion Criteria, Specific DOIs)
          </span>
          {showAdvanced ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </button>

        {showAdvanced && (
          <div style={{ padding: '0 1.75rem 1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem', borderTop: '1px solid #f1f5f9' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', paddingTop: '1rem' }}>
              <div>
                <FieldLabel>Inclusion Criteria</FieldLabel>
                <input type="text" className="input" style={{ fontSize: '0.82rem' }}
                  placeholder="e.g. Peer-reviewed; Empirical studies; 2018+" value={inclusionCriteria}
                  onChange={(e) => setInclusionCriteria(e.target.value)} />
                <p style={{ fontSize: '0.68rem', color: '#94a3b8', marginTop: '0.3rem' }}>Semicolon-separated</p>
              </div>
              <div>
                <FieldLabel>Exclusion Criteria</FieldLabel>
                <input type="text" className="input" style={{ fontSize: '0.82rem' }}
                  placeholder="e.g. Keynotes; Non-English; Extended abstracts" value={exclusionCriteria}
                  onChange={(e) => setExclusionCriteria(e.target.value)} />
                <p style={{ fontSize: '0.68rem', color: '#94a3b8', marginTop: '0.3rem' }}>Semicolon-separated</p>
              </div>
            </div>
            <div>
              <FieldLabel>Specific DOIs to Include</FieldLabel>
              <textarea rows={2} className="input" style={{ fontSize: '0.82rem', fontFamily: 'JetBrains Mono, monospace' }}
                placeholder="10.1234/example&#10;10.5678/another" value={specificDois}
                onChange={(e) => setSpecificDois(e.target.value)} />
              <p style={{ fontSize: '0.68rem', color: '#94a3b8', marginTop: '0.3rem' }}>One DOI per line</p>
            </div>
          </div>
        )}
      </div>

      {/* Submit */}
      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', paddingBottom: '2rem' }}>
        {questions.filter(Boolean).length === 0 && (
          <div className="info-banner" style={{ flex: 1, fontSize: '0.78rem' }}>
            💡 No research questions added — the system will infer from topic and objective.
          </div>
        )}
        <button type="submit" disabled={isLoading} className="btn btn-primary btn-lg" style={{ minWidth: 220 }}>
          {isLoading ? (
            <>
              <div className="spinner" style={{ width: 18, height: 18, borderWidth: 2 }} />
              <span>Generating Strategy...</span>
            </>
          ) : (
            <>
              <Sparkles size={18} />
              <span>Generate Search Strategy</span>
            </>
          )}
        </button>
      </div>
    </form>
  );
};
