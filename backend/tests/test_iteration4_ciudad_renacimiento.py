"""
Test suite for Iteration 4 - Ciudad Renacimiento zone update
Tests the new OSM data with 4318 nodes, 6044 edges, 18 schools
Tests search for new street names: Escudero, Zaragoza, Canal, Lazaro
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestGrafoStats:
    """Test graph statistics for new Ciudad Renacimiento zone"""
    
    def test_grafo_stats_node_count(self):
        """Verify correct node count (4318)"""
        response = requests.get(f"{BASE_URL}/api/grafo/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total_nodos"] == 4318, f"Expected 4318 nodes, got {data['total_nodos']}"
    
    def test_grafo_stats_edge_count(self):
        """Verify correct edge count (~6044)"""
        response = requests.get(f"{BASE_URL}/api/grafo/stats")
        assert response.status_code == 200
        data = response.json()
        # Allow some tolerance for edge count
        assert 6000 <= data["total_aristas"] <= 6100, f"Expected ~6044 edges, got {data['total_aristas']}"
    
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
    """Test schools endpoint for new zone"""
    
    def test_escuelas_returns_18_schools(self):
        """Verify 18 schools are returned"""
        response = requests.get(f"{BASE_URL}/api/escuelas")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 18, f"Expected 18 schools, got {len(data)}"
    
    def test_escuelas_have_correct_node_ids(self):
        """Verify schools have valid node IDs"""
        response = requests.get(f"{BASE_URL}/api/escuelas")
        assert response.status_code == 200
        data = response.json()
        
        # Check specific school node IDs from the new zone
        expected_node_ids = ["1912974604", "1912974404", "1912974033", "1859337429"]
        found_ids = [school["nodo_id"] for school in data]
        
        for expected_id in expected_node_ids:
            assert expected_id in found_ids, f"Expected node_id {expected_id} not found in schools"
    
    def test_escuelas_have_coordinates_in_new_zone(self):
        """Verify school coordinates are in Ciudad Renacimiento zone"""
        response = requests.get(f"{BASE_URL}/api/escuelas")
        assert response.status_code == 200
        data = response.json()
        
        # Ciudad Renacimiento center: 16.8971, -99.8199
        # Schools should be within reasonable distance
        for school in data:
            assert 16.85 <= school["lat"] <= 16.92, f"School {school['nombre']} lat out of range: {school['lat']}"
            assert -99.85 <= school["lon"] <= -99.80, f"School {school['nombre']} lon out of range: {school['lon']}"


class TestSearchNodos:
    """Test search endpoint for new street names"""
    
    def test_search_escudero_finds_juan_r_escudero(self):
        """Search 'Escudero' should find 'Avenida Juan R. Escudero' streets"""
        response = requests.get(f"{BASE_URL}/api/buscar-nodos", params={"q": "Escudero"})
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0, "Should find results for 'Escudero'"
        
        # Check that at least one result contains "Juan R. Escudero"
        names = [node["nombre"] for node in data]
        assert any("Juan R. Escudero" in name for name in names), f"Should find 'Juan R. Escudero' in results: {names[:5]}"
    
    def test_search_zaragoza_finds_ignacio_zaragoza(self):
        """Search 'Zaragoza' should find 'Ignacio Zaragoza' streets"""
        response = requests.get(f"{BASE_URL}/api/buscar-nodos", params={"q": "Zaragoza"})
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0, "Should find results for 'Zaragoza'"
        
        names = [node["nombre"] for node in data]
        assert any("Ignacio Zaragoza" in name for name in names), f"Should find 'Ignacio Zaragoza' in results: {names[:5]}"
    
    def test_search_canal_finds_canal_del_arroyo(self):
        """Search 'Canal' should find 'Canal del Arroyo' streets"""
        response = requests.get(f"{BASE_URL}/api/buscar-nodos", params={"q": "Canal"})
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0, "Should find results for 'Canal'"
        
        names = [node["nombre"] for node in data]
        assert any("Canal" in name for name in names), f"Should find 'Canal' in results: {names[:5]}"
    
    def test_search_lazaro_accent_tolerant(self):
        """Search 'Lazaro' (without accent) should find 'Lázaro Cárdenas' streets"""
        response = requests.get(f"{BASE_URL}/api/buscar-nodos", params={"q": "Lazaro"})
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0, "Should find results for 'Lazaro' (accent tolerant)"
        
        names = [node["nombre"] for node in data]
        assert any("Lázaro" in name or "Lazaro" in name for name in names), f"Should find 'Lázaro' in results: {names[:5]}"
    
    def test_search_returns_max_25_results(self):
        """Search should return max 25 results"""
        response = requests.get(f"{BASE_URL}/api/buscar-nodos", params={"q": "Calle"})
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 25, f"Should return max 25 results, got {len(data)}"
    
    def test_search_requires_min_2_chars(self):
        """Search with less than 2 chars should return empty"""
        response = requests.get(f"{BASE_URL}/api/buscar-nodos", params={"q": "A"})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0, "Should return empty for single character search"


class TestNodoCercano:
    """Test nearest node endpoint with new zone coordinates"""
    
    def test_nodo_cercano_in_new_zone(self):
        """Find nearest node to coordinates in Ciudad Renacimiento"""
        # Test with coordinates in the new zone center
        response = requests.post(f"{BASE_URL}/api/nodo-cercano", json={
            "lat": 16.897,
            "lon": -99.82
        })
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        assert "nombre" in data
        assert "lat" in data
        assert "lon" in data
        assert "distancia_m" in data
        
        # Should find a node within reasonable distance
        assert data["distancia_m"] < 100, f"Nearest node should be within 100m, got {data['distancia_m']}m"
    
    def test_nodo_cercano_returns_valid_node(self):
        """Nearest node should have valid coordinates in new zone"""
        response = requests.post(f"{BASE_URL}/api/nodo-cercano", json={
            "lat": 16.8971,
            "lon": -99.8199
        })
        assert response.status_code == 200
        data = response.json()
        
        # Verify returned node is in the zone
        assert 16.85 <= data["lat"] <= 16.92
        assert -99.85 <= data["lon"] <= -99.80


class TestCalcularRuta:
    """Test route calculation in new zone"""
    
    def test_calcular_ruta_from_test_node(self):
        """Calculate route from test node 1859337491 (Av Juan R Escudero / Ignacio Zaragoza)"""
        response = requests.post(f"{BASE_URL}/api/calcular-ruta", json={
            "nodo_origen": "1859337491"
        })
        assert response.status_code == 200
        data = response.json()
        
        assert data["exito"] == True
        assert data["mejor_ruta"] is not None
        assert len(data["todas_rutas"]) == 18, "Should calculate routes to all 18 schools"
    
    def test_calcular_ruta_has_instructions(self):
        """Route should include step-by-step instructions"""
        response = requests.post(f"{BASE_URL}/api/calcular-ruta", json={
            "nodo_origen": "1859337491"
        })
        assert response.status_code == 200
        data = response.json()
        
        mejor_ruta = data["mejor_ruta"]
        assert "instrucciones" in mejor_ruta
        assert len(mejor_ruta["instrucciones"]) > 0
        
        # Check instruction structure
        first_instruction = mejor_ruta["instrucciones"][0]
        assert "paso" in first_instruction
        assert "instruccion" in first_instruction
        assert "calle" in first_instruction
        assert "distancia_m" in first_instruction
    
    def test_calcular_ruta_instructions_reference_real_streets(self):
        """Instructions should reference real streets from Ciudad Renacimiento"""
        response = requests.post(f"{BASE_URL}/api/calcular-ruta", json={
            "nodo_origen": "1859337491"
        })
        assert response.status_code == 200
        data = response.json()
        
        mejor_ruta = data["mejor_ruta"]
        all_instructions = " ".join([i["instruccion"] for i in mejor_ruta["instrucciones"]])
        
        # Should reference at least one known street
        known_streets = ["Juan R. Escudero", "Ignacio Zaragoza", "Canal", "Circuito Interior"]
        found_street = any(street in all_instructions for street in known_streets)
        assert found_street, f"Instructions should reference known streets: {all_instructions[:200]}"
    
    def test_calcular_ruta_has_sugerencias_emergencia(self):
        """Route response should include emergency suggestions"""
        response = requests.post(f"{BASE_URL}/api/calcular-ruta", json={
            "nodo_origen": "1859337491"
        })
        assert response.status_code == 200
        data = response.json()
        
        assert "sugerencias_emergencia" in data
        assert len(data["sugerencias_emergencia"]) > 0
    
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
