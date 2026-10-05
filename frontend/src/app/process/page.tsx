"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import DashboardShell from "@/components/dashboard-shell";
import api from "@/lib/api";
import type {
  UploadHistoryItem,
  ProcessGraphResponse,
  ProcessNode,
  ProcessEdge,
} from "@/lib/types";
import {
  ReactFlow,
  Background,
  Controls,
  type Node,
  type Edge,
  MarkerType,
  useNodesState,
  useEdgesState,
  Position,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

export default function ProcessPage() {
  const [uploads, setUploads] = useState<UploadHistoryItem[]>([]);
  const [selectedUpload, setSelectedUpload] = useState<number | null>(null);
  const [graph, setGraph] = useState<ProcessGraphResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [minFrequency, setMinFrequency] = useState<number>(1);

  useEffect(() => {
    api.get("/upload/history?limit=20").then((r) => {
      setUploads(r.data);
      if (r.data.length > 0) setSelectedUpload(r.data[0].id);
    });
  }, []);

  useEffect(() => {
    if (!selectedUpload) return;
    setLoading(true);
    setMinFrequency(1);
    api
      .get(`/process-mine/graph?upload_id=${selectedUpload}`)
      .then((r) => setGraph(r.data))
      .catch(() => setGraph(null))
      .finally(() => setLoading(false));
  }, [selectedUpload]);

  // Convert API data to React Flow nodes/edges
  const { flowNodes, flowEdges } = useMemo(() => {
    if (!graph) return { flowNodes: [], flowEdges: [] };

    const nodes: Node[] = graph.nodes.map((n, i) => ({
      id: n.id,
      data: {
        label: (
          <div className="text-center">
            <p className="text-[11px] font-medium text-slate-800 leading-tight truncate max-w-[140px]">
              {n.label}
            </p>
            <p className="text-[10px] text-slate-400 mt-0.5 tabular-nums">
              {n.count.toLocaleString()} events
            </p>
          </div>
        ),
      },
      position: { x: (i % 4) * 220 + 40, y: Math.floor(i / 4) * 120 + 40 },
      style: {
        border: n.is_start
          ? "2px solid #059669"
          : n.is_end
          ? "2px solid #dc2626"
          : "1px solid #cbd5e1",
        borderRadius: 6,
        padding: "8px 12px",
        background: n.is_start
          ? "#ecfdf5"
          : n.is_end
          ? "#fef2f2"
          : "#ffffff",
        fontSize: 11,
        width: 180,
      },
      sourcePosition: Position.Right,
      targetPosition: Position.Left,
    }));

    // Simple layout: place nodes in columns based on topological distance from start
    const startNodes = graph.nodes.filter((n) => n.is_start).map((n) => n.id);
    const adjacency: Record<string, string[]> = {};
    for (const e of graph.edges) {
      if (!adjacency[e.source]) adjacency[e.source] = [];
      adjacency[e.source].push(e.target);
    }

    const depth: Record<string, number> = {};
    const queue = startNodes.map((id) => ({ id, d: 0 }));
    while (queue.length) {
      const { id, d } = queue.shift()!;
      if (depth[id] !== undefined && depth[id] <= d) continue;
      depth[id] = d;
      for (const next of adjacency[id] || []) {
        queue.push({ id: next, d: d + 1 });
      }
    }
    // Assign unvisited nodes
    for (const n of graph.nodes) {
      if (depth[n.id] === undefined) depth[n.id] = 0;
    }

    // Group by depth for column layout
    const byDepth: Record<number, string[]> = {};
    for (const [id, d] of Object.entries(depth)) {
      if (!byDepth[d]) byDepth[d] = [];
      byDepth[d].push(id);
    }

    const posMap: Record<string, { x: number; y: number }> = {};
    for (const [d, ids] of Object.entries(byDepth)) {
      const col = Number(d);
      ids.forEach((id, row) => {
        posMap[id] = { x: col * 240 + 40, y: row * 110 + 40 };
      });
    }

    nodes.forEach((n) => {
      if (posMap[n.id]) n.position = posMap[n.id];
    });

    // Filter edges by minimum transition frequency
    const filteredEdgesData = graph.edges.filter((e) => e.count >= minFrequency);
    const maxCount = Math.max(...graph.edges.map((e) => e.count), 1);
    const edges: Edge[] = filteredEdgesData.map((e) => ({
      id: `${e.source}-${e.target}`,
      source: e.source,
      target: e.target,
      label: e.count > 0 ? `${e.count.toLocaleString()}` : undefined,
      style: {
        strokeWidth: Math.max(1, (e.count / maxCount) * 4),
        stroke: "#94a3b8",
      },
      labelStyle: { fontSize: 9, fill: "#64748b" },
      markerEnd: { type: MarkerType.ArrowClosed, color: "#94a3b8" },
      animated: false,
    }));

    return { flowNodes: nodes, flowEdges: edges };
  }, [graph, minFrequency]);

  const [nodes, setNodes, onNodesChange] = useNodesState(flowNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(flowEdges);

  useEffect(() => {
    setNodes(flowNodes);
    setEdges(flowEdges);
  }, [flowNodes, flowEdges, setNodes, setEdges]);

  const selectedStats = selectedNode && graph?.activity_stats?.[selectedNode];
  const maxEdgeCount = graph?.edges?.length
    ? Math.max(...graph.edges.map((e) => e.count), 1)
    : 1;

  return (
    <DashboardShell>
      <div className="p-6 h-[calc(100vh-48px)] flex flex-col">
        <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
          <div>
            <h1 className="text-[18px] font-semibold text-slate-900">
              Process View
            </h1>
            <p className="text-[12px] text-slate-400 mt-0.5">
              {graph
                ? `${graph.metadata.total_activities} activities · ${flowEdges.length} of ${graph.metadata.total_transitions} transitions · ${graph.metadata.total_events.toLocaleString()} events`
                : "Workflow reconstruction"}
            </p>
          </div>

          <div className="flex items-center gap-3">
            {graph && graph.edges.length > 0 && (
              <div className="flex items-center gap-3 bg-white border border-slate-200 rounded px-3 py-1.5">
                <div className="flex flex-col">
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-[11px] font-medium text-slate-700">
                      Edge Filter (≥ {minFrequency.toLocaleString()})
                    </span>
                    <span className="text-[10px] text-slate-400 tabular-nums">
                      {flowEdges.length}/{graph.edges.length} edges
                    </span>
                  </div>
                  <input
                    type="range"
                    min={1}
                    max={maxEdgeCount}
                    value={minFrequency}
                    onChange={(e) => setMinFrequency(Number(e.target.value))}
                    className="w-40 h-1.5 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-slate-900 mt-1"
                  />
                </div>
                {minFrequency > 1 && (
                  <button
                    onClick={() => setMinFrequency(1)}
                    className="text-[11px] text-slate-500 hover:text-slate-900 underline"
                  >
                    Reset
                  </button>
                )}
              </div>
            )}

            <select
              value={selectedUpload ?? ""}
              onChange={(e) => setSelectedUpload(Number(e.target.value))}
              className="text-[12px] border border-slate-200 rounded px-2.5 py-1.5 bg-white"
            >
              {uploads.map((u) => (
                <option key={u.id} value={u.id}>{u.original_name}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="flex flex-1 gap-3 min-h-0">
          {/* Graph */}
          <div className="flex-1 bg-white border border-slate-200 rounded overflow-hidden">
            {loading ? (
              <div className="flex items-center justify-center h-full text-[13px] text-slate-400">
                Computing process graph...
              </div>
            ) : graph ? (
              <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onNodeClick={(_, node) => setSelectedNode(node.id)}
                fitView
                proOptions={{ hideAttribution: true }}
              >
                <Background color="#e2e8f0" gap={20} />
                <Controls />
              </ReactFlow>
            ) : (
              <div className="flex items-center justify-center h-full text-[13px] text-slate-400">
                Upload data and run process mining to see the graph.
              </div>
            )}
          </div>

          {/* Activity stats sidebar */}
          {selectedNode && selectedStats && (
            <div className="w-72 bg-white border border-slate-200 rounded p-4 overflow-y-auto">
              <h3 className="text-[13px] font-medium text-slate-800 mb-3">
                {selectedNode}
              </h3>
              <div className="space-y-2.5 text-[12px]">
                <Stat label="Occurrences" value={selectedStats.count.toLocaleString()} />
                {selectedStats.avg_duration_seconds != null && (
                  <Stat
                    label="Avg Duration"
                    value={formatDuration(selectedStats.avg_duration_seconds)}
                  />
                )}
                {selectedStats.median_duration_seconds != null && (
                  <Stat
                    label="Median Duration"
                    value={formatDuration(selectedStats.median_duration_seconds)}
                  />
                )}
                {selectedStats.first_occurrence && (
                  <Stat label="First Seen" value={new Date(selectedStats.first_occurrence).toLocaleDateString()} />
                )}
                {selectedStats.last_occurrence && (
                  <Stat label="Last Seen" value={new Date(selectedStats.last_occurrence).toLocaleDateString()} />
                )}
                {selectedStats.departments.length > 0 && (
                  <div>
                    <p className="text-[10px] uppercase text-slate-400 mb-1">Departments</p>
                    <div className="flex flex-wrap gap-1">
                      {selectedStats.departments.slice(0, 5).map((d) => (
                        <span key={d} className="px-1.5 py-0.5 bg-slate-50 border border-slate-200 rounded text-[10px] text-slate-600">
                          {d}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {selectedStats.resources.length > 0 && (
                  <div>
                    <p className="text-[10px] uppercase text-slate-400 mb-1">
                      Resources ({selectedStats.resources.length})
                    </p>
                    <p className="text-[11px] text-slate-500">
                      {selectedStats.resources.slice(0, 3).join(", ")}
                      {selectedStats.resources.length > 3 && ` +${selectedStats.resources.length - 3} more`}
                    </p>
                  </div>
                )}
              </div>
              <button
                onClick={() => setSelectedNode(null)}
                className="mt-4 text-[11px] text-slate-400 hover:text-slate-700"
              >
                Deselect
              </button>
            </div>
          )}
        </div>
      </div>
    </DashboardShell>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between">
      <span className="text-slate-400">{label}</span>
      <span className="font-medium text-slate-700">{value}</span>
    </div>
  );
}

function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds.toFixed(0)}s`;
  if (seconds < 3600) return `${(seconds / 60).toFixed(1)}m`;
  if (seconds < 86400) return `${(seconds / 3600).toFixed(1)}h`;
  return `${(seconds / 86400).toFixed(1)}d`;
}
