import React, { useState, useEffect, useMemo, useRef } from 'react';
import {
  Network,
  RefreshCw,
  Search,
  Filter,
  ZoomIn,
  ZoomOut,
  Maximize2,
  FileText,
  ShieldCheck,
  ChevronRight,
  Download,
  Layers,
  ArrowRight,
  ExternalLink,
  BookOpen,
  Activity,
  X,
  History,
  CheckCircle2,
  AlertCircle,
} from 'lucide-react';
import { ResearchRequest } from '../types';
import {
  GraphNode,
  GraphEdge,
  EvidenceGraphData,
  ProvenanceChain,
} from '../types/graph';
import {
  getEvidenceGraph,
  buildEvidenceGraph,
  synchronizeEvidenceGraph,
  getClaimProvenance,
} from '../services/api';
import { GraphBuildModal } from './GraphBuildModal';

interface EvidenceGraphViewProps {
  request: ResearchRequest;
  onBackToScreening?: () => void;
}

const NODE_COLORS: Record<string, { bg: string; border: string; text: string }> = {
  RESEARCH_REQUEST:    { bg: '#312e81', border: '#4338ca', text: '#fff' },
  RESEARCH_OBJECTIVE:  { bg: '#78350f', border: '#b45309', text: '#fef3c7' },
  RESEARCH_QUESTION:   { bg: '#581c87', border: '#7e22ce', text: '#f3e8ff' },
  PAPER:               { bg: '#1e1b4b', border: '#4f46e5', text: '#e0e7ff' },
  AUTHOR:              { bg: '#334155', border: '#64748b', text: '#f1f5f9' },
  METHOD:              { bg: '#064e3b', border: '#059669', text: '#d1fae5' },
  MODEL:               { bg: '#134e4a', border: '#0d9488', text: '#ccfbf1' },
  DATASET:             { bg: '#713f12', border: '#d97706', text: '#fef3c7' },
  METRIC:              { bg: '#164e63', border: '#0891b2', text: '#cffafe' },
  FINDING:             { bg: '#3b0764', border: '#7c3aed', text: '#ede9fe' },
  CLAIM:               { bg: '#172554', border: '#2563eb', text: '#dbeafe' },
  LIMITATION:          { bg: '#881337', border: '#e11d48', text: '#ffe4e6' },
  FUTURE_DIRECTION:    { bg: '#14532d', border: '#16a34a', text: '#dcfce7' },
  EVIDENCE_PASSAGE:    { bg: '#0f172a', border: '#475569', text: '#94a3b8' },
};

