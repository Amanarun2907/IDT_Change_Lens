import React, { useMemo, useState } from 'react';
import {
  ReactFlow,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  MarkerType,
  Node,
  Edge
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { ImpactGraph as ImpactGraphType } from '../types';
import { Layers, Zap, Info, ShieldAlert, Cpu } from 'lucide-react';

interface ImpactGraphProps {
  graph: ImpactGraphType;
}

export const ImpactGraph: React.FC<ImpactGraphProps> = ({ graph }) => {
  const [selectedNode, setSelectedNode] = useState<any | null>(null);

  // Transform backend graph nodes into React Flow Nodes with circular or layered layout
  const initialNodes: Node[] = useMemo(() => {
    if (!graph || !graph.nodes || graph.nodes.length === 0) {
      return [
        {
          id: 'placeholder',
          data: { label: 'No dependencies detected' },
          position: { x: 250, y: 150 },
          style: { background: '#1e293b', color: '#94a3b8', border: '1px solid #334155', borderRadius: '8px' }
        }
      ];
    }

    const modifiedNodes = graph.nodes.filter(n => n.status === 'MODIFIED');
    const callerNodes = graph.nodes.filter(n => n.status === 'CALLER');
    const dependentNodes = graph.nodes.filter(n => n.status === 'DEPENDENT' || n.type === 'API');
    const otherNodes = graph.nodes.filter(n => !['MODIFIED', 'CALLER', 'DEPENDENT'].includes(n.status) && n.type !== 'API');

    const result: Node[] = [];

    // Column 1: Callers (Left)
    callerNodes.forEach((node, i) => {
      result.push({
        id: node.id,
        data: { label: node.label, nodeData: node },
        position: { x: 50, y: 80 + i * 90 },
        style: {
          background: '#1e1b4b',
          color: '#c7d2fe',
          border: '1.5px solid #6366f1',
          borderRadius: '10px',
          padding: '10px 14px',
          fontSize: '12px',
          fontWeight: 600,
          boxShadow: '0 4px 12px rgba(99, 102, 241, 0.15)'
        }
      });
    });

    // Column 2: Modified Functions / Symbols (Center)
    modifiedNodes.forEach((node, i) => {
      const isHigh = node.severity === 'HIGH' || node.severity === 'CRITICAL';
      result.push({
        id: node.id,
        data: { label: node.label, nodeData: node },
        position: { x: 380, y: 60 + i * 110 },
        style: {
          background: isHigh ? '#450a0a' : '#2e1065',
          color: isHigh ? '#fca5a5' : '#e9d5ff',
          border: isHigh ? '2px solid #ef4444' : '2px solid #a855f7',
          borderRadius: '12px',
          padding: '12px 18px',
          fontSize: '13px',
          fontWeight: 700,
          boxShadow: isHigh ? '0 0 20px rgba(239, 68, 68, 0.35)' : '0 0 16px rgba(168, 85, 247, 0.25)'
        }
      });
    });

    // Column 3: Downstream APIs & Dependents (Right)
    [...dependentNodes, ...otherNodes].forEach((node, i) => {
      const isApi = node.type === 'API';
      result.push({
        id: node.id,
        data: { label: node.label, nodeData: node },
        position: { x: 720, y: 80 + i * 100 },
        style: {
          background: isApi ? '#083344' : '#0f172a',
          color: isApi ? '#67e8f9' : '#94a3b8',
          border: isApi ? '1.5px solid #06b6d4' : '1px solid #334155',
          borderRadius: '10px',
          padding: '10px 14px',
          fontSize: '12px',
          fontWeight: 600,
          boxShadow: isApi ? '0 0 16px rgba(6, 182, 212, 0.25)' : 'none'
        }
      });
    });

    return result;
  }, [graph]);

  const initialEdges: Edge[] = useMemo(() => {
    if (!graph || !graph.edges) return [];
    return graph.edges.map((edge) => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      label: edge.label || edge.relationship,
      animated: edge.relationship === 'CALLS',
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: edge.verified ? '#3b82f6' : '#94a3b8',
      },
      style: {
        stroke: edge.verified ? '#3b82f6' : '#64748b',
        strokeWidth: 2,
      },
      labelStyle: {
        fill: '#94a3b8',
        fontSize: 10,
        fontWeight: 500,
      },
      labelBgStyle: {
        fill: '#0f172a',
        fillOpacity: 0.9,
      }
    }));
  }, [graph]);

  const [nodes, , onNodesChange] = useNodesState(initialNodes);
  const [edges, , onEdgesChange] = useEdgesState(initialEdges);

  const onNodeClick = (_: any, node: Node) => {
    setSelectedNode(node.data?.nodeData || null);
  };

  return (
    <div className="relative glass-panel rounded-xl overflow-hidden border border-slate-800">
      {/* Top Legend Bar */}
      <div className="bg-slate-900/90 border-b border-slate-800 px-4 py-2.5 flex flex-wrap items-center justify-between text-xs gap-3">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-indigo-500"></span>
            <span className="text-slate-300">Callers</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-purple-500 border border-red-500"></span>
            <span className="text-slate-300">Modified Symbol</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-cyan-500"></span>
            <span className="text-slate-300">Exposed APIs / Downstream</span>
          </div>
        </div>

        <span className="text-slate-400 font-mono text-[11px]">
          {graph.nodes?.length || 0} nodes · {graph.edges?.length || 0} dependency relationships
        </span>
      </div>

      {/* Graph Canvas */}
      <div className="h-[520px] w-full bg-[#080c15]">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeClick={onNodeClick}
          fitView
          minZoom={0.2}
          maxZoom={2}
        >
          <Background color="#1e293b" gap={20} size={1} />
          <Controls className="bg-slate-900 border border-slate-700 text-slate-300 rounded-lg overflow-hidden" />
        </ReactFlow>
      </div>

      {/* Selected Node Details Drawer */}
      {selectedNode && (
        <div className="absolute bottom-4 right-4 max-w-sm glass-panel p-4 rounded-xl border border-blue-500/40 shadow-xl bg-slate-900/95 z-20">
          <div className="flex items-center justify-between pb-2 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <Zap className="w-4 h-4 text-blue-400" />
              <span className="font-semibold text-white text-sm">{selectedNode.label}</span>
            </div>
            <button
              onClick={() => setSelectedNode(null)}
              className="text-slate-400 hover:text-white text-xs px-1.5 py-0.5 rounded bg-slate-800"
            >
              ✕
            </button>
          </div>
          <div className="mt-2 text-xs space-y-1.5 text-slate-300">
            <div><span className="text-slate-400">Type:</span> {selectedNode.type}</div>
            <div><span className="text-slate-400">Status:</span> {selectedNode.status}</div>
            {selectedNode.details?.file && (
              <div><span className="text-slate-400">File:</span> <span className="font-mono text-slate-200">{selectedNode.details.file}</span></div>
            )}
            {selectedNode.details?.impact_type && (
              <div><span className="text-slate-400">Impact Classification:</span> {selectedNode.details.impact_type}</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
