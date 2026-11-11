import React, { useState } from 'react';
import { ResearchRequestCreate } from '../types';
import { Plus, Trash2, Search, HelpCircle, Layers, Calendar, CheckSquare } from 'lucide-react';

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

  const [preferredDbs, setPreferredDbs] = useState<string[]>([
    'openalex',
    'semantic_scholar',
    'crossref',
    'arxiv',
  ]);

  const [inclusionCriteria, setInclusionCriteria] = useState('Peer-reviewed or archived scientific works; Focus on text or multimodal fake news');
  const [exclusionCriteria, setExclusionCriteria] = useState('Non-English publications; Purely non-technical opinion pieces');
  const [specificDois, setSpecificDois] = useState('');

  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleAddQuestion = () => {
    setQuestions([...questions, '']);
  };

  const handleUpdateQuestion = (index: number, val: string) => {
    const updated = [...questions];
    updated[index] = val;
    setQuestions(updated);
  };

  const handleRemoveQuestion = (index: number) => {
    setQuestions(questions.filter((_, i) => i !== index));
  };

  const toggleDb = (db: string) => {
    if (preferredDbs.includes(db)) {
      if (preferredDbs.length > 1) {
        setPreferredDbs(preferredDbs.filter((d) => d !== db));
      }
    } else {
      setPreferredDbs([...preferredDbs, db]);
    }
  };

  const validate = (): boolean => {
    const errs: Record<string, string> = {};
    if (!topic.trim()) errs.topic = 'Research topic is required.';
    if (!objective.trim() || objective.trim().length < 10) {
      errs.objective = 'Research objective must be at least 10 characters.';
    }
    if (startYear > endYear) {
      errs.years = `Start year (${startYear}) cannot be later than end year (${endYear}).`;
    }
    if (maxPapers < 5 || maxPapers > 100) {
      errs.maxPapers = 'Max papers should be between 5 and 100.';
    }
    if (preferredDbs.length === 0) {
      errs.databases = 'Select at least one academic database.';
    }
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    const finalDomain = domain === 'Other' && customDomain.trim() ? customDomain.trim() : domain;

    const payload: ResearchRequestCreate = {
      topic: topic.trim(),
      objective: objective.trim(),
      domain: finalDomain,
      start_year: Number(startYear),
      end_year: Number(endYear),
      max_papers: Number(maxPapers),
      citation_style: citationStyle,
      research_questions: questions.map((q) => q.trim()).filter(Boolean),
      inclusion_criteria: inclusionCriteria
        .split(';')
        .map((s) => s.trim())
        .filter(Boolean),
      exclusion_criteria: exclusionCriteria
        .split(';')
        .map((s) => s.trim())
        .filter(Boolean),
      preferred_databases: preferredDbs,
      publication_types: ['journal', 'conference', 'review', 'preprint'],
      specific_dois: specificDois
        .split('\n')
        .map((s) => s.trim())
        .filter(Boolean),
    };

    onSubmit(payload);
  };

  return (
    <form onSubmit={handleSubmit} className="academic-card p-6 sm:p-8 max-w-4xl mx-auto space-y-8">
      <div>
        <div className="flex items-center gap-2 mb-1">
          <Layers className="h-5 w-5 text-indigo-600" />
          <h2 className="text-xl font-bold font-serif text-slate-900">Define Research Review Request</h2>
        </div>
        <p className="text-xs text-slate-500">
          Enter your research topic, define the review objective, and configure the academic scope for autonomous retrieval.
        </p>
      </div>

      {/* Core Fields */}
      <div className="space-y-5">
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1.5">
            Research Topic <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            className="input-base text-base font-medium"
            placeholder="e.g. Explainable AI for Fake News Detection"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
          />
          {errors.topic && <p className="text-xs text-red-600 mt-1">{errors.topic}</p>}
        </div>

        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1.5">
            Research Objective & Scope <span className="text-red-500">*</span>
          </label>
          <textarea
            rows={3}
            className="input-base"
            placeholder="State the primary goal of your literature review..."
            value={objective}
            onChange={(e) => setObjective(e.target.value)}
          />
          {errors.objective && <p className="text-xs text-red-600 mt-1">{errors.objective}</p>}
        </div>

        {/* Dynamic Research Questions */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-700">
              Research Questions
            </label>
            <button
              type="button"
              onClick={handleAddQuestion}
              className="text-xs font-medium text-indigo-600 hover:text-indigo-800 flex items-center gap-1"
            >
              <Plus className="h-3.5 w-3.5" />
              <span>Add Research Question</span>
            </button>
          </div>

          <div className="space-y-2.5">
            {questions.map((q, idx) => (
              <div key={idx} className="flex items-center gap-2">
                <span className="text-xs font-mono text-slate-400 w-6">RQ{idx + 1}</span>
                <input
                  type="text"
                  className="input-base text-xs"
                  placeholder="e.g. What datasets are standardly evaluated?"
                  value={q}
                  onChange={(e) => handleUpdateQuestion(idx, e.target.value)}
                />
                {questions.length > 1 && (
                  <button
                    type="button"
                    onClick={() => handleRemoveQuestion(idx)}
                    className="p-2 text-slate-400 hover:text-red-600 transition-colors"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      <hr className="border-slate-200" />

      {/* Scope Configuration */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1.5">
            Scientific Domain
          </label>
          <select
            className="input-base text-sm"
            value={domain}
            onChange={(e) => setDomain(e.target.value)}
          >
            {DOMAINS.map((d) => (
              <option key={d} value={d}>{d}</option>
            ))}
            <option value="Other">Other (Custom Domain)...</option>
          </select>
          {domain === 'Other' && (
            <input
              type="text"
              className="input-base text-xs mt-2"
              placeholder="Enter domain name..."
              value={customDomain}
              onChange={(e) => setCustomDomain(e.target.value)}
            />
          )}
        </div>

        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1.5">
            <Calendar className="h-3.5 w-3.5 inline mr-1 text-slate-500" />
            Publication Timeframe
          </label>
          <div className="flex items-center gap-2">
            <input
              type="number"
              className="input-base text-center"
              value={startYear}
              onChange={(e) => setStartYear(Number(e.target.value))}
              min={1990}
              max={2030}
            />
            <span className="text-slate-400 text-xs font-semibold">to</span>
            <input
              type="number"
              className="input-base text-center"
              value={endYear}
              onChange={(e) => setEndYear(Number(e.target.value))}
              min={1990}
              max={2030}
            />
          </div>
          {errors.years && <p className="text-xs text-red-600 mt-1">{errors.years}</p>}
        </div>

        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1.5">
            Target Academic Databases
          </label>
          <div className="grid grid-cols-2 gap-2 text-xs">
            {[
              { id: 'openalex', label: 'OpenAlex', color: 'badge-openalex' },
              { id: 'semantic_scholar', label: 'Semantic Scholar', color: 'badge-semantic_scholar' },
              { id: 'crossref', label: 'Crossref', color: 'badge-crossref' },
              { id: 'arxiv', label: 'arXiv Preprints', color: 'badge-arxiv' },
            ].map((db) => (
              <label
                key={db.id}
                className={`flex items-center gap-2 p-2 rounded-md border cursor-pointer select-none transition-colors ${
                  preferredDbs.includes(db.id)
                    ? 'border-indigo-300 bg-indigo-50/50 text-indigo-950 font-medium'
                    : 'border-slate-200 hover:bg-slate-50 text-slate-600'
                }`}
              >
                <input
                  type="checkbox"
                  checked={preferredDbs.includes(db.id)}
                  onChange={() => toggleDb(db.id)}
                  className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 h-3.5 w-3.5"
                />
                <span>{db.label}</span>
              </label>
            ))}
          </div>
          {errors.databases && <p className="text-xs text-red-600 mt-1">{errors.databases}</p>}
        </div>

        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1.5">
            Retrieval Parameters
          </label>
          <div className="flex items-center gap-3">
            <div className="flex-1">
              <span className="text-[11px] text-slate-500 block mb-1">Max Papers / Search:</span>
              <input
                type="number"
                className="input-base"
                value={maxPapers}
                onChange={(e) => setMaxPapers(Number(e.target.value))}
                min={5}
                max={100}
              />
            </div>
            <div className="flex-1">
              <span className="text-[11px] text-slate-500 block mb-1">Citation Format:</span>
              <select
                className="input-base"
                value={citationStyle}
                onChange={(e) => setCitationStyle(e.target.value)}
              >
                <option value="IEEE">IEEE</option>
                <option value="APA">APA 7th</option>
                <option value="Harvard">Harvard</option>
                <option value="ACM">ACM</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Optional Criteria */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
        <div>
          <label className="block text-[11px] font-semibold uppercase tracking-wider text-slate-500 mb-1">
            Inclusion Criteria (Semicolon-separated)
          </label>
          <input
            type="text"
            className="input-base text-xs"
            value={inclusionCriteria}
            onChange={(e) => setInclusionCriteria(e.target.value)}
            placeholder="e.g. Peer-reviewed; Empirical studies; 2018+"
          />
        </div>
        <div>
          <label className="block text-[11px] font-semibold uppercase tracking-wider text-slate-500 mb-1">
            Exclusion Criteria (Semicolon-separated)
          </label>
          <input
            type="text"
            className="input-base text-xs"
            value={exclusionCriteria}
            onChange={(e) => setExclusionCriteria(e.target.value)}
            placeholder="e.g. Keynotes; Non-English; Extended abstracts"
          />
        </div>
      </div>

      {/* Submit Action */}
      <div className="pt-4 flex items-center justify-end gap-3 border-t border-slate-200">
        <button
          type="submit"
          disabled={isLoading}
          className="btn-primary text-sm py-2.5 px-6 shadow-sm"
        >
          {isLoading ? (
            <span>Generating Search Strategy...</span>
          ) : (
            <>
              <Search className="h-4 w-4" />
              <span>Generate Search Strategy</span>
            </>
          )}
        </button>
      </div>
    </form>
  );
};

