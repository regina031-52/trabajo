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
from math import sqrt
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

class RutaResult(BaseModel):
    escuela: Escuela
    distancia_total: float
    tiempo_minutos: float
    ruta_nodos: List[str]
    ruta_coordenadas: List[dict]

class RutaResponse(BaseModel):
    exito: bool
    mensaje: str
    mejor_ruta: Optional[RutaResult] = None
    todas_rutas: List[RutaResult] = []

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

@api_router.post("/calcular-ruta", response_model=RutaResponse)
async def calcular_ruta(request: RutaRequest):
    """
    Calcula la ruta más corta desde el nodo origen a todas las escuelas
    usando el algoritmo A*, y retorna la escuela más cercana.
    """
    data = load_data()
    G = data["grafo"]
    escuelas = data["escuelas"]
    nodos_dict = {n["id"]: n for n in data["nodos"]}
    
    # Validar nodo origen
    if request.nodo_origen not in G:
        raise HTTPException(status_code=400, detail=f"Nodo origen '{request.nodo_origen}' no existe en el grafo")
    
    # Calcular ruta a cada escuela
    todas_rutas = []
    
    for escuela in escuelas:
        nodo_destino = escuela["nodo_id"]
        
        # Ejecutar A*
        ruta, distancia = astar_path(G, request.nodo_origen, nodo_destino)
        
        if ruta:
            # Obtener coordenadas de la ruta
            ruta_coords = []
            for nodo_id in ruta:
                if nodo_id in nodos_dict:
                    nodo = nodos_dict[nodo_id]
                    ruta_coords.append({
                        "id": nodo_id,
                        "lat": nodo["lat"],
                        "lon": nodo["lon"]
                    })
            
            # Calcular tiempo estimado (velocidad promedio caminando: 5 km/h = 83.33 m/min)
            tiempo_min = distancia / 83.33
            
            todas_rutas.append(RutaResult(
                escuela=Escuela(**escuela),
                distancia_total=round(distancia, 2),
                tiempo_minutos=round(tiempo_min, 1),
                ruta_nodos=ruta,
                ruta_coordenadas=ruta_coords
            ))
    
    if not todas_rutas:
        return RutaResponse(
            exito=False,
            mensaje="No se encontró ruta a ninguna escuela",
            todas_rutas=[]
        )
    
    # Ordenar por distancia y obtener la mejor
    todas_rutas.sort(key=lambda r: r.distancia_total)
    mejor_ruta = todas_rutas[0]
    
    return RutaResponse(
        exito=True,
        mensaje=f"Refugio más cercano: {mejor_ruta.escuela.nombre}",
        mejor_ruta=mejor_ruta,
        todas_rutas=todas_rutas
    )

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
