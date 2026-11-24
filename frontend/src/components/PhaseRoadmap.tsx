import React from 'react';
import {
  Search, ScanSearch, FileSearch, Microscope, GitBranch,
  ShieldCheck, BarChart3, FileText, FlaskConical, Lock, CheckCircle2,
} from 'lucide-react';

const PHASES = [
  {
    num: 1, label: 'Literature Retrieval',
    sub: 'Search strategy & paper retrieval',
    icon: CheckCircle2, color: '#10b981', active: false, done: true,
  },
  {
    num: 2, label: 'Screening & Evidence',
    sub: 'Paper screening & structured extraction',
    icon: CheckCircle2, color: '#10b981', active: false, done: true,
  },
  {
    num: 3, label: 'Evidence Database & Graph',
    sub: 'Graph construction & provenance',
    icon: GitBranch, color: '#8b5cf6', active: true, done: false,
  },
  {
    num: 4, label: 'Literature Synthesis',
    sub: 'Gap identification baseline',
    icon: Microscope, color: '#f59e0b', active: false, done: false,
  },
  {
    num: 5, label: 'Counterevidence Search',
    sub: 'Gap-specific counter-retrieval',
    icon: ShieldCheck, color: '#f43f5e', active: false, done: false,
  },
  {
    num: 6, label: 'Claim Verification',
    sub: 'Graph-based claim verification',
    icon: CheckCircle2, color: '#06b6d4', active: false, done: false,
  },
  {
    num: 7, label: 'Coverage Assessment',
    sub: 'Coverage-aware gap classification',
    icon: BarChart3, color: '#a855f7', active: false, done: false,
  },
  {
    num: 8, label: 'Report Generation',
    sub: 'Full review & gap report export',
    icon: FileText, color: '#10b981', active: false, done: false,
  },
  {
    num: 9, label: 'Benchmark Evaluation',
    sub: 'Ablations & human validation',
    icon: FlaskConical, color: '#38bdf8', active: false, done: false,
  },
];

interface PhaseRoadmapProps {
  currentActiveStep?: 'form' | 'strategy' | 'dashboard' | 'screening' | 'graph';
  onSelectStep?: (step: 'form' | 'strategy' | 'dashboard' | 'screening' | 'graph') => void;
}


export const PhaseRoadmap: React.FC<PhaseRoadmapProps> = ({ currentActiveStep }) => {
  return (
    <aside className="sidebar-col" style={{
      background: 'linear-gradient(180deg, #1e1b4b 0%, #252060 55%, #1a2744 100%)',
      minHeight: '100%',
      padding: '1.5rem 1rem',
      display: 'flex',
      flexDirection: 'column',
      gap: '0.25rem',
      borderRight: '1px solid rgba(255,255,255,0.06)',
    }}>
      {/* Header label */}
      <div style={{ padding: '0 0.5rem 1rem', borderBottom: '1px solid rgba(255,255,255,0.08)', marginBottom: '0.5rem' }}>
        <div style={{ fontSize: '0.65rem', fontWeight: 700, letterSpacing: '0.12em', color: 'rgba(255,255,255,0.35)', textTransform: 'uppercase', marginBottom: '0.25rem' }}>
          Research Pipeline
        </div>
        <div style={{ fontSize: '0.78rem', color: 'rgba(255,255,255,0.6)', fontWeight: 500 }}>
          12-Week Development Roadmap
        </div>
      </div>

      {/* Phase list */}
      {PHASES.map((phase) => {
        const Icon = phase.icon;
        return (
          <div
            key={phase.num}
            className={`phase-item ${phase.active ? 'active' : 'locked'}`}
            style={{ marginBottom: '0.1rem' }}
          >
            {/* Phase number circle */}
            <div style={{
              width: 32, height: 32, borderRadius: '50%', flexShrink: 0,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              background: phase.active ? phase.color : phase.done ? 'rgba(16,185,129,0.2)' : 'rgba(255,255,255,0.08)',
              boxShadow: phase.active ? `0 0 12px ${phase.color}55` : 'none',
              transition: 'all 0.2s',
            }}>
              {phase.active ? (
                <Icon size={15} color="#fff" />
              ) : phase.done ? (
                <CheckCircle2 size={15} color="#34d399" />
              ) : (
                <Lock size={12} color="rgba(255,255,255,0.3)" />
              )}
            </div>

            {/* Text */}
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{
                fontSize: '0.78rem',
                fontWeight: phase.active ? 700 : 500,
                color: phase.active ? '#fff' : 'rgba(255,255,255,0.4)',
                display: 'flex', alignItems: 'center', gap: '0.4rem',
              }}>
                <span style={{ color: phase.active ? phase.color : 'rgba(255,255,255,0.25)', fontSize: '0.65rem', fontWeight: 700 }}>
                  P{phase.num}
                </span>
                {phase.label}
              </div>
              <div style={{ fontSize: '0.68rem', color: phase.active ? 'rgba(255,255,255,0.5)' : 'rgba(255,255,255,0.22)', marginTop: '0.1rem' }}>
                {phase.sub}
              </div>
            </div>

            {/* Active indicator */}
            {phase.active && (
              <div style={{
                width: 6, height: 6, borderRadius: '50%',
                background: phase.color,
                boxShadow: `0 0 8px ${phase.color}`,
                animation: 'pulse 2s infinite',
                flexShrink: 0,
              }} />
            )}
          </div>
        );
      })}

      {/* Footer note */}
      <div style={{
        marginTop: 'auto', paddingTop: '1.25rem', borderTop: '1px solid rgba(255,255,255,0.08)',
        fontSize: '0.65rem', color: 'rgba(255,255,255,0.3)', textAlign: 'center', lineHeight: 1.6,
      }}>
        <FlaskConical size={14} style={{ display: 'block', margin: '0 auto 0.4rem', opacity: 0.4 }} />
        Phases 2–9 unlock as the<br />framework is developed
      </div>
    </aside>
  );
};

