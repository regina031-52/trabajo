"""
Script para construir el grafo de la Colonia Renacimiento en Acapulco, Guerrero
usando datos reales de OpenStreetMap a través de OSMnx.

Este script:
1. Descarga la red peatonal real de la colonia
2. Exporta todos los nodos y aristas a JSON
3. Asigna a cada escuela el nodo de red más cercano
4. Guarda los archivos JSON en disco
"""

import osmnx as ox
import networkx as nx
import json
from pathlib import Path
from scipy.spatial import cKDTree
import numpy as np

# Directorio para guardar los datos
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# Lista de escuelas/refugios con información proporcionada por el usuario
ESCUELAS = [
    {"id": "E01", "nombre": "Esc. Prim. Urb. Mat. Francisco Pérez Ríos", "alias": "", "tipo": "primaria", "unificada": False},
    {"id": "E02", "nombre": "Primaria Benemérito de las Américas", "alias": "", "tipo": "primaria", "unificada": False},
    {"id": "E03", "nombre": "Primaria Ignacio M. Altamirano / Estefanía Castañeda", "alias": "Ignacio M. Altamirano; Estefanía Castañeda", "tipo": "primaria", "unificada": True},
    {"id": "E04", "nombre": "Plantel Adolfo López Mateos", "alias": "Escuela Primaria Adolfo López Mateos; Esc. Prim. Urb. Vesp. Lic. Adolfo López Mateos", "tipo": "primaria", "unificada": True},
    {"id": "E05", "nombre": "Jardín de Niños Moisés Guevara", "alias": "", "tipo": "jardin", "unificada": False},
    {"id": "E06", "nombre": "Escuela Primaria Francisco Sarabia", "alias": "", "tipo": "primaria", "unificada": False},
    {"id": "E07", "nombre": "Escuela Primaria Rural Federal Jaime...", "alias": "", "tipo": "primaria", "unificada": False},
    {"id": "E08", "nombre": "Primaria 7", "alias": "", "tipo": "primaria", "unificada": False},
    {"id": "E09", "nombre": "Escuela Primaria Urbana Turno Matutino Raúl Isidro Burgos", "alias": "", "tipo": "primaria", "unificada": False},
    {"id": "E10", "nombre": "Escuela Prim. Raúl Isidro Burgos", "alias": "", "tipo": "primaria", "unificada": False},
    {"id": "E11", "nombre": "Plantel Jaime Torres Bodet No. 4 / Antonio I. Delgado", "alias": "Escuela Primaria Jaime Torres Bodet No. 4; Escuela Primaria Vespertina Antonio I. Delgado", "tipo": "primaria", "unificada": True},
    {"id": "E12", "nombre": "Escuela Primaria Turno Matutino Gabriela Mistral", "alias": "", "tipo": "primaria", "unificada": False},
    {"id": "E13", "nombre": "Escuela Primaria Urbana Matutina Lázaro Cárdenas", "alias": "", "tipo": "primaria", "unificada": False},
    {"id": "E14", "nombre": "Colegio Rodolfo Neri Vela", "alias": "", "tipo": "colegio", "unificada": False},
    {"id": "E15", "nombre": "Centro de Estudios Tecnológicos Industrial y de Servicios núm. 90 Julián Blanco Jiménez", "alias": "CETis 90 Julián Blanco Jiménez", "tipo": "cets", "unificada": False},
    {"id": "E16", "nombre": "Escuela Secundaria Técnica 68 Renacimiento", "alias": "", "tipo": "secundaria", "unificada": False},
    {"id": "E17", "nombre": "Escuela Secundaria General N. 49 Margarito Damián Vargas", "alias": "", "tipo": "secundaria", "unificada": False},
    {"id": "E18", "nombre": "Desarrollo Infantil y Juvenil Renacimiento A.C.", "alias": "", "tipo": "centro_educativo", "unificada": False},
]

def download_street_network():
    """
    Descarga la red peatonal de la Colonia Renacimiento, Acapulco usando OSMnx.
    Intenta múltiples métodos si alguno falla.
    """
    print("Descargando red de calles de Colonia Renacimiento, Acapulco...")
    
    # Coordenadas aproximadas del centro de la Colonia Renacimiento, Acapulco
    # Latitud: 16.8697, Longitud: -99.8827
    center_lat = 16.8697
    center_lon = -99.8827
    
    try:
        # Método 1: graph_from_point con radio de 1500m para cubrir la colonia
        print("Intentando descargar con graph_from_point...")
        G = ox.graph_from_point(
            center_point=(center_lat, center_lon),
            dist=1500,  # Radio en metros
            network_type="walk",
            simplify=True
        )
        print(f"Red descargada exitosamente: {G.number_of_nodes()} nodos, {G.number_of_edges()} aristas")
        return G
    except Exception as e:
        print(f"Error con graph_from_point: {e}")
    
    try:
        # Método 2: graph_from_address
        print("Intentando descargar con graph_from_address...")
        G = ox.graph_from_address(
            address="Colonia Renacimiento, Acapulco de Juárez, Guerrero, México",
            dist=1500,
            network_type="walk",
            simplify=True
        )
        print(f"Red descargada exitosamente: {G.number_of_nodes()} nodos, {G.number_of_edges()} aristas")
        return G
    except Exception as e:
        print(f"Error con graph_from_address: {e}")
    
    try:
        # Método 3: graph_from_bbox (bounding box)
        print("Intentando descargar con graph_from_bbox...")
        # Bounding box aproximado de la colonia
        north = center_lat + 0.015
        south = center_lat - 0.015
        east = center_lon + 0.015
        west = center_lon - 0.015
        
        G = ox.graph_from_bbox(
            bbox=(north, south, east, west),
            network_type="walk",
            simplify=True
        )
        print(f"Red descargada exitosamente: {G.number_of_nodes()} nodos, {G.number_of_edges()} aristas")
        return G
    except Exception as e:
        print(f"Error con graph_from_bbox: {e}")
        raise Exception("No se pudo descargar la red de calles con ningún método")

