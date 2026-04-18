"""
Test suite for Iteration 5 - Light Theme and Updated Graph
Tests: 8558 nodes, 18 schools, light theme verification
Tests search for: Alta Laja, Escudero, Costa Azul
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestGrafoStats:
    """Test graph statistics - updated for iteration 5"""
    
    def test_grafo_stats_node_count(self):
        """Verify correct node count (8558)"""
        response = requests.get(f"{BASE_URL}/api/grafo/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total_nodos"] == 8558, f"Expected 8558 nodes, got {data['total_nodos']}"
    
    def test_grafo_stats_school_count(self):
        """Verify correct school count (18)"""
        response = requests.get(f"{BASE_URL}/api/grafo/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total_escuelas"] == 18, f"Expected 18 schools, got {data['total_escuelas']}"
    
    def test_grafo_is_connected(self):
        """Verify graph is connected"""
        response = requests.get(f"{BASE_URL}/api/grafo/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["conectado"] == True, "Graph should be connected"


class TestEscuelas:
    """Test schools endpoint - 18 verified refugios"""
    
    def test_escuelas_returns_18_schools(self):
        """Verify 18 schools are returned"""
        response = requests.get(f"{BASE_URL}/api/escuelas")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 18, f"Expected 18 schools, got {len(data)}"
    
    def test_escuelas_have_verified_coordinates(self):
        """Verify schools have coordinates in Ciudad Renacimiento zone"""
        response = requests.get(f"{BASE_URL}/api/escuelas")
        assert response.status_code == 200
        data = response.json()
        
        for school in data:
            assert 16.88 <= school["lat"] <= 16.91, f"School {school['nombre']} lat out of range: {school['lat']}"
            assert -99.84 <= school["lon"] <= -99.81, f"School {school['nombre']} lon out of range: {school['lon']}"
    
    def test_escuelas_have_required_fields(self):
        """Verify schools have all required fields"""
        response = requests.get(f"{BASE_URL}/api/escuelas")
        assert response.status_code == 200
        data = response.json()
        
        required_fields = ["id", "nombre", "tipo", "nodo_id", "lat", "lon"]
        for school in data:
            for field in required_fields:
                assert field in school, f"School missing field: {field}"


class TestSearchNodos:
    """Test search endpoint for specific streets"""
    
    def test_search_alta_laja_finds_results(self):
        """Search 'Alta Laja' should find results"""
        response = requests.get(f"{BASE_URL}/api/buscar-nodos", params={"q": "Alta Laja"})
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0, "Should find results for 'Alta Laja'"
        
        names = [node["nombre"] for node in data]
        assert any("Alta Laja" in name for name in names), f"Should find 'Alta Laja' in results: {names[:5]}"
    
    def test_search_escudero_finds_results(self):
        """Search 'Escudero' should find results"""
        response = requests.get(f"{BASE_URL}/api/buscar-nodos", params={"q": "Escudero"})
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0, "Should find results for 'Escudero'"
        
        names = [node["nombre"] for node in data]
        assert any("Escudero" in name for name in names), f"Should find 'Escudero' in results: {names[:5]}"
    
    def test_search_costa_azul_finds_results(self):
        """Search 'Costa Azul' should find results"""
        response = requests.get(f"{BASE_URL}/api/buscar-nodos", params={"q": "Costa Azul"})
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0, "Should find results for 'Costa Azul'"
        
        names = [node["nombre"] for node in data]
        assert any("Costa Azul" in name for name in names), f"Should find 'Costa Azul' in results: {names[:5]}"
    
    def test_search_returns_max_25_results(self):
        """Search should return max 25 results"""
        response = requests.get(f"{BASE_URL}/api/buscar-nodos", params={"q": "Calle"})
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 25, f"Should return max 25 results, got {len(data)}"


class TestNodoCercano:
    """Test nearest node endpoint with Ciudad Renacimiento coordinates"""
    
    def test_nodo_cercano_ciudad_renacimiento_center(self):
        """Find nearest node to Ciudad Renacimiento center (16.8971, -99.8199)"""
        response = requests.post(f"{BASE_URL}/api/nodo-cercano", json={
            "lat": 16.8971,
            "lon": -99.8199
        })
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        assert "nombre" in data
        assert "lat" in data
        assert "lon" in data
        assert "distancia_m" in data
        
        # Should find a node within reasonable distance
        assert data["distancia_m"] < 50, f"Nearest node should be within 50m, got {data['distancia_m']}m"
    
    def test_nodo_cercano_returns_valid_node(self):
        """Nearest node should have valid coordinates in zone"""
        response = requests.post(f"{BASE_URL}/api/nodo-cercano", json={
            "lat": 16.89,
            "lon": -99.825
        })
        assert response.status_code == 200
        data = response.json()
        
        assert 16.85 <= data["lat"] <= 16.92
        assert -99.85 <= data["lon"] <= -99.80


class TestCalcularRuta:
    """Test route calculation with instructions and suggestions"""
    
    def test_calcular_ruta_returns_instructions(self):
        """Route should include step-by-step instructions"""
        # First get a valid node
        node_response = requests.post(f"{BASE_URL}/api/nodo-cercano", json={
            "lat": 16.8856874,
            "lon": -99.8262258
        })
        node_id = node_response.json()["id"]
        
        response = requests.post(f"{BASE_URL}/api/calcular-ruta", json={
            "nodo_origen": node_id
        })
        assert response.status_code == 200
        data = response.json()
        
        assert data["exito"] == True
        assert data["mejor_ruta"] is not None
        assert "instrucciones" in data["mejor_ruta"]
        assert len(data["mejor_ruta"]["instrucciones"]) > 0
    
    def test_calcular_ruta_returns_sugerencias(self):
        """Route should include emergency suggestions"""
        node_response = requests.post(f"{BASE_URL}/api/nodo-cercano", json={
            "lat": 16.8856874,
            "lon": -99.8262258
        })
        node_id = node_response.json()["id"]
        
        response = requests.post(f"{BASE_URL}/api/calcular-ruta", json={
            "nodo_origen": node_id
        })
        assert response.status_code == 200
        data = response.json()
        
        assert "sugerencias_emergencia" in data
        assert len(data["sugerencias_emergencia"]) > 0
    
    def test_calcular_ruta_returns_all_18_routes(self):
        """Route calculation should return routes to all 18 schools"""
        node_response = requests.post(f"{BASE_URL}/api/nodo-cercano", json={
            "lat": 16.8856874,
            "lon": -99.8262258
        })
        node_id = node_response.json()["id"]
        
        response = requests.post(f"{BASE_URL}/api/calcular-ruta", json={
            "nodo_origen": node_id
        })
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["todas_rutas"]) == 18, f"Should return routes to all 18 schools, got {len(data['todas_rutas'])}"
    
    def test_calcular_ruta_invalid_node(self):
        """Route calculation with invalid node should return 400"""
        response = requests.post(f"{BASE_URL}/api/calcular-ruta", json={
            "nodo_origen": "invalid_node_id"
        })
        assert response.status_code == 400


class TestAPIRoot:
    """Test API root endpoint"""
    
    def test_api_root(self):
        """API root should return welcome message"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
