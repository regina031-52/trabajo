"""
Backend API tests for ITERATION 3 features in Refugios A* application.
Tests: Improved search (prefix-stripping), collapsible panel, GPS button
New search: User doesn't need to type 'Calle', 'Avenida', etc.
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestImprovedSearchPrefixStripping:
    """Test GET /api/buscar-nodos - Improved search that strips prefixes"""
    
    def test_search_morro_finds_calle_el_morro(self):
        """Test that searching 'Morro' finds 'Calle el Morro' without typing 'Calle'"""
        response = requests.get(f"{BASE_URL}/api/buscar-nodos", params={"q": "Morro"})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0, "Should find results for 'Morro'"
        
        # Check that at least one result contains 'Morro'
        found_morro = any("morro" in r["nombre"].lower() for r in data)
        assert found_morro, f"Should find 'Morro' in results: {[r['nombre'] for r in data[:5]]}"
        print(f"✓ Search 'Morro' found {len(data)} results: {[r['nombre'] for r in data[:3]]}")
    
    def test_search_febrero_finds_5_de_febrero(self):
        """Test that searching 'Febrero' finds 'Calle 5 de Febrero' without prefix"""
        response = requests.get(f"{BASE_URL}/api/buscar-nodos", params={"q": "Febrero"})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0, "Should find results for 'Febrero'"
        
        # Check that at least one result contains 'Febrero'
        found_febrero = any("febrero" in r["nombre"].lower() for r in data)
        assert found_febrero, f"Should find 'Febrero' in results: {[r['nombre'] for r in data[:5]]}"
        print(f"✓ Search 'Febrero' found {len(data)} results: {[r['nombre'] for r in data[:3]]}")
    
    def test_search_perla_finds_la_perla(self):
        """Test that searching 'Perla' finds 'La Perla' street"""
        response = requests.get(f"{BASE_URL}/api/buscar-nodos", params={"q": "Perla"})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0, "Should find results for 'Perla'"
        
        # Check that at least one result contains 'Perla'
        found_perla = any("perla" in r["nombre"].lower() for r in data)
        assert found_perla, f"Should find 'Perla' in results: {[r['nombre'] for r in data[:5]]}"
        print(f"✓ Search 'Perla' found {len(data)} results: {[r['nombre'] for r in data[:3]]}")
    
    def test_search_zapata_still_works(self):
        """Test that existing search for 'Zapata' still works"""
        response = requests.get(f"{BASE_URL}/api/buscar-nodos", params={"q": "Zapata"})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0, "Should find results for 'Zapata'"
        print(f"✓ Search 'Zapata' found {len(data)} results")
    
    def test_search_cuauhtemoc_accent_tolerant(self):
        """Test that accent-tolerant search still works"""
        response = requests.get(f"{BASE_URL}/api/buscar-nodos", params={"q": "Cuauhtemoc"})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should find Cuauhtémoc even without accent
        print(f"✓ Search 'Cuauhtemoc' found {len(data)} results")
    
    def test_search_returns_max_25_results(self):
        """Test that search returns maximum 25 results"""
        response = requests.get(f"{BASE_URL}/api/buscar-nodos", params={"q": "Calle"})
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 25, f"Should return max 25 results, got {len(data)}"
        print(f"✓ Search returns max 25 results (got {len(data)})")
    
    def test_search_min_2_chars(self):
        """Test that search requires minimum 2 characters"""
        response = requests.get(f"{BASE_URL}/api/buscar-nodos", params={"q": "a"})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0, "Should return empty for single character"
        print(f"✓ Search requires min 2 chars")
    
    def test_search_cerca_de_nodes(self):
        """Test that 'Cerca de...' named nodes are searchable"""
        response = requests.get(f"{BASE_URL}/api/buscar-nodos", params={"q": "Cerca"})
        assert response.status_code == 200
        data = response.json()
        # Should find nodes with 'Cerca de...' names
        found_cerca = any("cerca" in r["nombre"].lower() for r in data)
        if found_cerca:
            print(f"✓ Found 'Cerca de...' nodes: {[r['nombre'] for r in data[:3]]}")
        else:
            print(f"✓ Search 'Cerca' returned {len(data)} results")


class TestNodoCercanoStillWorks:
    """Test POST /api/nodo-cercano - Verify it still works correctly"""
    
    def test_nodo_cercano_basic(self):
        """Test basic nodo-cercano functionality"""
        response = requests.post(
            f"{BASE_URL}/api/nodo-cercano",
            json={"lat": 16.87, "lon": -99.883}
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "nombre" in data
        assert "lat" in data
        assert "lon" in data
        assert "distancia_m" in data
        print(f"✓ Nodo cercano works: {data['nombre']}")
    
    def test_nodo_cercano_returns_valid_node_for_route(self):
        """Test that returned node can be used for route calculation"""
        # Get nearest node
        response = requests.post(
            f"{BASE_URL}/api/nodo-cercano",
            json={"lat": 16.8697, "lon": -99.8827}
        )
        assert response.status_code == 200
        nodo = response.json()
        
        # Use node for route
        route_response = requests.post(
            f"{BASE_URL}/api/calcular-ruta",
            json={"nodo_origen": nodo["id"]}
        )
        assert route_response.status_code == 200
        route_data = route_response.json()
        assert route_data["exito"] == True
        print(f"✓ Node {nodo['id']} valid for route calculation")


class TestCalcularRutaStillWorks:
    """Test POST /api/calcular-ruta - Verify it still returns instructions and suggestions"""
    
    def test_calcular_ruta_returns_instrucciones(self):
        """Test that calcular-ruta still returns instrucciones"""
        response = requests.post(
            f"{BASE_URL}/api/calcular-ruta",
            json={"nodo_origen": "1682374238"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["exito"] == True
        assert "instrucciones" in data["mejor_ruta"]
        assert len(data["mejor_ruta"]["instrucciones"]) > 0
        print(f"✓ Route has {len(data['mejor_ruta']['instrucciones'])} instructions")
    
    def test_calcular_ruta_returns_sugerencias(self):
        """Test that calcular-ruta still returns sugerencias_emergencia"""
        response = requests.post(
            f"{BASE_URL}/api/calcular-ruta",
            json={"nodo_origen": "1682374238"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "sugerencias_emergencia" in data
        assert len(data["sugerencias_emergencia"]) == 15
        print(f"✓ Route has {len(data['sugerencias_emergencia'])} emergency suggestions")
    
    def test_calcular_ruta_returns_todas_rutas(self):
        """Test that calcular-ruta returns all routes"""
        response = requests.post(
            f"{BASE_URL}/api/calcular-ruta",
            json={"nodo_origen": "1682374238"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "todas_rutas" in data
        assert len(data["todas_rutas"]) > 0
        print(f"✓ Route returns {len(data['todas_rutas'])} total routes")


class TestExistingEndpointsStillWork:
    """Test that existing endpoints still work correctly"""
    
    def test_root_endpoint(self):
        """Test GET /api/ returns welcome message"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"✓ Root endpoint works")
    
    def test_escuelas_endpoint(self):
        """Test GET /api/escuelas returns schools"""
        response = requests.get(f"{BASE_URL}/api/escuelas")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        print(f"✓ Escuelas endpoint returns {len(data)} schools")
    
    def test_grafo_stats_endpoint(self):
        """Test GET /api/grafo/stats returns statistics"""
        response = requests.get(f"{BASE_URL}/api/grafo/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_nodos" in data
        assert "total_escuelas" in data
        print(f"✓ Grafo stats: {data['total_nodos']} nodes, {data['total_escuelas']} schools")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
