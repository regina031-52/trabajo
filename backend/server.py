"""
Backend para la aplicación de búsqueda de refugios con algoritmo A*.
Usa NetworkX para el grafo y calcula rutas óptimas a escuelas/refugios.
"""

from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import json
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import networkx as nx
import heapq
from math import sqrt, atan2, degrees
import unicodedata

ROOT_DIR = Path(__file__).parent
DATA_DIR = ROOT_DIR / "data"
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI(title="Refugios A* API", description="API para encontrar el refugio más cercano usando A*")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============ MODELOS PYDANTIC ============

class Escuela(BaseModel):
    id: str
    nombre: str
    alias: str = ""
    tipo: str
    unificada: bool
    nodo_id: str
    lat: float
    lon: float

class Nodo(BaseModel):
    id: str
    lat: float
    lon: float
    tipo: str
    nombre: str

class Arista(BaseModel):
    origen: str
    destino: str
    distancia_m: float
    nombre_calle: str

class RutaRequest(BaseModel):
    nodo_origen: str

class NodoCercanoRequest(BaseModel):
    lat: float
    lon: float

class PasoInstruccion(BaseModel):
    paso: int
    instruccion: str
    calle: str
    distancia_m: float
    acumulado_m: float

class RutaResult(BaseModel):
    escuela: Escuela
    distancia_total: float
    tiempo_minutos: float
    ruta_nodos: List[str]
    ruta_coordenadas: List[dict]
    instrucciones: List[PasoInstruccion] = []

class RutaResponse(BaseModel):
    exito: bool
    mensaje: str
    mejor_ruta: Optional[RutaResult] = None
    todas_rutas: List[RutaResult] = []
    sugerencias_emergencia: List[str] = []

# ============ DATOS GLOBALES ============

# Cache de datos cargados
_data_cache = {
    "escuelas": None,
    "nodos": None,
    "aristas": None,
    "grafo": None
}

def load_data():
    """Carga los datos JSON y construye el grafo NetworkX."""
    global _data_cache
    
    if _data_cache["grafo"] is not None:
        return _data_cache
    
    try:
        # Cargar JSONs
        with open(DATA_DIR / "escuelas.json", "r", encoding="utf-8") as f:
            _data_cache["escuelas"] = json.load(f)
        
        with open(DATA_DIR / "nodos_calles.json", "r", encoding="utf-8") as f:
            _data_cache["nodos"] = json.load(f)
        
        with open(DATA_DIR / "aristas_calles.json", "r", encoding="utf-8") as f:
            _data_cache["aristas"] = json.load(f)
        
        # Construir grafo NetworkX
        G = nx.Graph()
        
        # Agregar nodos con atributos
        for nodo in _data_cache["nodos"]:
            G.add_node(
                nodo["id"],
                lat=nodo["lat"],
                lon=nodo["lon"],
                tipo=nodo["tipo"],
                nombre=nodo["nombre"]
            )
        
        # Agregar aristas con pesos (distancia)
        for arista in _data_cache["aristas"]:
            G.add_edge(
                arista["origen"],
                arista["destino"],
                weight=arista["distancia_m"],
                nombre=arista["nombre_calle"]
            )
        
        _data_cache["grafo"] = G
        logger.info(f"Grafo cargado: {G.number_of_nodes()} nodos, {G.number_of_edges()} aristas")
        
    except FileNotFoundError as e:
        logger.error(f"Archivo de datos no encontrado: {e}")
        raise HTTPException(status_code=500, detail="Datos del grafo no disponibles. Ejecute graph_builder.py primero.")
    
    return _data_cache

def heuristic(node1, node2, G):
    """
    Heurística para A*: distancia euclidiana basada en coordenadas.
    Multiplicada por factor para convertir grados a metros aproximados.
    """
    lat1, lon1 = G.nodes[node1]["lat"], G.nodes[node1]["lon"]
    lat2, lon2 = G.nodes[node2]["lat"], G.nodes[node2]["lon"]
    
    # Factor de conversión aproximado (1 grado ≈ 111km en el ecuador)
    lat_factor = 111000
    lon_factor = 111000 * 0.9  # Ajuste por latitud de Acapulco
    
    dlat = (lat2 - lat1) * lat_factor
    dlon = (lon2 - lon1) * lon_factor
    
    return sqrt(dlat**2 + dlon**2)

