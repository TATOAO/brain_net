'use client';

import React, { useState } from 'react';
import GraphComponent from '../components/GraphComponent';

// Mock data structure to match the provided example
interface Node {
  processor_class_name: string;
  processor_unique_name: string;
}

interface Edge {
  source_node_unique_name: string;
  target_node_unique_name: string;
  edge_unique_name: string;
}

interface GraphData {
  nodes: Node[];
  edges: Edge[];
  processor_id: string;
}

export default function GraphPage() {
  // Initial graph data matching the provided example
  const [graphData, setGraphData] = useState<GraphData>({
    nodes: [
      {
        processor_class_name: "ChunkerProcessor",
        processor_unique_name: "chunker_processor_1"
      },
      {
        processor_class_name: "HasherProcessor",
        processor_unique_name: "hasher_processor_1"
      }
    ],
    edges: [
      {
        source_node_unique_name: "chunker_processor_1",
        target_node_unique_name: "hasher_processor_1",
        edge_unique_name: "edge_1"
      }
    ],
    processor_id: "graph_1"
  });

  const handleGraphChange = (newGraphData: GraphData) => {
    setGraphData(newGraphData);
    console.log('Graph updated:', newGraphData);
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Graph Editor</h1>
          <p className="text-gray-600">
            Interactive graph editor with processor nodes and connections
          </p>
        </div>

        <div className="bg-white rounded-lg shadow-lg p-6">
          <div className="mb-4">
            <h2 className="text-xl font-semibold text-gray-800 mb-2">
              Graph: {graphData.processor_id}
            </h2>
            <div className="text-sm text-gray-600">
              <p>Nodes: {graphData.nodes.length} | Edges: {graphData.edges.length}</p>
            </div>
          </div>

          <GraphComponent 
            graphData={graphData} 
            onGraphChange={handleGraphChange}
          />

          <div className="mt-6 p-4 bg-gray-50 rounded-lg">
            <h3 className="text-lg font-semibold text-gray-800 mb-3">Graph Data</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h4 className="font-medium text-gray-700 mb-2">Nodes:</h4>
                <ul className="space-y-1">
                  {graphData.nodes.map((node, index) => (
                    <li key={index} className="text-sm text-gray-600">
                      • {node.processor_class_name} ({node.processor_unique_name})
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <h4 className="font-medium text-gray-700 mb-2">Edges:</h4>
                <ul className="space-y-1">
                  {graphData.edges.map((edge, index) => (
                    <li key={index} className="text-sm text-gray-600">
                      • {edge.source_node_unique_name} → {edge.target_node_unique_name}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
