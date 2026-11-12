"use client";

import React, { useEffect, useRef, useState, useMemo } from "react";
import cytoscape, { Core, EventObject } from "cytoscape";
import {
  GraphNode,
  GraphEdge,
  BlockchainNetwork,
  NodeType,
  EdgeRelationshipType,
} from "@/types/investigation";
import { formatAddress, formatCurrency, cn } from "@/lib/utils";
import {
  ZoomIn,
  ZoomOut,
  Maximize2,
  RotateCcw,
  Search,
  Filter,
  SlidersHorizontal,
  Info,
  Layers,
  Download,
  Minimize2,
} from "lucide-react";

type GraphLayoutMode = "breadthfirst" | "cose" | "circle" | "concentric";

interface CytoscapeGraphProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  onSelectNode?: (node: GraphNode | null) => void;
  onSelectEdge?: (edge: GraphEdge | null) => void;
  selectedNodeId?: string | null;
  className?: string;
}

export function CytoscapeGraph({
  nodes,
  edges,
  onSelectNode,
  onSelectEdge,
  selectedNodeId,
  className,
}: CytoscapeGraphProps) {
  const wrapperRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<Core | null>(null);
  const [layoutMode, setLayoutMode] = useState<GraphLayoutMode>("breadthfirst");
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Graph interaction state
  const [searchTerm, setSearchTerm] = useState("");
  const [maxHopFilter, setMaxHopFilter] = useState<number>(5);
  const [minAmountFilter, setMinAmountFilter] = useState<number>(0);
  const [selectedRelationshipTypes, setSelectedRelationshipTypes] = useState<
    Record<EdgeRelationshipType, boolean>
  >({
    confirmed_transfer: true,
    utxo_spending: true,
    token_transfer: true,
    bridge_correlated: true,
    heuristic_link: true,
  });
  const [isFilterOpen, setIsFilterOpen] = useState(false);

  // Filter elements
  const filteredNodes = useMemo(() => {
    return nodes.filter((n) => {
      if (n.hop > maxHopFilter) return false;
      if (searchTerm) {
        const term = searchTerm.toLowerCase();
        const matchesAddress = n.address?.toLowerCase().includes(term);
        const matchesLabel = n.label.toLowerCase().includes(term);
        const matchesEntity = n.entityName?.toLowerCase().includes(term);
        if (!matchesAddress && !matchesLabel && !matchesEntity) return false;
      }
      return true;
    });
  }, [nodes, maxHopFilter, searchTerm]);

  const filteredNodeIds = useMemo(
    () => new Set(filteredNodes.map((n) => n.id)),
    [filteredNodes]
  );

  const filteredEdges = useMemo(() => {
    return edges.filter((e) => {
      if (!filteredNodeIds.has(e.source) || !filteredNodeIds.has(e.target)) return false;
      if (!selectedRelationshipTypes[e.relationshipType]) return false;
      if (e.amount < minAmountFilter) return false;
      return true;
    });
  }, [edges, filteredNodeIds, selectedRelationshipTypes, minAmountFilter]);

  // Convert to Cytoscape format
  const elements = useMemo(() => {
    const nodeElements = filteredNodes.map((node) => {
      let nodeShape = "ellipse";
      let nodeColor = "#1e293b";
      let borderColor = "#3b82f6";

      if (node.isInputTarget) {
        nodeShape = "hexagon";
        borderColor = "#f59e0b"; // Gold amber for case target
        nodeColor = "#2d2006";
      } else if (node.type === "mixer") {
        nodeShape = "star";
        borderColor = "#ef4444";
        nodeColor = "#3d0a0a";
      } else if (node.type === "bridge") {
        nodeShape = "round-diamond";
        borderColor = "#8b5cf6";
        nodeColor = "#26103d";
      } else if (node.type === "contract" || node.type === "exchange") {
        nodeShape = "round-rectangle";
        borderColor = "#06b6d4";
        nodeColor = "#06222b";
      } else if (node.riskScore >= 90) {
        borderColor = "#ef4444";
      }

      return {
        data: {
          id: node.id,
          label: node.isInputTarget
            ? `[TARGET]\n${formatAddress(node.address || node.id)}`
            : `${node.entityName ? node.entityName.substring(0, 18) : formatAddress(node.address || node.id)}`,
          original: node,
          shape: nodeShape,
          backgroundColor: nodeColor,
          borderColor: borderColor,
          riskScore: node.riskScore,
        },
      };
    });

    const edgeElements = filteredEdges.map((edge) => {
      let lineColor = "#3b82f6";
      let lineStyle = "solid";
      let targetArrowShape = "triangle";

      if (edge.relationshipType === "utxo_spending") {
        lineColor = "#f59e0b";
        targetArrowShape = "vee";
      } else if (edge.relationshipType === "token_transfer") {
        lineColor = "#06b6d4";
        lineStyle = "dashed";
      } else if (edge.relationshipType === "bridge_correlated") {
        lineColor = "#8b5cf6";
        lineStyle = "dotted";
        targetArrowShape = "chevron";
      } else if (edge.relationshipType === "heuristic_link") {
        lineColor = "#ef4444";
        lineStyle = "dashed";
      }

      return {
        data: {
          id: edge.id,
          source: edge.source,
          target: edge.target,
          label: `${edge.amount.toLocaleString()} ${edge.currency}`,
          original: edge,
          lineColor,
          lineStyle,
          targetArrowShape,
        },
      };
    });

    return [...nodeElements, ...edgeElements];
  }, [filteredNodes, filteredEdges]);

  // Initialize and update Cytoscape instance
  useEffect(() => {
    if (!containerRef.current) return;

    if (!cyRef.current) {
      const cy = cytoscape({
        container: containerRef.current,
        elements: elements,
        boxSelectionEnabled: false,
        autounselectify: false,
        style: [
          {
            selector: "node",
            style: {
              "background-color": "data(backgroundColor)",
              label: "data(label)",
              color: "#f1f5f9",
              "font-size": "11px",
              "font-family": "ui-monospace, monospace",
              "text-valign": "bottom",
              "text-margin-y": 6,
              "text-wrap": "wrap",
              "border-width": 2,
              "border-color": "data(borderColor)",
              width: 44,
              height: 44,
              shape: "data(shape)" as any,
              "transition-property": "background-color, border-color, width, height",
              "transition-duration": 0.2,
            },
          },
          {
            selector: "node:selected",
            style: {
              "border-width": 4,
              "border-color": "#ffffff",
              width: 52,
              height: 52,
              "underlay-color": "#3b82f6",
              "underlay-padding": "6px",
              "underlay-opacity": 0.4,
            } as any,
          },
          {
            selector: "edge",
            style: {
              width: 2.5,
              "line-color": "data(lineColor)",
              "target-arrow-color": "data(lineColor)",
              "target-arrow-shape": "data(targetArrowShape)" as any,
              "curve-style": "bezier",
              "line-style": "data(lineStyle)" as any,
              label: "data(label)",
              "font-size": "9.5px",
              "font-family": "ui-monospace, monospace",
              color: "#94a3b8",
              "text-background-opacity": 0.85,
              "text-background-color": "#080c14",
              "text-background-padding": "2px",
              "text-rotation": "autorotate",
              "arrow-scale": 1.2,
            },
          },
          {
            selector: "edge:selected",
            style: {
              width: 4,
              "line-color": "#ffffff",
              "target-arrow-color": "#ffffff",
              color: "#ffffff",
            },
          },
        ],
        layout: {
          name: "breadthfirst",
          directed: true,
          padding: 50,
          spacingFactor: 1.6,
        },
      });

      cy.on("tap", "node", (evt: EventObject) => {
        const node = evt.target;
        const rawData = node.data("original") as GraphNode;
        if (onSelectNode) onSelectNode(rawData);
      });

      cy.on("tap", "edge", (evt: EventObject) => {
        const edge = evt.target;
        const rawData = edge.data("original") as GraphEdge;
        if (onSelectEdge) onSelectEdge(rawData);
      });

      cy.on("tap", (evt: EventObject) => {
        if (evt.target === cy) {
          if (onSelectNode) onSelectNode(null);
          if (onSelectEdge) onSelectEdge(null);
        }
      });

      cyRef.current = cy;
    } else {
      const cy = cyRef.current;
      cy.json({ elements });
      cy.layout({
        name: "breadthfirst",
        directed: true,
        padding: 50,
        spacingFactor: 1.6,
      }).run();
    }

    return () => {
      // Keep instance across hot renders or cleanup
    };
  }, [elements, onSelectNode, onSelectEdge]);

  // Highlight selected node
  useEffect(() => {
    if (!cyRef.current) return;
    const cy = cyRef.current;
    if (selectedNodeId) {
      cy.nodes().unselect();
      const target = cy.getElementById(selectedNodeId);
      if (target.length) {
        target.select();
      }
    }
  }, [selectedNodeId]);

  // Layout Controls
  const runLayout = (name: GraphLayoutMode) => {
    const cy = cyRef.current;
    if (!cy) return;
    if (name === "breadthfirst") {
      cy.layout({
        name: "breadthfirst",
        directed: true,
        padding: 50,
        spacingFactor: 1.6,
      }).run();
    } else {
      cy.layout({
        name,
        padding: 50,
        animate: true,
      }).run();
    }
  };

  const handleLayoutChange = (name: GraphLayoutMode) => {
    setLayoutMode(name);
    runLayout(name);
  };

  const handleExportPng = () => {
    const cy = cyRef.current;
    if (!cy) return;
    const pngDataUrl = cy.png({ full: true, bg: "#07090C", scale: 2 });
    const link = document.createElement("a");
    link.href = pngDataUrl;
    link.download = `cryptotrace-graph-${Date.now()}.png`;
    link.click();
  };

  const handleToggleFullscreen = () => {
    if (!wrapperRef.current) return;
    if (!document.fullscreenElement) {
      wrapperRef.current.requestFullscreen?.().then(() => setIsFullscreen(true)).catch(() => {});
    } else {
      document.exitFullscreen?.().then(() => setIsFullscreen(false)).catch(() => {});
    }
  };

  const handleZoomIn = () => cyRef.current?.zoom(cyRef.current.zoom() * 1.25);
  const handleZoomOut = () => cyRef.current?.zoom(cyRef.current.zoom() * 0.8);
  const handleFit = () => cyRef.current?.fit(undefined, 40);
  const handleResetLayout = () => runLayout(layoutMode);

  return (
    <div ref={wrapperRef} className={cn("relative w-full h-[600px] bg-[#07090C] border border-white/[0.08] rounded overflow-hidden flex flex-col", className)}>
      {/* Top Graph Toolbar */}
      <div className="absolute top-3 left-3 right-3 z-10 flex items-center justify-between gap-3 pointer-events-none">
        {/* Search Bar */}
        <div className="flex items-center gap-2 bg-cyber-surface/90 backdrop-blur-md border border-cyber-border rounded px-3 py-1.5 pointer-events-auto shadow-lg">
          <Search className="w-3.5 h-3.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search wallet, label, tx..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="bg-transparent text-xs text-slate-200 placeholder-slate-500 focus:outline-none w-48 font-mono"
          />
          {searchTerm && (
            <button
              onClick={() => setSearchTerm("")}
              className="text-xs text-slate-400 hover:text-slate-200 font-mono"
            >
              ×
            </button>
          )}
        </div>

        {/* Legend & Filter Trigger */}
        <div className="flex items-center gap-2 pointer-events-auto">
          <button
            onClick={() => setIsFilterOpen(!isFilterOpen)}
            className={cn(
              "flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono rounded border transition-colors shadow-lg",
              isFilterOpen
                ? "bg-cyber-primary text-white border-blue-400"
                : "bg-cyber-surface/90 backdrop-blur-md text-slate-300 border-cyber-border hover:border-slate-500"
            )}
          >
            <Filter className="w-3.5 h-3.5" />
            <span>GRAPH FILTERS</span>
          </button>
        </div>
      </div>

      {/* Floating Filter Drawer / Popover */}
      {isFilterOpen && (
        <div className="absolute top-14 right-3 z-20 w-80 bg-cyber-surface/95 backdrop-blur-lg border border-cyber-border rounded-lg p-4 shadow-2xl text-xs flex flex-col gap-3 font-mono">
          <div className="flex items-center justify-between border-b border-cyber-border pb-2 text-slate-200 font-semibold">
            <span className="flex items-center gap-1.5">
              <SlidersHorizontal className="w-3.5 h-3.5 text-cyber-primary" />
              FORENSIC GRAPH FILTERS
            </span>
            <button
              onClick={() => setIsFilterOpen(false)}
              className="text-slate-400 hover:text-slate-200"
            >
              ×
            </button>
          </div>

          {/* Hop Depth */}
          <div>
            <div className="flex justify-between text-slate-400 mb-1">
              <span>MAX HOP DEPTH:</span>
              <span className="text-cyber-primary font-bold">{maxHopFilter} HOPS</span>
            </div>
            <input
              type="range"
              min="1"
              max="5"
              value={maxHopFilter}
              onChange={(e) => setMaxHopFilter(Number(e.target.value))}
              className="w-full accent-cyber-primary cursor-pointer"
            />
          </div>

          {/* Min Amount Filter */}
          <div>
            <div className="flex justify-between text-slate-400 mb-1">
              <span>MIN TRANSFER VALUE:</span>
              <span className="text-cyber-primary font-bold">{minAmountFilter}</span>
            </div>
            <input
              type="range"
              min="0"
              max="2000"
              step="50"
              value={minAmountFilter}
              onChange={(e) => setMinAmountFilter(Number(e.target.value))}
              className="w-full accent-cyber-primary cursor-pointer"
            />
          </div>

          {/* Edge Relationship Types */}
          <div className="flex flex-col gap-1.5 pt-1 border-t border-cyber-border/60">
            <span className="text-slate-400 mb-1">RELATIONSHIP LAYERS:</span>
            {(
              [
                ["confirmed_transfer", "Confirmed On-Chain", "border-blue-500 text-blue-400"],
                ["utxo_spending", "UTXO Spending Flow", "border-amber-500 text-amber-400"],
                ["token_transfer", "Token Transfer (ERC-20)", "border-cyan-500 text-cyan-400"],
                ["bridge_correlated", "Cross-Chain Bridge", "border-violet-500 text-violet-400"],
                ["heuristic_link", "Heuristic / Peel Chain", "border-red-500 text-red-400"],
              ] as const
            ).map(([key, label, colorCls]) => (
              <label
                key={key}
                className="flex items-center justify-between gap-2 cursor-pointer hover:text-slate-200 text-slate-300"
              >
                <div className="flex items-center gap-2">
                  <span className={cn("w-2 h-2 rounded-full border", colorCls)} />
                  <span>{label}</span>
                </div>
                <input
                  type="checkbox"
                  checked={selectedRelationshipTypes[key]}
                  onChange={(e) =>
                    setSelectedRelationshipTypes((prev) => ({
                      ...prev,
                      [key]: e.target.checked,
                    }))
                  }
                  className="accent-cyber-primary"
                />
              </label>
            ))}
          </div>
        </div>
      )}

      {/* Floating Canvas Controls (Zoom/Pan/Reset/Layout/Export) */}
      <div className="absolute bottom-4 left-4 z-10 flex items-center gap-1.5 bg-[#0E1217]/95 backdrop-blur-md border border-white/[0.1] rounded p-1 shadow-lg pointer-events-auto">
        <button
          onClick={handleZoomIn}
          title="Zoom In"
          className="p-1.5 text-slate-400 hover:text-slate-100 hover:bg-slate-800 rounded transition-colors"
        >
          <ZoomIn className="w-4 h-4" />
        </button>
        <button
          onClick={handleZoomOut}
          title="Zoom Out"
          className="p-1.5 text-slate-400 hover:text-slate-100 hover:bg-slate-800 rounded transition-colors"
        >
          <ZoomOut className="w-4 h-4" />
        </button>
        <button
          onClick={handleFit}
          title="Fit View"
          className="p-1.5 text-slate-400 hover:text-slate-100 hover:bg-slate-800 rounded transition-colors"
        >
          <Maximize2 className="w-4 h-4" />
        </button>
        <button
          onClick={handleResetLayout}
          title="Reset Layout"
          className="p-1.5 text-slate-400 hover:text-slate-100 hover:bg-slate-800 rounded transition-colors"
        >
          <RotateCcw className="w-4 h-4" />
        </button>
        <select
          value={layoutMode}
          onChange={(e) => handleLayoutChange(e.target.value as GraphLayoutMode)}
          title="Graph Layout"
          aria-label="Graph Layout"
          className="h-7 px-2 rounded bg-[#07090C] border border-white/[0.08] text-[11px] font-mono text-[#F5F7FA]"
        >
          <option value="breadthfirst">Hierarchical</option>
          <option value="cose">Force (COSE)</option>
          <option value="circle">Circular</option>
          <option value="concentric">Concentric</option>
        </select>
        <button
          onClick={handleExportPng}
          title="Export Graph PNG"
          className="p-1.5 text-[#00E5FF] hover:bg-[#00E5FF]/15 rounded transition-colors"
        >
          <Download className="w-4 h-4" />
        </button>
        <button
          onClick={handleToggleFullscreen}
          title="Toggle Fullscreen"
          className="p-1.5 text-slate-400 hover:text-slate-100 hover:bg-slate-800 rounded transition-colors"
        >
          <Minimize2 className="w-4 h-4" />
        </button>
      </div>

      {/* Bottom Graph Stats Indicator */}
      <div className="absolute bottom-4 right-4 z-10 flex items-center gap-3 bg-cyber-surface/90 backdrop-blur-md border border-cyber-border rounded px-3 py-1 text-[11px] font-mono text-slate-400 pointer-events-auto shadow-lg">
        <span className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />
          <span>NODES: {filteredNodes.length}</span>
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
          <span>EDGES: {filteredEdges.length}</span>
        </span>
      </div>

      {/* Graph Canvas Container */}
      <div ref={containerRef} className="w-full h-full relative" />
    </div>
  );
}
