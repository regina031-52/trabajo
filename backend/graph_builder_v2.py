"""
Regenerar datos de Ciudad Renacimiento, Acapulco (CP 39715)
Coordenadas: 16.8971, -99.8199
"""
import osmnx as ox
import networkx as nx
import json
from pathlib import Path
from scipy.spatial import cKDTree
import numpy as np

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# Centro de Ciudad Renacimiento
CENTER_LAT = 16.8971
CENTER_LON = -99.8199

# Escuelas con ubicaciones aproximadas basadas en calles descritas por el usuario
ESCUELAS = [
    {
        "id": "E01",
        "nombre": "Esc. Prim. Urb. Mat. Francisco Pérez Ríos",
        "alias": "",
        "tipo": "primaria",
        "unificada": False,
        "zona": "Ignacio Zaragoza / Del Canal",
        "ref_calles": "Ignacio Zaragoza, cerca de Del Canal y Av. Juan R. Escudero",
        "lat_aprox": 16.9005,
        "lon_aprox": -99.8165
    },
    {
        "id": "E02",
        "nombre": "Primaria Benemérito de las Américas",
        "alias": "",
        "tipo": "primaria",
        "unificada": False,
        "zona": "Juan N. Álvarez / Prudencia",
        "ref_calles": "Juan N. Álvarez, cerca de Prudencia y Fuente de San Diego",
        "lat_aprox": 16.8990,
        "lon_aprox": -99.8175
    },
    {
        "id": "E03",
        "nombre": "Primaria Ignacio M. Altamirano / Estefanía Castañeda",
        "alias": "Ignacio M. Altamirano; Estefanía Castañeda",
        "tipo": "primaria",
        "unificada": True,
        "zona": "Oasis III",
        "ref_calles": "Zona Oasis III, cerca de Central, Oasis II y Juan N. Álvarez",
        "lat_aprox": 16.8965,
        "lon_aprox": -99.8155
    },
    {
        "id": "E04",
        "nombre": "Plantel Adolfo López Mateos",
        "alias": "Escuela Primaria Adolfo López Mateos; Esc. Prim. Urb. Vesp. Lic. Adolfo López Mateos",
        "tipo": "primaria",
        "unificada": True,
        "zona": "Carlos A. Carrillo / Oinalá / Francisco I. Madero",
        "ref_calles": "Carlos A. Carrillo, cerca de Oinalá y Francisco I. Madero",
        "lat_aprox": 16.8955,
        "lon_aprox": -99.8185
    },
    {
        "id": "E05",
        "nombre": "Jardín de Niños Moisés Guevara",
        "alias": "",
        "tipo": "jardin",
        "unificada": False,
        "zona": "Carlos A. Carrillo / Oinalá / Ayahualco",
        "ref_calles": "Carlos A. Carrillo, cerca de Oinalá y Ayahualco",
        "lat_aprox": 16.8948,
        "lon_aprox": -99.8195
    },
    {
        "id": "E06",
        "nombre": "Escuela Primaria Francisco Sarabia",
        "alias": "",
        "tipo": "primaria",
        "unificada": False,
        "zona": "Canal del Arroyo",
        "ref_calles": "Canal del Arroyo, entre Ayahualco y Amayaltepec",
        "lat_aprox": 16.8935,
        "lon_aprox": -99.8210
    },
    {
        "id": "E07",
        "nombre": "Escuela Primaria Rural Federal Jaime...",
        "alias": "",
        "tipo": "primaria",
        "unificada": False,
        "zona": "Canal del Arroyo",
        "ref_calles": "Canal del Arroyo, cerca de Amayaltepec y And. Acatitlán",
        "lat_aprox": 16.8925,
        "lon_aprox": -99.8225
    },
    {
        "id": "E08",
        "nombre": "Primaria 7",
        "alias": "",
        "tipo": "primaria",
        "unificada": False,
        "zona": "Cuauhtémoc / Ignacio Chávez",
        "ref_calles": "Cuauhtémoc, cerca de Ignacio Chávez y Mina del Chiquihuite",
        "lat_aprox": 16.8980,
        "lon_aprox": -99.8210
    },
    {
        "id": "E09",
        "nombre": "Escuela Primaria Urbana Turno Matutino Raúl Isidro Burgos",
        "alias": "",
        "tipo": "primaria",
        "unificada": False,
        "zona": "Cerro del Zical / Eje Central",
        "ref_calles": "Cerro del Zical, cerca de Tepetlixpa y Eje Central Vicente Guerrero",
        "lat_aprox": 16.8945,
        "lon_aprox": -99.8140
    },
    {
        "id": "E10",
        "nombre": "Escuela Prim. Raúl Isidro Burgos",
        "alias": "",
        "tipo": "primaria",
        "unificada": False,
        "zona": "Cerro del Capire / Eje Central",
        "ref_calles": "Cerro del Capire y Eje Central Vicente Guerrero",
        "lat_aprox": 16.8935,
        "lon_aprox": -99.8130
    },
    {
        "id": "E11",
        "nombre": "Plantel Jaime Torres Bodet No. 4 / Antonio I. Delgado",
        "alias": "Escuela Primaria Jaime Torres Bodet No. 4; Escuela Primaria Vespertina Antonio I. Delgado",
        "tipo": "primaria",
        "unificada": True,
        "zona": "Osa Mayor / Río Yolotla",
        "ref_calles": "Osa Mayor, cerca de Río Yolotla",
        "lat_aprox": 16.8915,
        "lon_aprox": -99.8160
    },
    {
        "id": "E12",
        "nombre": "Escuela Primaria Turno Matutino Gabriela Mistral",
        "alias": "",
        "tipo": "primaria",
        "unificada": False,
        "zona": "Valerio Trujano / Laguna Platanar",
        "ref_calles": "Valerio Trujano, Mixtepec y Laguna Platanar",
        "lat_aprox": 16.8920,
        "lon_aprox": -99.8195
    },
    {
        "id": "E13",
        "nombre": "Escuela Primaria Urbana Matutina Lázaro Cárdenas",
        "alias": "",
        "tipo": "primaria",
        "unificada": False,
        "zona": "Lázaro Cárdenas / Solidaridad",
        "ref_calles": "Lázaro Cárdenas, cerca de Solidaridad y 2 de Marzo",
        "lat_aprox": 16.8900,
        "lon_aprox": -99.8235
    },
    {
        "id": "E14",
        "nombre": "Colegio Rodolfo Neri Vela",
        "alias": "",
        "tipo": "colegio",
        "unificada": False,
        "zona": "And. Lucero / Valerio Trujano",
        "ref_calles": "And. Lucero, Valerio Trujano y Mixtepec",
        "lat_aprox": 16.8910,
        "lon_aprox": -99.8205
    },
    {
        "id": "E15",
        "nombre": "Centro de Estudios Tecnológicos Industrial y de Servicios núm. 90 Julián Blanco Jiménez",
        "alias": "CETis 90 Julián Blanco Jiménez",
        "tipo": "cets",
        "unificada": False,
        "zona": "Área educativa poniente",
        "ref_calles": "Zona educativa cerca de Lázaro Cárdenas, Solidaridad y 2 de Marzo",
        "lat_aprox": 16.8895,
        "lon_aprox": -99.8250
    },
    {
        "id": "E16",
        "nombre": "Escuela Secundaria Técnica 68 Renacimiento",
        "alias": "",
        "tipo": "secundaria",
        "unificada": False,
        "zona": "Área educativa poniente",
        "ref_calles": "Franja educativa de Lázaro Cárdenas / Solidaridad / 2 de Marzo",
        "lat_aprox": 16.8890,
        "lon_aprox": -99.8260
    },
    {
        "id": "E17",
        "nombre": "Escuela Secundaria General N. 49 Margarito Damián Vargas",
        "alias": "",
        "tipo": "secundaria",
        "unificada": False,
        "zona": "Alta Laja / Olímpica",
        "ref_calles": "Alta Laja y Olímpica",
        "lat_aprox": 16.8875,
        "lon_aprox": -99.8180
    },
    {
        "id": "E18",
        "nombre": "Desarrollo Infantil y Juvenil Renacimiento A.C.",
        "alias": "",
        "tipo": "centro_educativo",
        "unificada": False,
        "zona": "Av. Juan R. Escudero",
        "ref_calles": "Av. Juan R. Escudero y Nicolás Bravo",
        "lat_aprox": 16.8995,
        "lon_aprox": -99.8190
    },
]


