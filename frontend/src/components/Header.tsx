import React from 'react';
import { BookOpen, History, Cpu, Sparkles, FlaskConical } from 'lucide-react';

interface HeaderProps {
  onNewReview: () => void;
  onOpenHistory: () => void;
  onOpenMcp: () => void;
  activeStep: 'form' | 'strategy' | 'dashboard' | 'screening' | 'graph' | 'synthesis' | 'counterevidence';
  onSelectStep?: (step: 'form' | 'strategy' | 'dashboard' | 'screening' | 'graph' | 'synthesis' | 'counterevidence') => void;
}

const STEPS = [
  { id: 'form',            label: 'Research Input',       num: 1 },
  { id: 'strategy',        label: 'Search Strategy',      num: 2 },
  { id: 'dashboard',       label: 'Corpus Results',       num: 3 },
  { id: 'screening',       label: 'Screening & Evidence', num: 4 },
  { id: 'graph',           label: 'Evidence Graph',       num: 5 },
  { id: 'synthesis',       label: 'Literature Synthesis', num: 6 },
  { id: 'counterevidence', label: 'Counterevidence',      num: 7 },
] as const;

export const Header: React.FC<HeaderProps> = ({
  onNewReview,
  onOpenHistory,
  onOpenMcp,
  activeStep,
  onSelectStep,
}) => {
  const activeIdx = STEPS.findIndex((s) => s.id === activeStep);

  return (
    <header
      style={{
        background: 'linear-gradient(135deg, #1e1b4b 0%, #312e81 60%, #1e3a5f 100%)',
        borderBottom: '1px solid rgba(255,255,255,0.08)',
        position: 'sticky',
        top: 0,
        zIndex: 40,
        boxShadow: '0 4px 24px rgba(0,0,0,0.25)',
      }}
    >
      <div className="app-container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '1rem', padding: '0 1.5rem', height: 64 }}>
        {/* Brand */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexShrink: 0 }}>
          <div style={{
            width: 40, height: 40, borderRadius: '0.6rem',
            background: 'linear-gradient(135deg, #6366f1, #818cf8)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 0 0 2px rgba(129,140,248,.35)',
          }}>
            <FlaskConical size={20} color="#fff" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ fontFamily: 'Sora, Inter, sans-serif', fontWeight: 800, fontSize: '1.05rem', color: '#fff', letterSpacing: '-0.01em' }}>
                ResearchMind
              </span>
              <span style={{
                fontSize: '0.65rem', fontWeight: 700, letterSpacing: '0.08em',
                background: 'rgba(244,63,94,.2)', color: '#fb7185',
                borderRadius: '100px', padding: '0.15rem 0.55rem',
                border: '1px solid rgba(244,63,94,.35)',
              }}>
                PHASE 5 ACTIVE
              </span>
            </div>
            <div style={{ fontSize: '0.68rem', color: 'rgba(255,255,255,0.45)', marginTop: 1 }}>
              MCP Multi-Agent Research Gap Assessment · B.Tech Capstone
            </div>
          </div>
        </div>

        {/* Step Indicator — center */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 0 }}>
          {STEPS.map((step, i) => {
            const isDone   = i < activeIdx;
            const isActive = i === activeIdx;
            return (
              <React.Fragment key={step.id}>
                <div
                  onClick={() => onSelectStep && onSelectStep(step.id as any)}
                  style={{
                    display: 'flex', alignItems: 'center', gap: '0.4rem',
                    padding: '0.4rem 0.8rem', borderRadius: '0.5rem',
                    fontSize: '0.78rem', fontWeight: 600,
                    color: isActive ? '#fff' : isDone ? '#34d399' : 'rgba(255,255,255,0.35)',
                    background: isActive ? 'rgba(99,102,241,0.3)' : 'transparent',
                    cursor: onSelectStep ? 'pointer' : 'default',
                    transition: 'all 0.2s',
                  }}
                >
                  <div style={{
                    width: 22, height: 22, borderRadius: '50%',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: '0.68rem', fontWeight: 700, flexShrink: 0,
                    background: isActive ? '#6366f1' : isDone ? '#10b981' : 'rgba(255,255,255,0.1)',
                    color: isActive || isDone ? '#fff' : 'rgba(255,255,255,0.4)',
                  }}>
                    {isDone ? '✓' : step.num}
                  </div>
                  <span style={{ display: 'block' }}>{step.label}</span>
                </div>
                {i < STEPS.length - 1 && (
                  <div style={{
                    width: 32, height: 2,
                    background: isDone ? '#10b981' : 'rgba(255,255,255,0.12)',
                    borderRadius: 2, flexShrink: 0,
                    transition: 'background 0.3s',
                  }} />
                )}
              </React.Fragment>
            );
          })}
        </div>

        {/* Actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexShrink: 0 }}>
          <button onClick={onOpenMcp} className="btn btn-sm" style={{
            background: 'rgba(255,255,255,0.08)', color: 'rgba(255,255,255,0.75)',
            border: '1px solid rgba(255,255,255,0.12)',
          }} title="Inspect MCP Agent Tools">
            <Cpu size={14} />
            <span>MCP Tools</span>
          </button>

          <button onClick={onOpenHistory} className="btn btn-sm" style={{
            background: 'rgba(255,255,255,0.08)', color: 'rgba(255,255,255,0.75)',
            border: '1px solid rgba(255,255,255,0.12)',
          }}>
            <History size={14} />
            <span>History</span>
          </button>

          <button onClick={onNewReview} className="btn btn-sm btn-primary" style={{ padding: '0.45rem 1rem' }}>
            <Sparkles size={14} />
            <span>New Review</span>
          </button>
        </div>
      </div>
    </header>
  );
};
