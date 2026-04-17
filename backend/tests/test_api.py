"""
Backend API tests for Refugios A* application.
Tests all endpoints: root, escuelas, grafo/stats, buscar-nodos, calcular-ruta
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestRootEndpoint:
    """Test GET /api/ - Welcome message"""
    
    def test_root_returns_welcome_message(self):
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Refugios" in data["message"] or "API" in data["message"]
        print(f"✓ Root endpoint returns: {data['message']}")


class TestEscuelasEndpoint:
    """Test GET /api/escuelas - Returns 18 schools"""
    
    def test_escuelas_returns_list(self):
        response = requests.get(f"{BASE_URL}/api/escuelas")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Escuelas endpoint returns list with {len(data)} items")
    
    def test_escuelas_returns_18_schools(self):
        response = requests.get(f"{BASE_URL}/api/escuelas")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 18, f"Expected 18 schools, got {len(data)}"
        print(f"✓ Escuelas endpoint returns exactly 18 schools")
    
    def test_escuelas_structure(self):
        response = requests.get(f"{BASE_URL}/api/escuelas")
        assert response.status_code == 200
        data = response.json()
        # Check first school has required fields
        escuela = data[0]
        required_fields = ["id", "nombre", "tipo", "nodo_id", "lat", "lon"]
        for field in required_fields:
            assert field in escuela, f"Missing field: {field}"
        print(f"✓ Escuela structure is valid: {escuela['nombre']}")


class TestGrafoStatsEndpoint:
    """Test GET /api/grafo/stats - Returns graph statistics"""
    
    def test_grafo_stats_returns_stats(self):
        response = requests.get(f"{BASE_URL}/api/grafo/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_nodos" in data
        assert "total_aristas" in data
        assert "total_escuelas" in data
        print(f"✓ Grafo stats: {data['total_nodos']} nodos, {data['total_aristas']} aristas")
    
    def test_grafo_stats_has_1792_nodes(self):
        response = requests.get(f"{BASE_URL}/api/grafo/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total_nodos"] == 1792, f"Expected 1792 nodes, got {data['total_nodos']}"
        print(f"✓ Graph has exactly 1792 nodes")
    
    def test_grafo_is_connected(self):
        response = requests.get(f"{BASE_URL}/api/grafo/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["conectado"] == True, "Graph should be connected"
        print(f"✓ Graph is connected")


class TestBuscarNodosEndpoint:
    """Test GET /api/buscar-nodos - Search nodes by street name"""
    
    def test_buscar_zapata_returns_results(self):
        response = requests.get(f"{BASE_URL}/api/buscar-nodos", params={"q": "Zapata"})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0, "Search for 'Zapata' should return results"
        print(f"✓ Search 'Zapata' returns {len(data)} results")
        # Verify results contain Zapata in name
        for result in data[:3]:
            assert "Zapata" in result["nombre"], f"Result should contain 'Zapata': {result['nombre']}"
    
    def test_buscar_cuauhtemoc_accent_tolerant(self):
        """Test accent-tolerant search - Cuauhtemoc without accent"""
        response = requests.get(f"{BASE_URL}/api/buscar-nodos", params={"q": "Cuauhtemoc"})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0, "Search for 'Cuauhtemoc' (no accent) should return results"
        print(f"✓ Search 'Cuauhtemoc' (accent-tolerant) returns {len(data)} results")
    
    def test_buscar_single_char_returns_empty(self):
        """Test that single character search returns empty (min 2 chars)"""
        response = requests.get(f"{BASE_URL}/api/buscar-nodos", params={"q": "a"})
        assert response.status_code == 200
        data = response.json()
        assert data == [], f"Single char search should return empty, got {len(data)} results"
        print(f"✓ Single char 'a' returns empty list (min 2 chars required)")
    
    def test_buscar_empty_returns_empty(self):
        """Test that empty search returns empty"""
        response = requests.get(f"{BASE_URL}/api/buscar-nodos", params={"q": ""})
        assert response.status_code == 200
        data = response.json()
        assert data == [], "Empty search should return empty"
        print(f"✓ Empty search returns empty list")
    
    def test_buscar_result_structure(self):
        """Test search result structure"""
        response = requests.get(f"{BASE_URL}/api/buscar-nodos", params={"q": "Zapata"})
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        result = data[0]
        required_fields = ["id", "nombre", "lat", "lon", "tipo"]
        for field in required_fields:
            assert field in result, f"Missing field: {field}"
        print(f"✓ Search result structure is valid")


class TestCalcularRutaEndpoint:
    """Test POST /api/calcular-ruta - Calculate A* route"""
    
    def test_calcular_ruta_valid_node(self):
        """Test route calculation with valid node ID"""
        response = requests.post(
            f"{BASE_URL}/api/calcular-ruta",
            json={"nodo_origen": "308033213"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["exito"] == True
        assert "mejor_ruta" in data
        assert data["mejor_ruta"] is not None
        print(f"✓ Route calculated successfully to: {data['mejor_ruta']['escuela']['nombre']}")
    
    def test_calcular_ruta_returns_distance_and_time(self):
        """Test route returns distance and time"""
        response = requests.post(
            f"{BASE_URL}/api/calcular-ruta",
            json={"nodo_origen": "1682374238"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["exito"] == True
        mejor_ruta = data["mejor_ruta"]
        assert "distancia_total" in mejor_ruta
        assert "tiempo_minutos" in mejor_ruta
        assert mejor_ruta["distancia_total"] > 0
        assert mejor_ruta["tiempo_minutos"] > 0
        print(f"✓ Route: {mejor_ruta['distancia_total']:.1f}m, {mejor_ruta['tiempo_minutos']:.1f} min")
    
    def test_calcular_ruta_returns_coordinates(self):
        """Test route returns coordinate path"""
        response = requests.post(
            f"{BASE_URL}/api/calcular-ruta",
            json={"nodo_origen": "1687170343"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["exito"] == True
        mejor_ruta = data["mejor_ruta"]
        assert "ruta_coordenadas" in mejor_ruta
        assert len(mejor_ruta["ruta_coordenadas"]) > 0
        # Check coordinate structure
        coord = mejor_ruta["ruta_coordenadas"][0]
        assert "lat" in coord
        assert "lon" in coord
        print(f"✓ Route has {len(mejor_ruta['ruta_coordenadas'])} coordinate points")
    
    def test_calcular_ruta_returns_all_routes(self):
        """Test route returns all routes to all schools"""
        response = requests.post(
            f"{BASE_URL}/api/calcular-ruta",
            json={"nodo_origen": "308033213"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "todas_rutas" in data
        assert len(data["todas_rutas"]) == 18, f"Expected 18 routes, got {len(data['todas_rutas'])}"
        print(f"✓ Returns routes to all 18 schools")
    
    def test_calcular_ruta_invalid_node_returns_400(self):
        """Test route with invalid node returns 400 error"""
        response = requests.post(
            f"{BASE_URL}/api/calcular-ruta",
            json={"nodo_origen": "invalid_node_id_12345"}
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print(f"✓ Invalid node returns 400 error")
    
    def test_calcular_ruta_routes_sorted_by_distance(self):
        """Test that routes are sorted by distance (nearest first)"""
        response = requests.post(
            f"{BASE_URL}/api/calcular-ruta",
            json={"nodo_origen": "308033213"}
        )
        assert response.status_code == 200
        data = response.json()
        todas_rutas = data["todas_rutas"]
        # Check routes are sorted by distance
        distances = [r["distancia_total"] for r in todas_rutas]
        assert distances == sorted(distances), "Routes should be sorted by distance"
        print(f"✓ Routes are sorted by distance (nearest: {distances[0]:.1f}m)")


class TestNodosEndpoint:
    """Test GET /api/nodos - Returns all nodes"""
    
    def test_nodos_returns_list(self):
        response = requests.get(f"{BASE_URL}/api/nodos")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1792, f"Expected 1792 nodes, got {len(data)}"
        print(f"✓ Nodos endpoint returns {len(data)} nodes")


class TestAristasEndpoint:
    """Test GET /api/aristas - Returns all edges"""
    
    def test_aristas_returns_list(self):
        response = requests.get(f"{BASE_URL}/api/aristas")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 2000, f"Expected >2000 edges, got {len(data)}"
        print(f"✓ Aristas endpoint returns {len(data)} edges")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
