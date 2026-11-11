import React, { useState, useEffect } from 'react';
import { X, Cpu, Terminal, CheckCircle2, ShieldCheck } from 'lucide-react';

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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs">
      <div className="bg-white rounded-xl shadow-2xl max-w-3xl w-full max-h-[85vh] flex flex-col overflow-hidden border border-slate-200">
        <div className="p-5 border-b border-slate-200 flex items-center justify-between bg-slate-900 text-white">
          <div className="flex items-center gap-2.5">
            <Cpu className="h-5 w-5 text-indigo-400" />
            <div>
              <h2 className="text-base font-bold font-serif">
                Model Context Protocol (MCP) Server
              </h2>
              <p className="text-[11px] text-slate-300">
                Official Python MCP Server: <code className="font-mono text-indigo-300">academic-literature-review-mcp</code>
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-white rounded-md hover:bg-slate-800 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="p-6 overflow-y-auto space-y-4 text-xs flex-1">
          <div className="p-3.5 bg-indigo-50/70 rounded-lg border border-indigo-100 flex items-start gap-3">
            <ShieldCheck className="h-5 w-5 text-indigo-600 shrink-0 mt-0.5" />
            <div className="text-slate-700 leading-relaxed">
              <strong className="text-indigo-950 block mb-0.5">Autonomous Multi-Agent Architecture</strong>
              These tools are exposed via the official Python MCP SDK. In future phases, autonomous research agents (e.g. Counterevidence Searcher, Gap Verifier) will call these tools to retrieve citations and verify scientific claims without human intervention.
            </div>
          </div>

          <h3 className="font-bold uppercase tracking-wider text-slate-800 text-xs">
            Exposed MCP Tools Directory ({toolsData?.tools?.length || 6})
          </h3>

          <div className="space-y-3">
            {toolsData?.tools?.map((tool: any, idx: number) => (
              <div key={idx} className="p-4 rounded-lg border border-slate-200 bg-slate-50/50 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-mono font-bold text-indigo-700 text-xs flex items-center gap-1.5">
                    <Terminal className="h-3.5 w-3.5 text-slate-500" />
                    {tool.name}
                  </span>
                  <span className="badge bg-emerald-50 text-emerald-800 border-emerald-200 text-[10px]">
                    MCP Tool
                  </span>
                </div>
                <p className="text-slate-600 text-xs">{tool.description}</p>
                <div className="pt-1.5 border-t border-slate-200/60">
                  <span className="text-[10px] uppercase font-semibold text-slate-400 block mb-1">
                    Parameters Schema:
                  </span>
                  <div className="grid grid-cols-2 gap-1.5 font-mono text-[11px] text-slate-600 bg-white p-2 rounded border border-slate-200">
                    {Object.entries(tool.parameters).map(([param, type]) => (
                      <div key={param}>
                        <strong className="text-slate-900">{param}:</strong> {String(type)}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="p-3.5 border-t border-slate-200 bg-slate-50 flex items-center justify-end">
          <button onClick={onClose} className="btn-secondary py-1 px-4 text-xs">
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

