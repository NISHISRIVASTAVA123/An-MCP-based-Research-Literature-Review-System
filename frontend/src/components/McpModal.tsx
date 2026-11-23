import React, { useState, useEffect } from 'react';
import { X, Cpu, Terminal, ShieldCheck, Zap } from 'lucide-react';

interface McpModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const McpModal: React.FC<McpModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  const [toolsData, setToolsData] = useState<any>(null);

  useEffect(() => {
    fetch('/api/mcp/tools')
      .then((r) => r.json())
      .then((d) => setToolsData(d))
      .catch((e) => console.error(e));
  }, []);

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-panel"
        style={{ maxWidth: 740, width: '100%', display: 'flex', flexDirection: 'column' }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div style={{ padding: '1.25rem 1.75rem', borderBottom: '1px solid rgba(255,255,255,0.1)', background: 'linear-gradient(135deg, #1e1b4b 0%, #312e81 100%)', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div style={{ width: 36, height: 36, borderRadius: '0.5rem', background: 'rgba(129,140,248,0.25)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Cpu size={20} color="#a5b4fc" />
            </div>
            <div>
              <h2 style={{ fontFamily: 'Sora, sans-serif', fontSize: '1.05rem', fontWeight: 700 }}>
                Model Context Protocol (MCP) Server
              </h2>
              <p style={{ fontSize: '0.72rem', color: 'rgba(255,255,255,0.6)' }}>
                Server: <code style={{ fontFamily: 'JetBrains Mono, monospace', color: '#a5b4fc' }}>academic-literature-review-mcp</code> · Python MCP SDK v2
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="btn btn-ghost"
            style={{ borderRadius: '0.4rem', padding: '0.4rem', color: 'rgba(255,255,255,0.7)' }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Content Body */}
        <div style={{ padding: '1.5rem 1.75rem', overflowY: 'auto', maxHeight: 480, display: 'flex', flexDirection: 'column', gap: '1.25rem', fontSize: '0.82rem' }}>
          {/* Banner */}
          <div style={{ background: '#eef2ff', borderRadius: '0.75rem', padding: '1rem 1.25rem', border: '1px solid #c7d2fe', display: 'flex', gap: '0.75rem', alignItems: 'flex-start' }}>
            <ShieldCheck size={20} color="#4f46e5" style={{ flexShrink: 0, marginTop: 2 }} />
            <div style={{ color: '#312e81', lineHeight: 1.55 }}>
              <strong style={{ display: 'block', fontSize: '0.85rem', marginBottom: '0.2rem' }}>
                Autonomous Agent Interoperability Layer
              </strong>
              These native MCP tools are directly callable by Claude, Gemini, or any MCP-compliant autonomous multi-agent orchestrator. In subsequent phases (e.g. Counterevidence Searcher, Claim Verifier), agents will autonomously invoke these tools to conduct scientific literature review without human oversight.
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '0.72rem', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: '#64748b' }}>
              Registered MCP Tools Directory ({toolsData?.tools?.length || 6})
            </span>
            <span className="badge badge-success" style={{ fontSize: '0.68rem' }}>
              Active &amp; Ready
            </span>
          </div>

          {/* Tools list */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {toolsData?.tools?.map((tool: any, idx: number) => (
              <div
                key={idx}
                style={{
                  background: '#f8fafc',
                  borderRadius: '0.65rem',
                  border: '1px solid #e2e8f0',
                  padding: '1rem 1.25rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.5rem',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span style={{ fontFamily: 'JetBrains Mono, monospace', fontWeight: 700, color: '#4338ca', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <Terminal size={14} color="#6366f1" />
                    {tool.name}
                  </span>
                  <span className="badge badge-brand" style={{ fontSize: '0.65rem' }}>
                    Tool Function
                  </span>
                </div>

                <p style={{ color: '#475569', fontSize: '0.78rem' }}>
                  {tool.description}
                </p>

                <div style={{ paddingTop: '0.4rem', borderTop: '1px solid #e2e8f0' }}>
                  <span style={{ fontSize: '0.65rem', fontWeight: 700, textTransform: 'uppercase', color: '#94a3b8', display: 'block', marginBottom: '0.3rem' }}>
                    Parameters Schema:
                  </span>
                  <div style={{ background: '#fff', padding: '0.5rem 0.75rem', borderRadius: '0.4rem', border: '1px solid #e2e8f0', display: 'flex', flexWrap: 'wrap', gap: '0.75rem', fontFamily: 'JetBrains Mono, monospace', fontSize: '0.72rem' }}>
                    {Object.entries(tool.parameters).map(([param, type]) => (
                      <div key={param}>
                        <span style={{ color: '#0f172a', fontWeight: 700 }}>{param}:</span> <span style={{ color: '#6366f1' }}>{String(type)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div style={{ padding: '0.85rem 1.75rem', borderTop: '1px solid #e2e8f0', background: '#f8fafc', display: 'flex', justifyContent: 'flex-end' }}>
          <button onClick={onClose} className="btn btn-secondary btn-sm">
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