def download_network():
    """Descarga la red peatonal de Ciudad Renacimiento."""
    print(f"Descargando red de Ciudad Renacimiento ({CENTER_LAT}, {CENTER_LON})...")

    try:
        print("Método 1: graph_from_point con radio 2000m...")
        G = ox.graph_from_point(
            center_point=(CENTER_LAT, CENTER_LON),
            dist=2000,
            network_type="walk",
            simplify=True
        )
        print(f"OK: {G.number_of_nodes()} nodos, {G.number_of_edges()} aristas")
        return G
    except Exception as e:
        print(f"Error: {e}")

    try:
        print("Método 2: graph_from_address...")
        G = ox.graph_from_address(
            address="Ciudad Renacimiento, Acapulco de Juárez, Guerrero, México",
            dist=2000,
            network_type="walk",
            simplify=True
        )
        print(f"OK: {G.number_of_nodes()} nodos, {G.number_of_edges()} aristas")
        return G
    except Exception as e:
        print(f"Error: {e}")

    try:
        print("Método 3: graph_from_bbox...")
        G = ox.graph_from_bbox(
            bbox=(CENTER_LAT + 0.02, CENTER_LAT - 0.02,
                  CENTER_LON + 0.02, CENTER_LON - 0.02),
            network_type="walk",
            simplify=True
        )
        print(f"OK: {G.number_of_nodes()} nodos, {G.number_of_edges()} aristas")
        return G
    except Exception as e:
        print(f"Error: {e}")
        raise Exception("No se pudo descargar la red")


