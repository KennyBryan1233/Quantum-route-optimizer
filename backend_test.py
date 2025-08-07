#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Quantum Route Optimization System
Tests all API endpoints including QAOA and Dijkstra algorithms
"""

import requests
import json
import time
import sys
from typing import Dict, List, Any

# Get backend URL from environment
BACKEND_URL = "https://0f0323c4-560c-4e79-957c-05eeb4b5d17c.preview.emergentagent.com/api"

class QuantumRouteOptimizerTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.session = requests.Session()
        self.test_results = []
        self.sample_nodes = []
        
    def log_test(self, test_name: str, success: bool, message: str, details: Any = None):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "details": details,
            "timestamp": time.time()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        if details and not success:
            print(f"   Details: {details}")
    
    def test_api_health(self):
        """Test basic API health check"""
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "Quantum Route Optimization API" in data["message"]:
                    self.log_test("API Health Check", True, "API is responding correctly")
                    return True
                else:
                    self.log_test("API Health Check", False, "Unexpected response format", data)
                    return False
            else:
                self.log_test("API Health Check", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("API Health Check", False, f"Connection error: {str(e)}")
            return False
    
    def test_sample_data_generation(self):
        """Test sample data generation endpoint"""
        try:
            response = self.session.post(f"{self.base_url}/demo/create-sample-nodes")
            if response.status_code == 200:
                data = response.json()
                if "nodes" in data and len(data["nodes"]) == 10:
                    self.sample_nodes = data["nodes"]
                    self.log_test("Sample Data Generation", True, f"Created {len(data['nodes'])} sample nodes")
                    return True
                else:
                    self.log_test("Sample Data Generation", False, "Unexpected response format", data)
                    return False
            else:
                self.log_test("Sample Data Generation", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Sample Data Generation", False, f"Request error: {str(e)}")
            return False
    
    def test_get_nodes(self):
        """Test retrieving all nodes"""
        try:
            response = self.session.get(f"{self.base_url}/nodes")
            if response.status_code == 200:
                nodes = response.json()
                if isinstance(nodes, list) and len(nodes) >= 10:
                    # Verify node structure
                    sample_node = nodes[0]
                    required_fields = ["id", "name", "lat", "lng", "timestamp"]
                    if all(field in sample_node for field in required_fields):
                        self.log_test("Get Nodes", True, f"Retrieved {len(nodes)} nodes with correct structure")
                        return True
                    else:
                        self.log_test("Get Nodes", False, "Node structure missing required fields", sample_node)
                        return False
                else:
                    self.log_test("Get Nodes", False, f"Expected at least 10 nodes, got {len(nodes) if isinstance(nodes, list) else 'invalid format'}")
                    return False
            else:
                self.log_test("Get Nodes", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Get Nodes", False, f"Request error: {str(e)}")
            return False
    
    def test_create_custom_node(self):
        """Test creating a custom node"""
        try:
            custom_node = {
                "name": "Test Delivery Point",
                "lat": 40.7580,
                "lng": -73.9855
            }
            
            response = self.session.post(f"{self.base_url}/nodes", json=custom_node)
            if response.status_code == 200:
                node = response.json()
                if all(field in node for field in ["id", "name", "lat", "lng"]):
                    if (node["name"] == custom_node["name"] and 
                        node["lat"] == custom_node["lat"] and 
                        node["lng"] == custom_node["lng"]):
                        self.log_test("Create Custom Node", True, f"Created node: {node['name']}")
                        return True, node["id"]
                    else:
                        self.log_test("Create Custom Node", False, "Node data mismatch", node)
                        return False, None
                else:
                    self.log_test("Create Custom Node", False, "Invalid node structure", node)
                    return False, None
            else:
                self.log_test("Create Custom Node", False, f"HTTP {response.status_code}", response.text)
                return False, None
        except Exception as e:
            self.log_test("Create Custom Node", False, f"Request error: {str(e)}")
            return False, None
    
    def test_delete_node(self, node_id: str):
        """Test deleting a node"""
        try:
            response = self.session.delete(f"{self.base_url}/nodes/{node_id}")
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "deleted successfully" in data["message"]:
                    self.log_test("Delete Node", True, f"Successfully deleted node {node_id}")
                    return True
                else:
                    self.log_test("Delete Node", False, "Unexpected response format", data)
                    return False
            else:
                self.log_test("Delete Node", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Delete Node", False, f"Request error: {str(e)}")
            return False
    
    def test_graph_visualization(self):
        """Test graph visualization endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/graph/visualization")
            if response.status_code == 200:
                data = response.json()
                if "nodes" in data and "edges" in data:
                    nodes = data["nodes"]
                    edges = data["edges"]
                    if len(nodes) >= 10 and len(edges) > 0:
                        # Verify node structure
                        sample_node = nodes[0]
                        if all(field in sample_node for field in ["id", "name", "lat", "lng"]):
                            # Verify edge structure
                            sample_edge = edges[0]
                            if all(field in sample_edge for field in ["from", "to", "weight"]):
                                self.log_test("Graph Visualization", True, f"Retrieved {len(nodes)} nodes and {len(edges)} edges")
                                return True
                            else:
                                self.log_test("Graph Visualization", False, "Invalid edge structure", sample_edge)
                                return False
                        else:
                            self.log_test("Graph Visualization", False, "Invalid node structure", sample_node)
                            return False
                    else:
                        self.log_test("Graph Visualization", False, f"Insufficient data: {len(nodes)} nodes, {len(edges)} edges")
                        return False
                else:
                    self.log_test("Graph Visualization", False, "Missing nodes or edges in response", data)
                    return False
            else:
                self.log_test("Graph Visualization", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Graph Visualization", False, f"Request error: {str(e)}")
            return False
    
    def test_route_optimization_dijkstra(self):
        """Test route optimization using Dijkstra algorithm"""
        try:
            # Get current nodes to select start and end points
            nodes_response = self.session.get(f"{self.base_url}/nodes")
            if nodes_response.status_code != 200:
                self.log_test("Route Optimization (Dijkstra)", False, "Could not retrieve nodes for testing")
                return False
            
            nodes = nodes_response.json()
            if len(nodes) < 2:
                self.log_test("Route Optimization (Dijkstra)", False, "Need at least 2 nodes for route optimization")
                return False
            
            # Select first and last nodes as start and end
            start_node = nodes[0]["id"]
            end_node = nodes[-1]["id"]
            
            route_request = {
                "start_node_id": start_node,
                "end_node_id": end_node,
                "algorithm": "dijkstra"
            }
            
            start_time = time.time()
            response = self.session.post(f"{self.base_url}/route/optimize", json=route_request)
            execution_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                required_fields = ["algorithm", "start_node_id", "end_node_id", "path", "distance", "execution_time"]
                if all(field in result for field in required_fields):
                    if (result["algorithm"] == "dijkstra" and 
                        result["start_node_id"] == start_node and 
                        result["end_node_id"] == end_node and
                        isinstance(result["path"], list) and len(result["path"]) >= 2 and
                        isinstance(result["distance"], (int, float)) and result["distance"] >= 0 and
                        isinstance(result["execution_time"], (int, float))):
                        
                        self.log_test("Route Optimization (Dijkstra)", True, 
                                    f"Path found: {len(result['path'])} nodes, distance: {result['distance']:.2f}km, time: {result['execution_time']:.3f}s")
                        return True
                    else:
                        self.log_test("Route Optimization (Dijkstra)", False, "Invalid result data", result)
                        return False
                else:
                    self.log_test("Route Optimization (Dijkstra)", False, "Missing required fields", result)
                    return False
            else:
                self.log_test("Route Optimization (Dijkstra)", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Route Optimization (Dijkstra)", False, f"Request error: {str(e)}")
            return False
    
    def test_route_optimization_qaoa(self):
        """Test route optimization using QAOA algorithm"""
        try:
            # Get current nodes to select start and end points
            nodes_response = self.session.get(f"{self.base_url}/nodes")
            if nodes_response.status_code != 200:
                self.log_test("Route Optimization (QAOA)", False, "Could not retrieve nodes for testing")
                return False
            
            nodes = nodes_response.json()
            if len(nodes) < 2:
                self.log_test("Route Optimization (QAOA)", False, "Need at least 2 nodes for route optimization")
                return False
            
            # Select different nodes for QAOA test
            start_node = nodes[1]["id"] if len(nodes) > 1 else nodes[0]["id"]
            end_node = nodes[2]["id"] if len(nodes) > 2 else nodes[-1]["id"]
            
            route_request = {
                "start_node_id": start_node,
                "end_node_id": end_node,
                "algorithm": "qaoa"
            }
            
            start_time = time.time()
            response = self.session.post(f"{self.base_url}/route/optimize", json=route_request)
            execution_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                required_fields = ["algorithm", "start_node_id", "end_node_id", "path", "distance", "execution_time"]
                if all(field in result for field in required_fields):
                    if (result["algorithm"] == "qaoa" and 
                        result["start_node_id"] == start_node and 
                        result["end_node_id"] == end_node and
                        isinstance(result["path"], list) and len(result["path"]) >= 2 and
                        isinstance(result["distance"], (int, float)) and result["distance"] >= 0 and
                        isinstance(result["execution_time"], (int, float))):
                        
                        self.log_test("Route Optimization (QAOA)", True, 
                                    f"Path found: {len(result['path'])} nodes, distance: {result['distance']:.2f}km, time: {result['execution_time']:.3f}s")
                        return True
                    else:
                        self.log_test("Route Optimization (QAOA)", False, "Invalid result data", result)
                        return False
                else:
                    self.log_test("Route Optimization (QAOA)", False, "Missing required fields", result)
                    return False
            else:
                self.log_test("Route Optimization (QAOA)", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Route Optimization (QAOA)", False, f"Request error: {str(e)}")
            return False
    
    def test_route_results_history(self):
        """Test retrieving route optimization results history"""
        try:
            response = self.session.get(f"{self.base_url}/route/results")
            if response.status_code == 200:
                results = response.json()
                if isinstance(results, list):
                    if len(results) >= 2:  # Should have at least 2 results from previous tests
                        sample_result = results[0]
                        required_fields = ["algorithm", "start_node_id", "end_node_id", "path", "distance", "execution_time"]
                        if all(field in sample_result for field in required_fields):
                            self.log_test("Route Results History", True, f"Retrieved {len(results)} route optimization results")
                            return True
                        else:
                            self.log_test("Route Results History", False, "Invalid result structure", sample_result)
                            return False
                    else:
                        self.log_test("Route Results History", True, f"Retrieved {len(results)} results (may be empty initially)")
                        return True
                else:
                    self.log_test("Route Results History", False, "Expected list of results", results)
                    return False
            else:
                self.log_test("Route Results History", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Route Results History", False, f"Request error: {str(e)}")
            return False
    
    def test_error_handling(self):
        """Test error handling for invalid requests"""
        try:
            # Test invalid algorithm
            invalid_request = {
                "start_node_id": "invalid_id",
                "end_node_id": "invalid_id",
                "algorithm": "invalid_algorithm"
            }
            
            response = self.session.post(f"{self.base_url}/route/optimize", json=invalid_request)
            if response.status_code == 400:
                self.log_test("Error Handling (Invalid Algorithm)", True, "Correctly rejected invalid algorithm")
            else:
                self.log_test("Error Handling (Invalid Algorithm)", False, f"Expected 400, got {response.status_code}")
            
            # Test invalid node IDs
            nodes_response = self.session.get(f"{self.base_url}/nodes")
            if nodes_response.status_code == 200:
                nodes = nodes_response.json()
                if nodes:
                    valid_request = {
                        "start_node_id": "nonexistent_id",
                        "end_node_id": nodes[0]["id"],
                        "algorithm": "dijkstra"
                    }
                    
                    response = self.session.post(f"{self.base_url}/route/optimize", json=valid_request)
                    if response.status_code == 404:
                        self.log_test("Error Handling (Invalid Node ID)", True, "Correctly rejected invalid node ID")
                        return True
                    else:
                        self.log_test("Error Handling (Invalid Node ID)", False, f"Expected 404, got {response.status_code}")
                        return False
            
            return True
        except Exception as e:
            self.log_test("Error Handling", False, f"Request error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Quantum Route Optimization Backend Tests")
        print("=" * 60)
        
        # Test sequence
        tests_passed = 0
        total_tests = 0
        
        # 1. Basic API Health
        total_tests += 1
        if self.test_api_health():
            tests_passed += 1
        
        # 2. Sample Data Generation
        total_tests += 1
        if self.test_sample_data_generation():
            tests_passed += 1
        
        # 3. Node Management
        total_tests += 1
        if self.test_get_nodes():
            tests_passed += 1
        
        total_tests += 1
        success, node_id = self.test_create_custom_node()
        if success:
            tests_passed += 1
            
            # Test delete if create was successful
            total_tests += 1
            if self.test_delete_node(node_id):
                tests_passed += 1
        else:
            total_tests += 1  # Count the delete test as failed
        
        # 4. Graph Visualization
        total_tests += 1
        if self.test_graph_visualization():
            tests_passed += 1
        
        # 5. Route Optimization - Dijkstra
        total_tests += 1
        if self.test_route_optimization_dijkstra():
            tests_passed += 1
        
        # 6. Route Optimization - QAOA
        total_tests += 1
        if self.test_route_optimization_qaoa():
            tests_passed += 1
        
        # 7. Route Results History
        total_tests += 1
        if self.test_route_results_history():
            tests_passed += 1
        
        # 8. Error Handling
        total_tests += 1
        if self.test_error_handling():
            tests_passed += 1
        
        # Summary
        print("\n" + "=" * 60)
        print(f"🏁 Test Summary: {tests_passed}/{total_tests} tests passed")
        
        if tests_passed == total_tests:
            print("🎉 All tests passed! Quantum Route Optimization backend is working correctly.")
            return True
        else:
            print(f"⚠️  {total_tests - tests_passed} tests failed. Check the details above.")
            return False

def main():
    """Main test execution"""
    tester = QuantumRouteOptimizerTester()
    success = tester.run_all_tests()
    
    # Return appropriate exit code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()