def astar_path(G, origen, destino):
    """
    Implementación del algoritmo A* para encontrar la ruta más corta.
    Retorna (ruta, distancia_total) o (None, inf) si no hay ruta.
    """
    if origen not in G or destino not in G:
        return None, float('inf')
    
    if origen == destino:
        return [origen], 0
    
    # Cola de prioridad: (f_score, contador, nodo)
    contador = 0
    open_set = [(0, contador, origen)]
    
    # Diccionarios para tracking
    came_from = {}
    g_score = {origen: 0}
    f_score = {origen: heuristic(origen, destino, G)}
    open_set_hash = {origen}
    
    while open_set:
        _, _, current = heapq.heappop(open_set)
        
        if current == destino:
            # Reconstruir ruta
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()
            return path, g_score[destino]
        
        open_set_hash.discard(current)
        
        for neighbor in G.neighbors(current):
            # Obtener peso de la arista
            edge_data = G.get_edge_data(current, neighbor)
            weight = edge_data.get("weight", 1)
            
            tentative_g = g_score[current] + weight
            
            if tentative_g < g_score.get(neighbor, float('inf')):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f = tentative_g + heuristic(neighbor, destino, G)
                f_score[neighbor] = f
                
                if neighbor not in open_set_hash:
                    contador += 1
                    heapq.heappush(open_set, (f, contador, neighbor))
                    open_set_hash.add(neighbor)
    
    return None, float('inf')

# ============ ENDPOINTS ============

@api_router.get("/")
async def root():
    """Endpoint raíz de la API."""
    return {"message": "API de Refugios A* - Colonia Renacimiento, Acapulco"}

@api_router.get("/escuelas", response_model=List[Escuela])
async def get_escuelas():
    """Obtiene la lista de todas las escuelas/refugios."""
    data = load_data()
    return data["escuelas"]

@api_router.get("/nodos", response_model=List[Nodo])
async def get_nodos():
    """Obtiene la lista de todos los nodos de la red."""
    data = load_data()
    return data["nodos"]

@api_router.get("/aristas", response_model=List[Arista])
async def get_aristas():
    """Obtiene la lista de todas las aristas de la red."""
    data = load_data()
    return data["aristas"]

@api_router.get("/grafo/stats")
async def get_grafo_stats():
    """Obtiene estadísticas del grafo."""
    data = load_data()
    G = data["grafo"]
    return {
        "total_nodos": G.number_of_nodes(),
        "total_aristas": G.number_of_edges(),
        "total_escuelas": len(data["escuelas"]),
        "conectado": nx.is_connected(G)
    }

def get_bearing(lat1, lon1, lat2, lon2):
    """Calcula el ángulo de dirección entre dos puntos (en grados, 0=norte)."""
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    angle = degrees(atan2(dlon, dlat))
    return angle % 360

def get_turn_direction(bearing_prev, bearing_next):
    """Determina la dirección del giro entre dos segmentos."""
    diff = (bearing_next - bearing_prev + 360) % 360
    if diff < 30 or diff > 330:
        return "Continua recto"
    elif 30 <= diff < 150:
        return "Gira a la derecha"
    elif 150 <= diff <= 210:
        return "Da vuelta"
    else:
        return "Gira a la izquierda"

