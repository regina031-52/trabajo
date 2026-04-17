"""
Backend API tests for NEW FEATURES in Refugios A* application.
Tests: nodo-cercano endpoint, instrucciones in calcular-ruta, sugerencias_emergencia
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestNodoCercanoEndpoint:
    """Test POST /api/nodo-cercano - Find nearest node from lat/lon"""
    
    def test_nodo_cercano_returns_nearest_node(self):
        """Test that nodo-cercano returns a valid node"""
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
        assert "tipo" in data
        assert "distancia_m" in data
        print(f"✓ Nodo cercano found: {data['nombre']} at {data['distancia_m']:.1f}m")
    
    def test_nodo_cercano_returns_distance(self):
        """Test that nodo-cercano returns distance in meters"""
        response = requests.post(
            f"{BASE_URL}/api/nodo-cercano",
            json={"lat": 16.87, "lon": -99.883}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["distancia_m"], (int, float))
        assert data["distancia_m"] >= 0
        print(f"✓ Distance returned: {data['distancia_m']:.1f}m")
    
    def test_nodo_cercano_different_location(self):
        """Test nodo-cercano with different coordinates"""
        response = requests.post(
            f"{BASE_URL}/api/nodo-cercano",
            json={"lat": 16.8697, "lon": -99.8827}
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        # The returned node should be close to the input coordinates
        assert abs(data["lat"] - 16.8697) < 0.01
        assert abs(data["lon"] - (-99.8827)) < 0.01
        print(f"✓ Different location test passed: {data['nombre']}")
    
    def test_nodo_cercano_returns_valid_node_id(self):
        """Test that returned node ID can be used in calcular-ruta"""
        # First get nearest node
        response = requests.post(
            f"{BASE_URL}/api/nodo-cercano",
            json={"lat": 16.87, "lon": -99.883}
        )
        assert response.status_code == 200
        nodo = response.json()
        
        # Then use that node ID to calculate route
        route_response = requests.post(
            f"{BASE_URL}/api/calcular-ruta",
            json={"nodo_origen": nodo["id"]}
        )
        assert route_response.status_code == 200
        route_data = route_response.json()
        assert route_data["exito"] == True
        print(f"✓ Node ID {nodo['id']} is valid for route calculation")


class TestInstruccionesInCalcularRuta:
    """Test that POST /api/calcular-ruta includes instrucciones array"""
    
    def test_calcular_ruta_includes_instrucciones(self):
        """Test that mejor_ruta includes instrucciones array"""
        response = requests.post(
            f"{BASE_URL}/api/calcular-ruta",
            json={"nodo_origen": "1682374238"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["exito"] == True
        assert "instrucciones" in data["mejor_ruta"]
        assert isinstance(data["mejor_ruta"]["instrucciones"], list)
        print(f"✓ Instrucciones array present with {len(data['mejor_ruta']['instrucciones'])} steps")
    
    def test_instrucciones_not_empty(self):
        """Test that instrucciones array is not empty"""
        response = requests.post(
            f"{BASE_URL}/api/calcular-ruta",
            json={"nodo_origen": "1682374238"}
        )
        assert response.status_code == 200
        data = response.json()
        instrucciones = data["mejor_ruta"]["instrucciones"]
        assert len(instrucciones) > 0, "Instrucciones should not be empty"
        print(f"✓ Instrucciones has {len(instrucciones)} steps")
    
    def test_instrucciones_structure(self):
        """Test that each instruction has required fields"""
        response = requests.post(
            f"{BASE_URL}/api/calcular-ruta",
            json={"nodo_origen": "1682374238"}
        )
        assert response.status_code == 200
        data = response.json()
        instrucciones = data["mejor_ruta"]["instrucciones"]
        
        for i, inst in enumerate(instrucciones):
            assert "paso" in inst, f"Instruction {i} missing 'paso'"
            assert "instruccion" in inst, f"Instruction {i} missing 'instruccion'"
            assert "calle" in inst, f"Instruction {i} missing 'calle'"
            assert "distancia_m" in inst, f"Instruction {i} missing 'distancia_m'"
            assert "acumulado_m" in inst, f"Instruction {i} missing 'acumulado_m'"
        
        print(f"✓ All {len(instrucciones)} instructions have valid structure")
    
    def test_instrucciones_paso_sequential(self):
        """Test that paso numbers are sequential starting from 1"""
        response = requests.post(
            f"{BASE_URL}/api/calcular-ruta",
            json={"nodo_origen": "1682374238"}
        )
        assert response.status_code == 200
        data = response.json()
        instrucciones = data["mejor_ruta"]["instrucciones"]
        
        for i, inst in enumerate(instrucciones):
            expected_paso = i + 1
            assert inst["paso"] == expected_paso, f"Expected paso {expected_paso}, got {inst['paso']}"
        
        print(f"✓ Paso numbers are sequential (1 to {len(instrucciones)})")
    
    def test_instrucciones_acumulado_increasing(self):
        """Test that acumulado_m is non-decreasing"""
        response = requests.post(
            f"{BASE_URL}/api/calcular-ruta",
            json={"nodo_origen": "1682374238"}
        )
        assert response.status_code == 200
        data = response.json()
        instrucciones = data["mejor_ruta"]["instrucciones"]
        
        prev_acumulado = 0
        for inst in instrucciones:
            assert inst["acumulado_m"] >= prev_acumulado, \
                f"Acumulado should be non-decreasing: {prev_acumulado} -> {inst['acumulado_m']}"
            prev_acumulado = inst["acumulado_m"]
        
        print(f"✓ Acumulado_m is non-decreasing (final: {prev_acumulado}m)")
    
    def test_instrucciones_last_step_is_arrival(self):
        """Test that last instruction indicates arrival"""
        response = requests.post(
            f"{BASE_URL}/api/calcular-ruta",
            json={"nodo_origen": "1682374238"}
        )
        assert response.status_code == 200
        data = response.json()
        instrucciones = data["mejor_ruta"]["instrucciones"]
        
        last_inst = instrucciones[-1]
        assert "llegado" in last_inst["instruccion"].lower() or "destino" in last_inst["calle"].lower(), \
            f"Last instruction should indicate arrival: {last_inst['instruccion']}"
        
        print(f"✓ Last instruction indicates arrival: '{last_inst['instruccion']}'")


class TestSugerenciasEmergencia:
    """Test that POST /api/calcular-ruta includes sugerencias_emergencia array"""
    
    def test_calcular_ruta_includes_sugerencias(self):
        """Test that response includes sugerencias_emergencia array"""
        response = requests.post(
            f"{BASE_URL}/api/calcular-ruta",
            json={"nodo_origen": "1682374238"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "sugerencias_emergencia" in data
        assert isinstance(data["sugerencias_emergencia"], list)
        print(f"✓ Sugerencias_emergencia array present")
    
    def test_sugerencias_not_empty(self):
        """Test that sugerencias_emergencia is not empty"""
        response = requests.post(
            f"{BASE_URL}/api/calcular-ruta",
            json={"nodo_origen": "1682374238"}
        )
        assert response.status_code == 200
        data = response.json()
        sugerencias = data["sugerencias_emergencia"]
        assert len(sugerencias) > 0, "Sugerencias should not be empty"
        print(f"✓ Sugerencias has {len(sugerencias)} items")
    
    def test_sugerencias_has_15_items(self):
        """Test that sugerencias_emergencia has 15 items"""
        response = requests.post(
            f"{BASE_URL}/api/calcular-ruta",
            json={"nodo_origen": "1682374238"}
        )
        assert response.status_code == 200
        data = response.json()
        sugerencias = data["sugerencias_emergencia"]
        assert len(sugerencias) == 15, f"Expected 15 sugerencias, got {len(sugerencias)}"
        print(f"✓ Sugerencias has exactly 15 items")
    
    def test_sugerencias_are_strings(self):
        """Test that all sugerencias are non-empty strings"""
        response = requests.post(
            f"{BASE_URL}/api/calcular-ruta",
            json={"nodo_origen": "1682374238"}
        )
        assert response.status_code == 200
        data = response.json()
        sugerencias = data["sugerencias_emergencia"]
        
        for i, sug in enumerate(sugerencias):
            assert isinstance(sug, str), f"Sugerencia {i} should be string"
            assert len(sug) > 0, f"Sugerencia {i} should not be empty"
        
        print(f"✓ All {len(sugerencias)} sugerencias are valid strings")
    
    def test_sugerencias_includes_water(self):
        """Test that sugerencias includes water recommendation"""
        response = requests.post(
            f"{BASE_URL}/api/calcular-ruta",
            json={"nodo_origen": "1682374238"}
        )
        assert response.status_code == 200
        data = response.json()
        sugerencias = data["sugerencias_emergencia"]
        
        # Check for water-related suggestion
        has_water = any("agua" in s.lower() for s in sugerencias)
        assert has_water, "Sugerencias should include water recommendation"
        print(f"✓ Sugerencias includes water recommendation")


class TestNodosSeleccionablesEndpoint:
    """Test GET /api/nodos-seleccionables - Returns selectable nodes"""
    
    def test_nodos_seleccionables_returns_list(self):
        """Test that endpoint returns a list"""
        response = requests.get(f"{BASE_URL}/api/nodos-seleccionables")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        print(f"✓ Nodos seleccionables returns {len(data)} nodes")
    
    def test_nodos_seleccionables_structure(self):
        """Test that each node has required fields"""
        response = requests.get(f"{BASE_URL}/api/nodos-seleccionables")
        assert response.status_code == 200
        data = response.json()
        
        node = data[0]
        required_fields = ["id", "nombre", "lat", "lon", "tipo"]
        for field in required_fields:
            assert field in node, f"Missing field: {field}"
        
        print(f"✓ Node structure is valid")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
