import React, { useState, useEffect } from "react";
import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet';
import axios from "axios";
import "leaflet/dist/leaflet.css";
import L from 'leaflet';
import "./App.css";

// Fix for default markers in react-leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [nodes, setNodes] = useState([]);
  const [selectedStart, setSelectedStart] = useState('');
  const [selectedEnd, setSelectedEnd] = useState('');
  const [routeResult, setRouteResult] = useState(null);
  const [optimizationHistory, setOptimizationHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showAddNode, setShowAddNode] = useState(false);
  const [newNode, setNewNode] = useState({ name: '', lat: '', lng: '' });
  const [mapCenter] = useState([40.7128, -74.0060]); // NYC center

  useEffect(() => {
    fetchNodes();
    fetchOptimizationHistory();
  }, []);

  const fetchNodes = async () => {
    try {
      const response = await axios.get(`${API}/nodes`);
      setNodes(response.data);
    } catch (error) {
      console.error('Error fetching nodes:', error);
    }
  };

  const fetchOptimizationHistory = async () => {
    try {
      const response = await axios.get(`${API}/route/results`);
      setOptimizationHistory(response.data.slice(-10)); // Last 10 results
    } catch (error) {
      console.error('Error fetching optimization history:', error);
    }
  };

  const createSampleNodes = async () => {
    try {
      setLoading(true);
      await axios.post(`${API}/demo/create-sample-nodes`);
      await fetchNodes();
      alert('Sample nodes created successfully!');
    } catch (error) {
      console.error('Error creating sample nodes:', error);
      alert('Error creating sample nodes');
    } finally {
      setLoading(false);
    }
  };

  const addNode = async () => {
    if (!newNode.name || !newNode.lat || !newNode.lng) {
      alert('Please fill all fields');
      return;
    }

    try {
      await axios.post(`${API}/nodes`, {
        name: newNode.name,
        lat: parseFloat(newNode.lat),
        lng: parseFloat(newNode.lng)
      });
      await fetchNodes();
      setNewNode({ name: '', lat: '', lng: '' });
      setShowAddNode(false);
    } catch (error) {
      console.error('Error adding node:', error);
      alert('Error adding node');
    }
  };

  const optimizeRoute = async (algorithm) => {
    if (!selectedStart || !selectedEnd) {
      alert('Please select both start and end points');
      return;
    }

    try {
      setLoading(true);
      const response = await axios.post(`${API}/route/optimize`, {
        start_node_id: selectedStart,
        end_node_id: selectedEnd,
        algorithm: algorithm
      });
      
      setRouteResult(response.data);
      await fetchOptimizationHistory();
    } catch (error) {
      console.error('Error optimizing route:', error);
      alert('Error optimizing route');
    } finally {
      setLoading(false);
    }
  };

  const getRouteCoordinates = () => {
    if (!routeResult || !routeResult.path) return [];
    
    return routeResult.path.map(nodeId => {
      const node = nodes.find(n => n.id === nodeId);
      return node ? [node.lat, node.lng] : null;
    }).filter(coord => coord !== null);
  };

  const getNodeName = (nodeId) => {
    const node = nodes.find(n => n.id === nodeId);
    return node ? node.name : nodeId;
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <div className="bg-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold text-gray-900">
            🔬 Quantum Route Optimization
          </h1>
          <p className="text-gray-600 mt-2">
            Compare Dijkstra's Algorithm vs QAOA (Quantum Approximate Optimization Algorithm)
          </p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Control Panel */}
          <div className="lg:col-span-1 space-y-6">
            
            {/* Node Management */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold mb-4">📍 Delivery Points</h2>
              
              <div className="space-y-4">
                <button
                  onClick={createSampleNodes}
                  disabled={loading}
                  className="w-full bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded transition-colors disabled:opacity-50"
                >
                  {loading ? '⏳ Loading...' : '🎯 Create Sample Nodes (10)'}
                </button>

                <button
                  onClick={() => setShowAddNode(!showAddNode)}
                  className="w-full bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded transition-colors"
                >
                  ➕ Add Custom Node
                </button>

                {showAddNode && (
                  <div className="space-y-2 border-t pt-4">
                    <input
                      type="text"
                      placeholder="Node name"
                      value={newNode.name}
                      onChange={(e) => setNewNode({...newNode, name: e.target.value})}
                      className="w-full border rounded px-3 py-2"
                    />
                    <input
                      type="number"
                      step="any"
                      placeholder="Latitude"
                      value={newNode.lat}
                      onChange={(e) => setNewNode({...newNode, lat: e.target.value})}
                      className="w-full border rounded px-3 py-2"
                    />
                    <input
                      type="number"
                      step="any"
                      placeholder="Longitude"
                      value={newNode.lng}
                      onChange={(e) => setNewNode({...newNode, lng: e.target.value})}
                      className="w-full border rounded px-3 py-2"
                    />
                    <button
                      onClick={addNode}
                      className="w-full bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded"
                    >
                      Add Node
                    </button>
                  </div>
                )}
              </div>

              <div className="mt-4">
                <p className="text-sm text-gray-600 mb-2">Active Nodes: {nodes.length}</p>
                <div className="max-h-32 overflow-y-auto space-y-1">
                  {nodes.map(node => (
                    <div key={node.id} className="text-xs bg-gray-100 p-2 rounded">
                      <strong>{node.name}</strong><br/>
                      {node.lat.toFixed(4)}, {node.lng.toFixed(4)}
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Route Selection */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold mb-4">🛣️ Route Planning</h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Start Point</label>
                  <select
                    value={selectedStart}
                    onChange={(e) => setSelectedStart(e.target.value)}
                    className="w-full border rounded px-3 py-2"
                  >
                    <option value="">Select start point</option>
                    {nodes.map(node => (
                      <option key={node.id} value={node.id}>{node.name}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">End Point</label>
                  <select
                    value={selectedEnd}
                    onChange={(e) => setSelectedEnd(e.target.value)}
                    className="w-full border rounded px-3 py-2"
                  >
                    <option value="">Select end point</option>
                    {nodes.map(node => (
                      <option key={node.id} value={node.id}>{node.name}</option>
                    ))}
                  </select>
                </div>

                <div className="space-y-2">
                  <button
                    onClick={() => optimizeRoute('dijkstra')}
                    disabled={loading || !selectedStart || !selectedEnd}
                    className="w-full bg-purple-500 hover:bg-purple-600 text-white px-4 py-2 rounded transition-colors disabled:opacity-50"
                  >
                    🚀 Classical (Dijkstra)
                  </button>

                  <button
                    onClick={() => optimizeRoute('qaoa')}
                    disabled={loading || !selectedStart || !selectedEnd}
                    className="w-full bg-indigo-500 hover:bg-indigo-600 text-white px-4 py-2 rounded transition-colors disabled:opacity-50"
                  >
                    ⚛️ Quantum (QAOA)
                  </button>
                </div>
              </div>
            </div>

            {/* Results */}
            {routeResult && (
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-xl font-semibold mb-4">📊 Latest Result</h2>
                
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="font-medium">Algorithm:</span>
                    <span className={`px-2 py-1 rounded ${
                      routeResult.algorithm === 'dijkstra' 
                        ? 'bg-purple-100 text-purple-800'
                        : 'bg-indigo-100 text-indigo-800'
                    }`}>
                      {routeResult.algorithm.toUpperCase()}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="font-medium">Distance:</span>
                    <span>{routeResult.distance.toFixed(2)} km</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="font-medium">Execution Time:</span>
                    <span>{(routeResult.execution_time * 1000).toFixed(2)} ms</span>
                  </div>
                  <div className="mt-3">
                    <span className="font-medium">Path:</span>
                    <div className="mt-1 text-xs bg-gray-100 p-2 rounded">
                      {routeResult.path.map((nodeId, idx) => (
                        <span key={idx}>
                          {getNodeName(nodeId)}
                          {idx < routeResult.path.length - 1 && ' → '}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Map */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <div className="p-4 bg-gray-50 border-b">
                <h2 className="text-xl font-semibold">🗺️ Interactive Route Map</h2>
                <p className="text-sm text-gray-600 mt-1">
                  {routeResult 
                    ? `Showing ${routeResult.algorithm.toUpperCase()} route: ${routeResult.distance.toFixed(2)} km`
                    : 'Select start and end points, then choose an algorithm to see the optimized route'
                  }
                </p>
              </div>
              
              <div style={{ height: '600px' }}>
                <MapContainer 
                  center={mapCenter} 
                  zoom={11} 
                  style={{ height: '100%', width: '100%' }}
                >
                  <TileLayer
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                  />
                  
                  {/* Render nodes as markers */}
                  {nodes.map((node) => (
                    <Marker 
                      key={node.id} 
                      position={[node.lat, node.lng]}
                    >
                      <Popup>
                        <div>
                          <strong>{node.name}</strong><br/>
                          Lat: {node.lat}<br/>
                          Lng: {node.lng}<br/>
                          <div className="mt-2 space-x-2">
                            <button
                              onClick={() => setSelectedStart(node.id)}
                              className="text-xs bg-green-500 text-white px-2 py-1 rounded"
                            >
                              Set as Start
                            </button>
                            <button
                              onClick={() => setSelectedEnd(node.id)}
                              className="text-xs bg-red-500 text-white px-2 py-1 rounded"
                            >
                              Set as End
                            </button>
                          </div>
                        </div>
                      </Popup>
                    </Marker>
                  ))}

                  {/* Render route if available */}
                  {routeResult && getRouteCoordinates().length > 1 && (
                    <Polyline 
                      positions={getRouteCoordinates()}
                      pathOptions={{
                        color: routeResult.algorithm === 'dijkstra' ? '#7c3aed' : '#4f46e5',
                        weight: 4,
                        opacity: 0.8
                      }}
                    />
                  )}
                </MapContainer>
              </div>
            </div>

            {/* Optimization History */}
            {optimizationHistory.length > 0 && (
              <div className="bg-white rounded-lg shadow p-6 mt-6">
                <h2 className="text-xl font-semibold mb-4">📈 Optimization History</h2>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left py-2">Algorithm</th>
                        <th className="text-left py-2">Route</th>
                        <th className="text-left py-2">Distance</th>
                        <th className="text-left py-2">Time (ms)</th>
                      </tr>
                    </thead>
                    <tbody>
                      {optimizationHistory.map((result, idx) => (
                        <tr key={idx} className="border-b">
                          <td className="py-2">
                            <span className={`px-2 py-1 rounded text-xs ${
                              result.algorithm === 'dijkstra'
                                ? 'bg-purple-100 text-purple-800'
                                : 'bg-indigo-100 text-indigo-800'
                            }`}>
                              {result.algorithm.toUpperCase()}
                            </span>
                          </td>
                          <td className="py-2 max-w-xs">
                            <div className="text-xs">
                              {getNodeName(result.start_node_id)} → {getNodeName(result.end_node_id)}
                            </div>
                          </td>
                          <td className="py-2">{result.distance.toFixed(2)} km</td>
                          <td className="py-2">{(result.execution_time * 1000).toFixed(2)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;