def generate_instructions(ruta_nodos, G, nodos_dict):
    """
    Genera instrucciones paso a paso para la ruta.
    Agrupa segmentos de la misma calle en un solo paso.
    """
    if len(ruta_nodos) < 2:
        return []

    instrucciones = []
    acumulado = 0
    paso_num = 0

    # Recorrer pares de nodos en la ruta
    calle_actual = None
    dist_calle = 0
    paso_inicio_idx = 0

    for i in range(len(ruta_nodos) - 1):
        n1 = ruta_nodos[i]
        n2 = ruta_nodos[i + 1]
        edge = G.get_edge_data(n1, n2)
        if not edge:
            continue

        nombre_calle = edge.get("nombre", "Sin nombre")
        dist_seg = edge.get("weight", 0)

        if calle_actual is None:
            # Primer segmento
            calle_actual = nombre_calle
            dist_calle = dist_seg
            paso_inicio_idx = i
        elif nombre_calle == calle_actual:
            # Misma calle, acumular distancia
            dist_calle += dist_seg
        else:
            # Cambio de calle: generar instrucción del tramo anterior
            paso_num += 1
            acumulado += dist_calle

            # Calcular giro si hay suficientes puntos
            if i >= 2:
                p0 = nodos_dict[ruta_nodos[i - 2]]
                p1 = nodos_dict[ruta_nodos[i - 1]]
                p2 = nodos_dict[ruta_nodos[i]]
                bearing_prev = get_bearing(p0["lat"], p0["lon"], p1["lat"], p1["lon"])
                bearing_next = get_bearing(p1["lat"], p1["lon"], p2["lat"], p2["lon"])
                giro = get_turn_direction(bearing_prev, bearing_next)
            else:
                giro = "Camina por"

            if paso_num == 1:
                texto = f"Sal caminando por {calle_actual} ({round(dist_calle)} m)"
            else:
                texto = f"{giro} hacia {nombre_calle} (recorriste {round(dist_calle)} m por {calle_actual})"

            instrucciones.append(PasoInstruccion(
                paso=paso_num,
                instruccion=texto,
                calle=calle_actual,
                distancia_m=round(dist_calle, 1),
                acumulado_m=round(acumulado, 1)
            ))

            calle_actual = nombre_calle
            dist_calle = dist_seg
            paso_inicio_idx = i

    # Último tramo
    if calle_actual and dist_calle > 0:
        paso_num += 1
        acumulado += dist_calle
        instrucciones.append(PasoInstruccion(
            paso=paso_num,
            instruccion=f"Continua por {calle_actual} hasta llegar al refugio ({round(dist_calle)} m)",
            calle=calle_actual,
            distancia_m=round(dist_calle, 1),
            acumulado_m=round(acumulado, 1)
        ))

    # Paso final
    paso_num += 1
    instrucciones.append(PasoInstruccion(
        paso=paso_num,
        instruccion="Has llegado al refugio",
        calle="Destino",
        distancia_m=0,
        acumulado_m=round(acumulado, 1)
    ))

    return instrucciones

SUGERENCIAS_EMERGENCIA = [
    "Agua embotellada (al menos 3 litros por persona)",
    "Documentos importantes en bolsa impermeable (INE, CURP, actas)",
    "Botiquin de primeros auxilios",
    "Linterna con pilas extra",
    "Radio portatil de pilas",
    "Alimentos no perecederos (enlatados, barras, galletas)",
    "Medicamentos personales (si aplica)",
    "Ropa extra y cobija ligera",
    "Cargador portatil para celular",
    "Silbato de emergencia",
    "Dinero en efectivo (billetes y monedas)",
    "Copia de llaves de casa",
    "Articulos de higiene basicos (papel, jabon, gel antibacterial)",
    "Mascarilla o cubrebocas",
    "Bolsas de plastico (para proteger documentos)"
]

