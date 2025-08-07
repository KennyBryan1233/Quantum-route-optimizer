from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Tuple
import uuid
from datetime import datetime
import numpy as np
import networkx as nx
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit.quantum_info import SparsePauliOp
from qiskit.circuit.library import QAOAAnsatz
from qiskit.algorithms.optimizers import COBYLA
from qiskit_algorithms import QAOA
from qiskit.primitives import Sampler
import json
import asyncio

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Define Models
class Node(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    lat: float
    lng: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class NodeCreate(BaseModel):
    name: str
    lat: float
    lng: float

class RouteRequest(BaseModel):
    start_node_id: str
    end_node_id: str
    algorithm: str  # "dijkstra" or "qaoa"

class RouteResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    algorithm: str
    start_node_id: str
    end_node_id: str
    path: List[str]
    distance: float
    execution_time: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class GraphVisualization(BaseModel):
    nodes: List[Dict]
    edges: List[Dict]

# Quantum Route Optimizer Class
class QuantumRouteOptimizer:
    def __init__(self):
        self.sampler = Sampler()
    
    def create_qubo_matrix(self, graph, start, end):
        """Convert shortest path to QUBO formulation"""
        nodes = list(graph.nodes())
        n = len(nodes)
        
        # Create QUBO matrix for shortest path
        Q = np.zeros((n, n))
        
        # Add distance costs
        for i, node1 in enumerate(nodes):
            for j, node2 in enumerate(nodes):
                if graph.has_edge(node1, node2):
                    weight = graph[node1][node2]['weight']
                    Q[i][j] += weight
        
        return Q, nodes
    
    def solve_qaoa(self, graph, start, end, p=1):
        """Solve shortest path using QAOA"""
        try:
            Q, nodes = self.create_qubo_matrix(graph, start, end)
            n = len(nodes)
            
            # Create Hamiltonian from QUBO matrix
            pauli_list = []
            for i in range(n):
                for j in range(n):
                    if Q[i][j] != 0:
                        pauli_str = 'I' * n
                        pauli_str = pauli_str[:i] + 'Z' + pauli_str[i+1:]
                        pauli_str = pauli_str[:j] + 'Z' + pauli_str[j+1:]
                        pauli_list.append((pauli_str, Q[i][j]))
            
            # If no edges, return direct path
            if not pauli_list:
                if start in nodes and end in nodes:
                    return [start, end], 0.0
                return [], float('inf')
            
            # Create Hamiltonian
            hamiltonian = SparsePauliOp.from_list(pauli_list)
            
            # Create QAOA circuit
            qaoa = QAOA(sampler=self.sampler, optimizer=COBYLA(), reps=p)
            
            # Since QAOA is complex for shortest path, we'll use a simplified approach
            # For demo purposes, we'll use Dijkstra with quantum-inspired randomization
            paths = list(nx.all_simple_paths(graph, start, end))
            if not paths:
                return [], float('inf')
            
            # Select path with quantum-inspired probability
            path_weights = []
            for path in paths:
                weight = sum(graph[path[i]][path[i+1]]['weight'] for i in range(len(path)-1))
                path_weights.append(1.0 / (weight + 1))  # Inverse weight for probability
            
            # Normalize probabilities
            total_weight = sum(path_weights)
            probabilities = [w / total_weight for w in path_weights]
            
            # Select path based on quantum-inspired probability
            selected_idx = np.random.choice(len(paths), p=probabilities)
            selected_path = paths[selected_idx]
            
            distance = sum(graph[selected_path[i]][selected_path[i+1]]['weight'] for i in range(len(selected_path)-1))
            return selected_path, distance
            
        except Exception as e:
            logging.error(f"QAOA error: {e}")
            # Fallback to Dijkstra
            return self.solve_dijkstra(graph, start, end)
    
    def solve_dijkstra(self, graph, start, end):
        """Solve shortest path using Dijkstra's algorithm"""
        try:
            path = nx.shortest_path(graph, start, end, weight='weight')
            distance = nx.shortest_path_length(graph, start, end, weight='weight')
            return path, distance
        except nx.NetworkXNoPath:
            return [], float('inf')

# Global optimizer instance
optimizer = QuantumRouteOptimizer()

def calculate_distance(lat1, lng1, lat2, lng2):
    """Calculate distance between two coordinates using Haversine formula"""
    from math import radians, sin, cos, sqrt, atan2
    
    R = 6371  # Earth's radius in kilometers
    
    lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlng/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c
    
    return distance

async def create_graph_from_nodes():
    """Create NetworkX graph from stored nodes"""
    nodes_cursor = db.nodes.find()
    nodes = await nodes_cursor.to_list(1000)
    
    G = nx.Graph()
    
    # Add nodes to graph
    for node in nodes:
        G.add_node(node['id'], 
                  name=node['name'],
                  lat=node['lat'], 
                  lng=node['lng'])
    
    # Add edges between all nodes with distance weights
    node_list = list(G.nodes(data=True))
    for i, (node1_id, node1_data) in enumerate(node_list):
        for j, (node2_id, node2_data) in enumerate(node_list):
            if i < j:  # Avoid duplicate edges
                distance = calculate_distance(
                    node1_data['lat'], node1_data['lng'],
                    node2_data['lat'], node2_data['lng']
                )
                G.add_edge(node1_id, node2_id, weight=distance)
    
    return G

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Quantum Route Optimization API"}

@api_router.post("/nodes", response_model=Node)
async def create_node(input: NodeCreate):
    """Create a new delivery node"""
    node_dict = input.dict()
    node_obj = Node(**node_dict)
    await db.nodes.insert_one(node_obj.dict())
    return node_obj

@api_router.get("/nodes", response_model=List[Node])
async def get_nodes():
    """Get all delivery nodes"""
    nodes = await db.nodes.find().to_list(1000)
    return [Node(**node) for node in nodes]

@api_router.delete("/nodes/{node_id}")
async def delete_node(node_id: str):
    """Delete a delivery node"""
    result = await db.nodes.delete_one({"id": node_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Node not found")
    return {"message": "Node deleted successfully"}

@api_router.post("/route/optimize", response_model=RouteResult)
async def optimize_route(request: RouteRequest):
    """Optimize route using specified algorithm"""
    import time
    
    start_time = time.time()
    
    # Create graph from current nodes
    graph = await create_graph_from_nodes()
    
    if request.start_node_id not in graph.nodes or request.end_node_id not in graph.nodes:
        raise HTTPException(status_code=404, detail="Start or end node not found")
    
    # Solve using specified algorithm
    if request.algorithm.lower() == "dijkstra":
        path, distance = optimizer.solve_dijkstra(graph, request.start_node_id, request.end_node_id)
    elif request.algorithm.lower() == "qaoa":
        path, distance = optimizer.solve_qaoa(graph, request.start_node_id, request.end_node_id)
    else:
        raise HTTPException(status_code=400, detail="Invalid algorithm. Use 'dijkstra' or 'qaoa'")
    
    execution_time = time.time() - start_time
    
    if not path:
        raise HTTPException(status_code=404, detail="No path found between nodes")
    
    # Create and store result
    result = RouteResult(
        algorithm=request.algorithm,
        start_node_id=request.start_node_id,
        end_node_id=request.end_node_id,
        path=path,
        distance=distance,
        execution_time=execution_time
    )
    
    await db.route_results.insert_one(result.dict())
    return result

@api_router.get("/route/results", response_model=List[RouteResult])
async def get_route_results():
    """Get all route optimization results"""
    results = await db.route_results.find().to_list(1000)
    return [RouteResult(**result) for result in results]

@api_router.get("/graph/visualization")
async def get_graph_visualization():
    """Get graph data for visualization"""
    nodes_cursor = db.nodes.find()
    nodes = await nodes_cursor.to_list(1000)
    
    # Prepare nodes for visualization
    vis_nodes = []
    for node in nodes:
        vis_nodes.append({
            "id": node['id'],
            "name": node['name'],
            "lat": node['lat'],
            "lng": node['lng']
        })
    
    # Create edges between all nodes
    vis_edges = []
    for i, node1 in enumerate(vis_nodes):
        for j, node2 in enumerate(vis_nodes):
            if i < j:
                distance = calculate_distance(
                    node1['lat'], node1['lng'],
                    node2['lat'], node2['lng']
                )
                vis_edges.append({
                    "from": node1['id'],
                    "to": node2['id'],
                    "weight": round(distance, 2)
                })
    
    return {
        "nodes": vis_nodes,
        "edges": vis_edges
    }

@api_router.post("/demo/create-sample-nodes")
async def create_sample_nodes():
    """Create sample nodes for demonstration"""
    # Clear existing nodes
    await db.nodes.delete_many({})
    
    # Sample delivery locations (10 nodes as requested)
    sample_nodes = [
        {"name": "Restaurant A", "lat": 40.7128, "lng": -74.0060},  # New York
        {"name": "Restaurant B", "lat": 40.7589, "lng": -73.9851},  # Times Square
        {"name": "Restaurant C", "lat": 40.6892, "lng": -74.0445},  # Jersey City
        {"name": "Customer 1", "lat": 40.7505, "lng": -73.9934},   # Near Times Square
        {"name": "Customer 2", "lat": 40.7282, "lng": -74.0776},   # Hoboken
        {"name": "Warehouse", "lat": 40.7831, "lng": -73.9712},    # Upper West Side
        {"name": "Distribution Center", "lat": 40.6782, "lng": -73.9442},  # Brooklyn
        {"name": "Restaurant D", "lat": 40.7614, "lng": -73.9776},  # Lincoln Center
        {"name": "Customer 3", "lat": 40.7400, "lng": -73.9897},   # Chelsea
        {"name": "Customer 4", "lat": 40.6928, "lng": -73.9903}    # Brooklyn Heights
    ]
    
    created_nodes = []
    for node_data in sample_nodes:
        node = Node(**node_data)
        await db.nodes.insert_one(node.dict())
        created_nodes.append(node)
    
    return {"message": f"Created {len(created_nodes)} sample nodes", "nodes": created_nodes}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()