def extract_nodes(G):
    """
    Extrae todos los nodos del grafo con sus coordenadas.
    Retorna lista de diccionarios con id, lat, lon.
    """
    nodes = []
    for node_id, data in G.nodes(data=True):
        nodes.append({
            "id": str(node_id),
            "lat": data["y"],
            "lon": data["x"],
            "tipo": "interseccion",
            "nombre": data.get("street_count", "") and f"Intersección {len(nodes)+1}" or f"Nodo {len(nodes)+1}"
        })
    return nodes

def extract_edges(G):
    """
    Extrae todas las aristas del grafo con distancias.
    Retorna lista de diccionarios con origen, destino, distancia_m, nombre.
    """
    edges = []
    for u, v, data in G.edges(data=True):
        # Obtener distancia (length en OSMnx está en metros)
        distancia = data.get("length", 0)
        
        # Obtener nombre de la calle si existe
        nombre = data.get("name", "")
        if isinstance(nombre, list):
            nombre = ", ".join(nombre)
        
        edges.append({
            "origen": str(u),
            "destino": str(v),
            "distancia_m": round(distancia, 2),
            "nombre_calle": nombre or "Sin nombre"
        })
    return edges

def assign_schools_to_nodes(nodes, schools):
    """
    Asigna a cada escuela el nodo de la red más cercano usando KDTree.
    """
    # Construir KDTree con las coordenadas de los nodos
    coords = np.array([(n["lat"], n["lon"]) for n in nodes])
    tree = cKDTree(coords)
    
    # Para cada escuela, buscar el nodo más cercano
    # Usamos coordenadas aproximadas basadas en la distribución de la colonia
    # En producción, estas coordenadas vendrían de geocoding de las direcciones
    
    # Coordenadas aproximadas para las escuelas (distribuidas en la colonia)
    school_coords = [
        (16.8750, -99.8850),  # E01
        (16.8720, -99.8800),  # E02
        (16.8680, -99.8820),  # E03
        (16.8700, -99.8780),  # E04
        (16.8660, -99.8850),  # E05
        (16.8730, -99.8870),  # E06
        (16.8640, -99.8800),  # E07
        (16.8710, -99.8830),  # E08
        (16.8690, -99.8860),  # E09
        (16.8670, -99.8780),  # E10
        (16.8750, -99.8800),  # E11
        (16.8680, -99.8890),  # E12
        (16.8720, -99.8850),  # E13
        (16.8660, -99.8830),  # E14
        (16.8740, -99.8820),  # E15
        (16.8700, -99.8900),  # E16
        (16.8650, -99.8860),  # E17
        (16.8730, -99.8780),  # E18
    ]
    
    schools_with_nodes = []
    for i, school in enumerate(schools):
        # Buscar el nodo más cercano a la posición de la escuela
        _, idx = tree.query(school_coords[i])
        nearest_node = nodes[idx]
        
        schools_with_nodes.append({
            **school,
            "nodo_id": nearest_node["id"],
            "lat": school_coords[i][0],
            "lon": school_coords[i][1]
        })
        
        # Actualizar el nodo para indicar que es entrada de escuela
        nodes[idx]["tipo"] = "escuela"
        nodes[idx]["nombre"] = school["nombre"]
    
    return schools_with_nodes

def save_json(data, filename):
    """Guarda datos en archivo JSON."""
    filepath = DATA_DIR / filename
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Guardado: {filepath}")

def build_graph_data():
    """
    Función principal que construye todos los datos del grafo.
    """
    # 1. Descargar red de calles
    G = download_street_network()
    
    # 2. Extraer nodos
    nodes = extract_nodes(G)
    print(f"Extraídos {len(nodes)} nodos")
    
    # 3. Extraer aristas
    edges = extract_edges(G)
    print(f"Extraídas {len(edges)} aristas")
    
    # 4. Asignar escuelas a nodos
    schools = assign_schools_to_nodes(nodes, ESCUELAS)
    print(f"Asignadas {len(schools)} escuelas a nodos de la red")
    
    # 5. Guardar JSONs
    save_json(schools, "escuelas.json")
    save_json(nodes, "nodos_calles.json")
    save_json(edges, "aristas_calles.json")
    
    # 6. Guardar red completa (para referencia)
    red_completa = {
        "info": {
            "colonia": "Renacimiento",
            "ciudad": "Acapulco de Juárez",
            "estado": "Guerrero",
            "pais": "México",
            "total_nodos": len(nodes),
            "total_aristas": len(edges),
            "total_escuelas": len(schools)
        },
        "escuelas": schools,
        "nodos": nodes,
        "aristas": edges
    }
    save_json(red_completa, "red_completa.json")
    
    print("\n✓ Todos los archivos JSON generados exitosamente")
    return red_completa

if __name__ == "__main__":
    build_graph_data()