@api_router.post("/calcular-ruta", response_model=RutaResponse)
async def calcular_ruta(request: RutaRequest):
    """
    Calcula la ruta más corta desde el nodo origen a todas las escuelas
    usando el algoritmo A*, y retorna la escuela más cercana con instrucciones.
    """
    data = load_data()
    G = data["grafo"]
    escuelas = data["escuelas"]
    nodos_dict = {n["id"]: n for n in data["nodos"]}

    if request.nodo_origen not in G:
        raise HTTPException(status_code=400, detail=f"Nodo origen '{request.nodo_origen}' no existe en el grafo")

    todas_rutas = []

    for escuela in escuelas:
        nodo_destino = escuela["nodo_id"]
        ruta, distancia = astar_path(G, request.nodo_origen, nodo_destino)

        if ruta:
            ruta_coords = []
            for nodo_id in ruta:
                if nodo_id in nodos_dict:
                    nodo = nodos_dict[nodo_id]
                    ruta_coords.append({
                        "id": nodo_id,
                        "lat": nodo["lat"],
                        "lon": nodo["lon"]
                    })

            tiempo_min = distancia / 83.33
            instrucciones = generate_instructions(ruta, G, nodos_dict)

            todas_rutas.append(RutaResult(
                escuela=Escuela(**escuela),
                distancia_total=round(distancia, 2),
                tiempo_minutos=round(tiempo_min, 1),
                ruta_nodos=ruta,
                ruta_coordenadas=ruta_coords,
                instrucciones=instrucciones
            ))

    if not todas_rutas:
        return RutaResponse(
            exito=False,
            mensaje="No se encontro ruta a ninguna escuela",
            todas_rutas=[]
        )

    todas_rutas.sort(key=lambda r: r.distancia_total)
    mejor_ruta = todas_rutas[0]

    return RutaResponse(
        exito=True,
        mensaje=f"Refugio mas cercano: {mejor_ruta.escuela.nombre}",
        mejor_ruta=mejor_ruta,
        todas_rutas=todas_rutas,
        sugerencias_emergencia=SUGERENCIAS_EMERGENCIA
    )

@api_router.post("/nodo-cercano")
async def get_nodo_cercano(request: NodoCercanoRequest):
    """
    Dado un lat/lon (click en mapa), encuentra el nodo de la red más cercano.
    """
    data = load_data()
    nodos = data["nodos"]

    mejor = None
    mejor_dist = float("inf")

    lat_factor = 111000
    lon_factor = 111000 * 0.9

    for nodo in nodos:
        dlat = (nodo["lat"] - request.lat) * lat_factor
        dlon = (nodo["lon"] - request.lon) * lon_factor
        d = sqrt(dlat**2 + dlon**2)
        if d < mejor_dist:
            mejor_dist = d
            mejor = nodo

    if not mejor:
        raise HTTPException(status_code=404, detail="No se encontro nodo cercano")

    return {
        "id": mejor["id"],
        "nombre": mejor["nombre"],
        "lat": mejor["lat"],
        "lon": mejor["lon"],
        "tipo": mejor["tipo"],
        "distancia_m": round(mejor_dist, 1)
    }

@api_router.get("/nodos-seleccionables")
async def get_nodos_seleccionables():
    """
    Obtiene nodos que el usuario puede seleccionar como punto de inicio.
    Incluye nombre legible para mostrar en el selector.
    """
    data = load_data()
    nodos = data["nodos"]
    
    seleccionables = []
    for i, nodo in enumerate(nodos):
        nombre_display = nodo["nombre"]
        if not nombre_display or nombre_display.startswith("Nodo"):
            nombre_display = f"Punto {i+1}"
        
        seleccionables.append({
            "id": nodo["id"],
            "nombre": nombre_display,
            "lat": nodo["lat"],
            "lon": nodo["lon"],
            "tipo": nodo["tipo"]
        })
    
    return seleccionables

@api_router.get("/buscar-nodos")
async def buscar_nodos(q: str = ""):
    """
    Busca nodos por nombre de calle. Tolerante a acentos.
    Retorna los primeros 20 resultados.
    """
    data = load_data()
    nodos = data["nodos"]
    
    if not q or len(q) < 2:
        return []
    
    def normalize(text):
        """Quitar acentos y convertir a minúsculas."""
        nfkd = unicodedata.normalize('NFKD', text)
        return "".join(c for c in nfkd if not unicodedata.combining(c)).lower()
    
    q_norm = normalize(q)
    resultados = []
    
    for nodo in nodos:
        nombre = nodo["nombre"]
        if nombre and q_norm in normalize(nombre):
            resultados.append({
                "id": nodo["id"],
                "nombre": nombre,
                "lat": nodo["lat"],
                "lon": nodo["lon"],
                "tipo": nodo["tipo"]
            })
            if len(resultados) >= 20:
                break
    
    return resultados

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