def extract_nodes(G):
    nodes = []
    for node_id, data in G.nodes(data=True):
        nodes.append({
            "id": str(node_id),
            "lat": data["y"],
            "lon": data["x"],
            "tipo": "interseccion",
            "nombre": f"Nodo {len(nodes)+1}"
        })
    return nodes


def extract_edges(G):
    edges = []
    for u, v, data in G.edges(data=True):
        distancia = data.get("length", 0)
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


def enrich_node_names(nodes, edges, escuelas):
    """Asigna nombres de calles reales a los nodos."""
    from collections import defaultdict

    nodo_calles = defaultdict(set)
    for a in edges:
        nombre = a["nombre_calle"]
        if nombre and nombre != "Sin nombre":
            for parte in nombre.split(","):
                parte = parte.strip()
                if parte:
                    nodo_calles[a["origen"]].add(parte)
                    nodo_calles[a["destino"]].add(parte)

    nodos_escuela = {esc["nodo_id"]: esc["nombre"] for esc in escuelas}

    # Construir adyacencia para BFS
    adj = defaultdict(set)
    for a in edges:
        adj[a["origen"]].add(a["destino"])
        adj[a["destino"]].add(a["origen"])

    nodos_dict = {n["id"]: n for n in nodes}
    sin_nombre_count = 0

    for nodo in nodes:
        nid = nodo["id"]
        if nid in nodos_escuela:
            nodo["nombre"] = nodos_escuela[nid]
            nodo["tipo"] = "escuela"
            continue

        calles = nodo_calles.get(nid, set())
        if calles:
            calles_list = sorted(calles)
            nodo["nombre"] = f"{calles_list[0]} / {calles_list[1]}" if len(calles_list) >= 2 else calles_list[0]
        else:
            # BFS para encontrar vecino con nombre
            encontrado = False
            visitados = {nid}
            cola = list(adj[nid])
            for _ in range(3):
                siguiente = []
                for vecino in cola:
                    if vecino in visitados:
                        continue
                    visitados.add(vecino)
                    vc = nodo_calles.get(vecino, set())
                    if vc:
                        nodo["nombre"] = f"Cerca de {sorted(vc)[0]}"
                        encontrado = True
                        break
                    siguiente.extend(adj[vecino])
                if encontrado:
                    break
                cola = siguiente

            if not encontrado:
                sin_nombre_count += 1
                nodo["nombre"] = f"Punto {sin_nombre_count}"

    return nodes


def assign_schools(nodes, escuelas_raw):
    """Asigna cada escuela al nodo más cercano."""
    coords = np.array([(n["lat"], n["lon"]) for n in nodes])
    tree = cKDTree(coords)

    escuelas = []
    for esc in escuelas_raw:
        _, idx = tree.query([esc["lat_aprox"], esc["lon_aprox"]])
        nearest = nodes[idx]

        escuelas.append({
            "id": esc["id"],
            "nombre": esc["nombre"],
            "alias": esc["alias"],
            "tipo": esc["tipo"],
            "unificada": esc["unificada"],
            "nodo_id": nearest["id"],
            "lat": esc["lat_aprox"],
            "lon": esc["lon_aprox"]
        })

        nodes[idx]["tipo"] = "escuela"
        nodes[idx]["nombre"] = esc["nombre"]

    return escuelas


def save_json(data, filename):
    filepath = DATA_DIR / filename
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Guardado: {filepath}")


def main():
    G = download_network()

    nodes = extract_nodes(G)
    edges = extract_edges(G)
    print(f"Nodos: {len(nodes)}, Aristas: {len(edges)}")

    escuelas = assign_schools(nodes, ESCUELAS)
    nodes = enrich_node_names(nodes, edges, escuelas)

    con_nombre = sum(1 for n in nodes if not n["nombre"].startswith("Punto"))
    print(f"Nodos con nombre: {con_nombre}/{len(nodes)}")

    save_json(escuelas, "escuelas.json")
    save_json(nodes, "nodos_calles.json")
    save_json(edges, "aristas_calles.json")
    save_json({
        "info": {
            "colonia": "Ciudad Renacimiento",
            "ciudad": "Acapulco de Juárez",
            "estado": "Guerrero",
            "cp": "39715",
            "centro_lat": CENTER_LAT,
            "centro_lon": CENTER_LON,
            "total_nodos": len(nodes),
            "total_aristas": len(edges),
            "total_escuelas": len(escuelas)
        },
        "escuelas": escuelas,
        "nodos": nodes,
        "aristas": edges
    }, "red_completa.json")

    print("\nTodos los archivos generados correctamente")


if __name__ == "__main__":
    main()