export const EvidenceGraphView: React.FC<EvidenceGraphViewProps> = ({
  request,
  onBackToScreening,
}) => {
  const [graphData, setGraphData] = useState<EvidenceGraphData | null>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [provenanceModal, setProvenanceModal] = useState<ProvenanceChain | null>(null);
  const [isBuildModalOpen, setIsBuildModalOpen] = useState(false);

  const [isLoading, setIsLoading] = useState(false);
  const [isBuilding, setIsBuilding] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Filters & Search
  const [selectedType, setSelectedType] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  // Canvas Pan & Zoom
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  const canvasRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (request?.id) {
      loadGraph();
    }
  }, [request.id]);

  const loadGraph = async () => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const data = await getEvidenceGraph(request.id);
      setGraphData(data);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to load evidence graph.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleBuildGraph = async (isSync = false) => {
    setIsBuilding(true);
    setErrorMsg(null);
    try {
      if (isSync) {
        await synchronizeEvidenceGraph(request.id);
      } else {
        await buildEvidenceGraph(request.id);
      }
      await loadGraph();
    } catch (err: any) {
      setErrorMsg(err.detail || err.message || 'Graph build failed.');
    } finally {
      setIsBuilding(false);
    }
  };

  const handleTraceProvenance = async (claimId: string) => {
    try {
      const trace = await getClaimProvenance(claimId);
      setProvenanceModal(trace);
    } catch (err: any) {
      alert(`Could not trace provenance: ${err.message}`);
    }
  };

  // Node Positions Calculation (Deterministic Circular Clustering Layout)
  const layout = useMemo(() => {
    if (!graphData || graphData.nodes.length === 0) return { positions: {}, width: 1200, height: 800 };

    const positions: Record<string, { x: number; y: number }> = {};
    const nodes = graphData.nodes;

    const centerX = 600;
    const centerY = 450;

    // Center root request node
    const reqNode = nodes.find((n) => n.node_type === 'RESEARCH_REQUEST');
    if (reqNode) {
      positions[reqNode.id] = { x: centerX, y: centerY };
    }

    // Inner ring: Questions, Objectives, Papers
    const innerNodes = nodes.filter(
      (n) => ['PAPER', 'RESEARCH_QUESTION', 'RESEARCH_OBJECTIVE'].includes(n.node_type)
    );
    const innerRadius = 260;
    innerNodes.forEach((n, idx) => {
      const angle = (2 * Math.PI * idx) / Math.max(innerNodes.length, 1);
      positions[n.id] = {
        x: centerX + innerRadius * Math.cos(angle),
        y: centerY + innerRadius * Math.sin(angle),
      };
    });

    // Middle ring: Methods, Models, Datasets, Metrics
    const midNodes = nodes.filter(
      (n) => ['METHOD', 'MODEL', 'DATASET', 'METRIC'].includes(n.node_type)
    );
    const midRadius = 450;
    midNodes.forEach((n, idx) => {
      const angle = (2 * Math.PI * idx) / Math.max(midNodes.length, 1) + 0.3;
      positions[n.id] = {
        x: centerX + midRadius * Math.cos(angle),
        y: centerY + midRadius * Math.sin(angle),
      };
    });

    // Outer ring: Claims, Findings, Limitations, Passages, Authors
    const outerNodes = nodes.filter(
      (n) => ['CLAIM', 'FINDING', 'LIMITATION', 'FUTURE_DIRECTION', 'EVIDENCE_PASSAGE', 'AUTHOR'].includes(n.node_type)
    );
    const outerRadius = 660;
    outerNodes.forEach((n, idx) => {
      const angle = (2 * Math.PI * idx) / Math.max(outerNodes.length, 1);
      positions[n.id] = {
        x: centerX + outerRadius * Math.cos(angle),
        y: centerY + outerRadius * Math.sin(angle),
      };
    });

    return { positions, width: 1400, height: 1000 };
  }, [graphData]);

  // Filtering
  const filteredNodes = useMemo(() => {
    if (!graphData) return [];
    return graphData.nodes.filter((n) => {
      const matchesType = selectedType === 'ALL' || n.node_type === selectedType;
      const matchesSearch =
        !searchQuery ||
        n.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
        n.normalized_label.toLowerCase().includes(searchQuery.toLowerCase());
      return matchesType && matchesSearch;
    });
  }, [graphData, selectedType, searchQuery]);

  const filteredNodeIds = useMemo(() => new Set(filteredNodes.map((n) => n.id)), [filteredNodes]);

  const filteredEdges = useMemo(() => {
    if (!graphData) return [];
    return graphData.edges.filter(
      (e) => filteredNodeIds.has(e.source_node_id) && filteredNodeIds.has(e.target_node_id)
    );
  }, [graphData, filteredNodeIds]);

  // Pan handlers
  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.button === 0) {
      setIsDragging(true);
      setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging) {
      setPan({ x: e.clientX - dragStart.x, y: e.clientY - dragStart.y });
    }
  };

  const handleMouseUp = () => setIsDragging(false);

  const resetView = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  const exportGraphJson = () => {
    if (!graphData) return;
    const blob = new Blob([JSON.stringify(graphData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `evidence_graph_${request.id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const stats = graphData?.statistics;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', minHeight: '85vh', gap: '1rem' }}>
      {/* Top Banner & KPI Strip */}
      <div
        style={{
          background: 'linear-gradient(135deg, #1e1b4b 0%, #312e81 60%, #1e3a5f 100%)',
          borderRadius: '1rem',
          padding: '1.25rem 1.75rem',
          color: '#fff',
          boxShadow: '0 10px 25px -5px rgba(0,0,0,0.15)',
        }}
      >
        <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: '1rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
              <div
                style={{
                  width: 38,
                  height: 38,
                  borderRadius: '0.6rem',
                  background: 'rgba(255,255,255,0.15)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <Network size={22} color="#818cf8" />
              </div>
              <div>
                <h1 style={{ fontSize: '1.25rem', fontWeight: 800, margin: 0, letterSpacing: '-0.01em' }}>
                  Scientific Evidence Knowledge Graph
                </h1>
                <div style={{ fontSize: '0.78rem', color: '#cbd5e1', marginTop: 2 }}>
                  Topic: <strong>{request.topic}</strong> · Verifiable Cross-Paper Evidence Matrix
                </div>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <button
              onClick={() => handleBuildGraph(false)}
              disabled={isBuilding}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.45rem',
                padding: '0.55rem 1.1rem',
                borderRadius: '0.5rem',
                background: '#6366f1',
                color: '#fff',
                border: 'none',
                fontSize: '0.82rem',
                fontWeight: 700,
                cursor: isBuilding ? 'not-allowed' : 'pointer',
                boxShadow: '0 4px 12px rgba(99,102,241,0.3)',
              }}
            >
              <RefreshCw size={15} className={isBuilding ? 'animate-spin' : ''} />
              <span>{isBuilding ? 'Building Graph...' : 'Rebuild Graph'}</span>
            </button>

            <button
              onClick={() => handleBuildGraph(true)}
              disabled={isBuilding}
              title="Synchronize newly added Phase 2 extractions"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.45rem',
                padding: '0.55rem 0.9rem',
                borderRadius: '0.5rem',
                background: 'rgba(255,255,255,0.1)',
                color: '#fff',
                border: '1px solid rgba(255,255,255,0.2)',
                fontSize: '0.82rem',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              <Layers size={15} />
              <span>Sync Extractions</span>
            </button>

            <button
              onClick={() => setIsBuildModalOpen(true)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.45rem',
                padding: '0.55rem 0.9rem',
                borderRadius: '0.5rem',
                background: 'rgba(255,255,255,0.1)',
                color: '#fff',
                border: '1px solid rgba(255,255,255,0.2)',
                fontSize: '0.82rem',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              <ShieldCheck size={15} color="#34d399" />
              <span>Audit Report</span>
            </button>

            <button
              onClick={exportGraphJson}
              disabled={!graphData || graphData.nodes.length === 0}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem',
                padding: '0.55rem 0.85rem',
                borderRadius: '0.5rem',
                background: 'rgba(255,255,255,0.1)',
                color: '#cbd5e1',
                border: '1px solid rgba(255,255,255,0.15)',
                fontSize: '0.82rem',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              <Download size={14} />
              <span>Export</span>
            </button>
          </div>
        </div>

        {/* Real-time KPI Stats Banner */}
        {stats && (
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
              gap: '0.65rem',
              marginTop: '1.25rem',
              paddingTop: '1rem',
              borderTop: '1px solid rgba(255,255,255,0.1)',
            }}
          >
            <div>
              <div style={{ fontSize: '0.65rem', color: '#94a3b8', fontWeight: 600, textTransform: 'uppercase' }}>Nodes</div>
              <div style={{ fontSize: '1.3rem', fontWeight: 800 }}>{stats.total_nodes}</div>
            </div>
            <div>
              <div style={{ fontSize: '0.65rem', color: '#94a3b8', fontWeight: 600, textTransform: 'uppercase' }}>Relationships</div>
              <div style={{ fontSize: '1.3rem', fontWeight: 800 }}>{stats.total_edges}</div>
            </div>
            <div>
              <div style={{ fontSize: '0.65rem', color: '#94a3b8', fontWeight: 600, textTransform: 'uppercase' }}>Papers</div>
              <div style={{ fontSize: '1.3rem', fontWeight: 800 }}>{stats.papers_count}</div>
            </div>
            <div>
              <div style={{ fontSize: '0.65rem', color: '#94a3b8', fontWeight: 600, textTransform: 'uppercase' }}>Methods</div>
              <div style={{ fontSize: '1.3rem', fontWeight: 800, color: '#6ee7b7' }}>{stats.methods_count}</div>
            </div>
            <div>
              <div style={{ fontSize: '0.65rem', color: '#94a3b8', fontWeight: 600, textTransform: 'uppercase' }}>Datasets</div>
              <div style={{ fontSize: '1.3rem', fontWeight: 800, color: '#fde047' }}>{stats.datasets_count}</div>
            </div>
            <div>
              <div style={{ fontSize: '0.65rem', color: '#94a3b8', fontWeight: 600, textTransform: 'uppercase' }}>Claims</div>
              <div style={{ fontSize: '1.3rem', fontWeight: 800, color: '#93c5fd' }}>{stats.claims_count}</div>
            </div>
            <div>
              <div style={{ fontSize: '0.65rem', color: '#94a3b8', fontWeight: 600, textTransform: 'uppercase' }}>Passages</div>
              <div style={{ fontSize: '1.3rem', fontWeight: 800, color: '#cbd5e1' }}>{stats.evidence_passages_count}</div>
            </div>
            <div>
              <div style={{ fontSize: '0.65rem', color: '#94a3b8', fontWeight: 600, textTransform: 'uppercase' }}>Verified Evidence</div>
              <div style={{ fontSize: '1.3rem', fontWeight: 800, color: '#34d399' }}>
                {stats.claims_with_evidence_percentage}%
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Control Bar: Search & Filter Types */}
      <div
        style={{
          background: '#fff',
          borderRadius: '0.75rem',
          padding: '0.75rem 1.25rem',
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '1rem',
          border: '1px solid #e2e8f0',
        }}
      >
        {/* Search */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', maxWidth: 320, width: '100%', position: 'relative' }}>
          <Search size={16} color="#94a3b8" style={{ position: 'absolute', left: 10 }} />
          <input
            type="text"
            placeholder="Search entities (e.g. BERT, LIAR, accuracy)..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              width: '100%',
              padding: '0.45rem 0.75rem 0.45rem 2.1rem',
              borderRadius: '0.5rem',
              border: '1px solid #cbd5e1',
              fontSize: '0.82rem',
              outline: 'none',
            }}
          />
        </div>

        {/* Node Type Pills */}
        <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '0.35rem' }}>
          {[
            { id: 'ALL', label: 'All Entities' },
            { id: 'PAPER', label: 'Papers' },
            { id: 'METHOD', label: 'Methods' },
            { id: 'DATASET', label: 'Datasets' },
            { id: 'CLAIM', label: 'Claims' },
            { id: 'FINDING', label: 'Findings' },
            { id: 'LIMITATION', label: 'Limitations' },
            { id: 'EVIDENCE_PASSAGE', label: 'Evidence Passages' },
          ].map((pill) => (
            <button
              key={pill.id}
              onClick={() => setSelectedType(pill.id)}
              style={{
                padding: '0.3rem 0.7rem',
                borderRadius: '100px',
                fontSize: '0.74rem',
                fontWeight: 600,
                border: selectedType === pill.id ? '1px solid #6366f1' : '1px solid #e2e8f0',
                background: selectedType === pill.id ? '#ede9fe' : '#f8fafc',
                color: selectedType === pill.id ? '#4f46e5' : '#64748b',
                cursor: 'pointer',
              }}
            >
              {pill.label}
            </button>
          ))}
        </div>

        {/* Zoom & View Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <button
            onClick={() => setZoom((z) => Math.min(z + 0.2, 2.5))}
            style={{ padding: '0.4rem', border: '1px solid #cbd5e1', borderRadius: '0.375rem', background: '#fff', cursor: 'pointer' }}
            title="Zoom In"
          >
            <ZoomIn size={16} />
          </button>
          <button
            onClick={() => setZoom((z) => Math.max(z - 0.2, 0.4))}
            style={{ padding: '0.4rem', border: '1px solid #cbd5e1', borderRadius: '0.375rem', background: '#fff', cursor: 'pointer' }}
            title="Zoom Out"
          >
            <ZoomOut size={16} />
          </button>
          <button
            onClick={resetView}
            style={{ padding: '0.4rem', border: '1px solid #cbd5e1', borderRadius: '0.375rem', background: '#fff', cursor: 'pointer' }}
            title="Reset View"
          >
            <Maximize2 size={16} />
          </button>
        </div>
      </div>

      {/* Main Graph Canvas & Side Inspector Drawer */}
      <div style={{ display: 'flex', flex: 1, gap: '1rem', minHeight: 650, position: 'relative' }}>
        {/* Interactive Canvas */}
        <div
          ref={canvasRef}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          style={{
            flex: 1,
            background: '#090d16',
            borderRadius: '1rem',
            border: '1px solid #1e293b',
            overflow: 'hidden',
            position: 'relative',
            cursor: isDragging ? 'grabbing' : 'grab',
            userSelect: 'none',
          }}
        >
          {isLoading ? (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#94a3b8' }}>
              <RefreshCw size={32} className="animate-spin" style={{ marginRight: '0.75rem' }} />
              <span>Loading evidence knowledge graph...</span>
            </div>
          ) : !graphData || graphData.nodes.length === 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#94a3b8' }}>
              <Network size={48} color="#475569" style={{ marginBottom: '1rem' }} />
              <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f1f5f9' }}>Evidence Graph Not Constructed Yet</div>
              <div style={{ fontSize: '0.82rem', color: '#64748b', marginTop: '0.25rem', marginBottom: '1.5rem' }}>
                Construct knowledge graph nodes and edges from Phase 2 eligible screening decisions.
              </div>
              <button
                onClick={() => handleBuildGraph(false)}
                disabled={isBuilding}
                style={{
                  padding: '0.65rem 1.35rem',
                  borderRadius: '0.5rem',
                  background: '#6366f1',
                  color: '#fff',
                  border: 'none',
                  fontWeight: 700,
                  fontSize: '0.88rem',
                  cursor: 'pointer',
                  boxShadow: '0 4px 14px rgba(99,102,241,0.4)',
                }}
              >
                {isBuilding ? 'Building Graph...' : 'Build Evidence Graph'}
              </button>
            </div>
          ) : (
            <svg
              width="100%"
              height="100%"
              style={{ minHeight: 650 }}
              viewBox={`0 0 ${layout.width} ${layout.height}`}
            >
              <defs>
                <marker
                  id="arrow"
                  viewBox="0 0 10 10"
                  refX="18"
                  refY="5"
                  markerWidth="6"
                  markerHeight="6"
                  orient="auto-start-reverse"
                >
                  <path d="M 0 0 L 10 5 L 0 10 z" fill="#475569" />
                </marker>
                <marker
                  id="arrow-support"
                  viewBox="0 0 10 10"
                  refX="18"
                  refY="5"
                  markerWidth="6"
                  markerHeight="6"
                  orient="auto-start-reverse"
                >
                  <path d="M 0 0 L 10 5 L 0 10 z" fill="#10b981" />
                </marker>
              </defs>

              <g transform={`translate(${pan.x}, ${pan.y}) scale(${zoom})`}>
                {/* Edges */}
                {filteredEdges.map((e) => {
                  const src = layout.positions[e.source_node_id];
                  const tgt = layout.positions[e.target_node_id];
                  if (!src || !tgt) return null;

                  const isSupport = e.relationship_type === 'SUPPORTS';
                  const strokeColor = isSupport ? '#10b981' : '#334155';
                  const strokeWidth = isSupport ? 1.8 : 1.2;

                  return (
                    <g key={e.id}>
                      <line
                        x1={src.x}
                        y1={src.y}
                        x2={tgt.x}
                        y2={tgt.y}
                        stroke={strokeColor}
                        strokeWidth={strokeWidth}
                        strokeOpacity={0.65}
                        markerEnd={isSupport ? 'url(#arrow-support)' : 'url(#arrow)'}
                      />
                    </g>
                  );
                })}

                {/* Nodes */}
                {filteredNodes.map((n) => {
                  const pos = layout.positions[n.id];
                  if (!pos) return null;

                  const style = NODE_COLORS[n.node_type] || { bg: '#1e293b', border: '#475569', text: '#cbd5e1' };
                  const isSelected = selectedNode?.id === n.id;
                  const isPaper = n.node_type === 'PAPER';
                  const radius = isPaper ? 24 : 16;

                  return (
                    <g
                      key={n.id}
                      transform={`translate(${pos.x}, ${pos.y})`}
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedNode(n);
                      }}
                      style={{ cursor: 'pointer' }}
                    >
                      <circle
                        r={radius}
                        fill={style.bg}
                        stroke={isSelected ? '#38bdf8' : style.border}
                        strokeWidth={isSelected ? 3.5 : 2}
                        filter={isSelected ? 'drop-shadow(0 0 8px #38bdf8)' : undefined}
                      />
                      <text
                        dy={radius + 14}
                        textAnchor="middle"
                        fill="#e2e8f0"
                        fontSize={isPaper ? 11 : 9.5}
                        fontWeight={isPaper ? 700 : 500}
                        style={{ pointerEvents: 'none', textShadow: '0 1px 4px rgba(0,0,0,0.8)' }}
                      >
                        {n.label.length > 22 ? n.label.substring(0, 20) + '...' : n.label}
                      </text>
                    </g>
                  );
                })}
              </g>
            </svg>
          )}

          {/* Canvas Floating Legend */}
          <div
            style={{
              position: 'absolute',
              bottom: 16,
              left: 16,
              background: 'rgba(15, 23, 42, 0.85)',
              backdropFilter: 'blur(6px)',
              padding: '0.65rem 1rem',
              borderRadius: '0.5rem',
              border: '1px solid rgba(255,255,255,0.1)',
              display: 'flex',
              flexWrap: 'wrap',
              gap: '0.75rem',
              fontSize: '0.7rem',
              color: '#cbd5e1',
            }}
          >
            {Object.entries(NODE_COLORS).slice(3, 11).map(([type, c]) => (
              <div key={type} style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                <span style={{ width: 10, height: 10, borderRadius: '50%', background: c.border }} />
                <span>{type}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Right Node Inspector Drawer */}
        {selectedNode && (
          <div
            style={{
              width: 360,
              background: '#fff',
              borderRadius: '1rem',
              border: '1px solid #e2e8f0',
              boxShadow: '-4px 0 20px rgba(0,0,0,0.06)',
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden',
            }}
          >
            {/* Inspector Header */}
            <div
              style={{
                padding: '1rem 1.25rem',
                borderBottom: '1px solid #e2e8f0',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                background: '#f8fafc',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span
                  style={{
                    padding: '0.2rem 0.55rem',
                    borderRadius: '100px',
                    fontSize: '0.68rem',
                    fontWeight: 700,
                    background: '#ede9fe',
                    color: '#6366f1',
                    border: '1px solid #ddd6fe',
                  }}
                >
                  {selectedNode.node_type}
                </span>
                <span style={{ fontSize: '0.78rem', fontWeight: 600, color: '#64748b' }}>Entity Inspector</span>
              </div>
              <button
                onClick={() => setSelectedNode(null)}
                style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8' }}
              >
                <X size={18} />
              </button>
            </div>

            {/* Inspector Body */}
            <div style={{ padding: '1.25rem', overflowY: 'auto', flex: 1, display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <h3 style={{ fontSize: '0.98rem', fontWeight: 700, color: '#1e293b', margin: 0 }}>
                  {selectedNode.label}
                </h3>
                <div style={{ fontSize: '0.72rem', color: '#64748b', marginTop: 4 }}>
                  Entity Key: <code style={{ background: '#f1f5f9', padding: '0.1rem 0.3rem', borderRadius: 4 }}>{selectedNode.entity_key}</code>
                </div>
              </div>

              {/* Provenance Trace Action for Claims & Findings */}
              {['CLAIM', 'FINDING'].includes(selectedNode.node_type) && (
                <button
                  onClick={() => handleTraceProvenance(selectedNode.id)}
                  style={{
                    width: '100%',
                    padding: '0.6rem',
                    borderRadius: '0.5rem',
                    background: 'linear-gradient(135deg, #4f46e5 0%, #6366f1 100%)',
                    color: '#fff',
                    border: 'none',
                    fontWeight: 700,
                    fontSize: '0.8rem',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '0.45rem',
                    boxShadow: '0 4px 10px rgba(99,102,241,0.25)',
                  }}
                >
                  <ShieldCheck size={16} />
                  <span>Trace Provenance Chain</span>
                </button>
              )}

              {/* Properties Sheet */}
              <div>
                <h4 style={{ fontSize: '0.74rem', fontWeight: 700, textTransform: 'uppercase', color: '#94a3b8', marginBottom: '0.5rem' }}>
                  Entity Metadata & Properties
                </h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', fontSize: '0.78rem' }}>
                  {Object.entries(selectedNode.properties || {}).map(([k, v]) => (
                    <div
                      key={k}
                      style={{
                        padding: '0.45rem 0.65rem',
                        background: '#f8fafc',
                        borderRadius: '0.375rem',
                        border: '1px solid #f1f5f9',
                      }}
                    >
                      <div style={{ color: '#64748b', fontSize: '0.68rem', textTransform: 'uppercase', fontWeight: 600 }}>{k}</div>
                      <div style={{ color: '#1e293b', marginTop: 2, wordBreak: 'break-word' }}>
                        {typeof v === 'object' ? JSON.stringify(v) : String(v)}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Provenance Modal Dialog */}
      {provenanceModal && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            zIndex: 60,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'rgba(15, 23, 42, 0.65)',
            backdropFilter: 'blur(4px)',
            padding: '1rem',
          }}
        >
          <div
            style={{
              background: '#fff',
              borderRadius: '1rem',
              maxWidth: 680,
              width: '100%',
              padding: '1.5rem',
              boxShadow: '0 25px 50px -12px rgba(0,0,0,0.25)',
              display: 'flex',
              flexDirection: 'column',
              gap: '1.25rem',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid #e2e8f0', paddingBottom: '0.75rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <ShieldCheck size={22} color="#059669" />
                <h3 style={{ fontSize: '1.05rem', fontWeight: 700, margin: 0 }}>Scientific Claim Provenance Chain</h3>
              </div>
              <button onClick={() => setProvenanceModal(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8' }}>
                <X size={20} />
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
              {/* Step 1: Claim */}
              <div style={{ padding: '0.85rem', background: '#eff6ff', borderRadius: '0.5rem', border: '1px solid #bfdbfe' }}>
                <div style={{ fontSize: '0.7rem', fontWeight: 700, color: '#1d4ed8', textTransform: 'uppercase' }}>1. Extracted Claim</div>
                <div style={{ fontSize: '0.88rem', fontWeight: 600, color: '#1e3a8a', marginTop: 4 }}>"{provenanceModal.claim_text}"</div>
                <div style={{ fontSize: '0.72rem', color: '#3b82f6', marginTop: 4 }}>
                  Status: <strong>{provenanceModal.verification_status}</strong> · Scope: <strong>{provenanceModal.source_scope}</strong>
                </div>
              </div>

              {/* Step 2: Evidence Passage */}
              <div style={{ padding: '0.85rem', background: '#f8fafc', borderRadius: '0.5rem', border: '1px solid #e2e8f0' }}>
                <div style={{ fontSize: '0.7rem', fontWeight: 700, color: '#059669', textTransform: 'uppercase' }}>
                  2. Verbatim Supporting Passage (Page {provenanceModal.page_number || 1} · {provenanceModal.section_heading || 'Abstract'})
                </div>
                <div style={{ fontSize: '0.84rem', fontStyle: 'italic', color: '#334155', marginTop: 4, background: '#fff', padding: '0.5rem', borderRadius: 4, border: '1px solid #cbd5e1' }}>
                  "{provenanceModal.exact_passage || 'No verbatim passage quote anchored.'}"
                </div>
              </div>

              {/* Step 3: Source Paper */}
              <div style={{ padding: '0.85rem', background: '#f8fafc', borderRadius: '0.5rem', border: '1px solid #e2e8f0' }}>
                <div style={{ fontSize: '0.7rem', fontWeight: 700, color: '#6366f1', textTransform: 'uppercase' }}>3. Canonical Source Paper</div>
                <div style={{ fontSize: '0.88rem', fontWeight: 600, color: '#1e293b', marginTop: 4 }}>{provenanceModal.paper_title}</div>
                <div style={{ fontSize: '0.72rem', color: '#64748b', marginTop: 4 }}>
                  Paper ID: {provenanceModal.paper_id} · Year: {provenanceModal.publication_year || 'N/A'} · DOI: {provenanceModal.paper_doi || 'N/A'}
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', borderTop: '1px solid #e2e8f0', paddingTop: '0.75rem' }}>
              <button
                onClick={() => setProvenanceModal(null)}
                style={{ padding: '0.45rem 1rem', borderRadius: '0.375rem', background: '#6366f1', color: '#fff', border: 'none', fontWeight: 600, cursor: 'pointer', fontSize: '0.82rem' }}
              >
                Close Provenance Trace
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Build Audit Modal */}
      <GraphBuildModal
        requestId={request.id}
        isOpen={isBuildModalOpen}
        onClose={() => setIsBuildModalOpen(false)}
        onRebuildTriggered={() => handleBuildGraph(false)}
      />
    </div>
  );
};
