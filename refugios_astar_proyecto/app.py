#!/usr/bin/env python3
"""
================================================================================
  REFUGIOS A* - Aplicación Web con Flask
  Ciudad Renacimiento, Acapulco de Juárez, Guerrero (CP 39715)
  
  Encuentra el refugio (escuela) más cercano usando el algoritmo A*
  con datos reales de calles de OpenStreetMap.
  
  CÓMO EJECUTAR:
    1. pip install flask networkx
    2. python app.py
    3. Abrir en navegador: http://localhost:5000
  
  ARCHIVOS NECESARIOS:
    app.py                      ← este archivo
    data/escuelas.json          ← 19 refugios verificados
    data/nodos_calles.json      ← 8,558 nodos de calles (de OpenStreetMap)
    data/aristas_calles.json    ← 23,332 aristas/conexiones entre calles
================================================================================
"""

# ============================================================
# IMPORTACIONES
# ============================================================
# Flask: framework web ligero para Python (crea el servidor)
from flask import Flask, jsonify, request, render_template_string

# json: para leer los archivos de datos (.json)
import json

# pathlib: para manejar rutas de archivos de forma segura
from pathlib import Path

# heapq: cola de prioridad, esencial para el algoritmo A*
import heapq

# math: funciones matemáticas (raíz cuadrada, arco tangente, etc.)
from math import sqrt, atan2, degrees

# unicodedata: para normalizar texto (quitar acentos en búsquedas)
import unicodedata

# networkx: librería de grafos, usada para modelar la red de calles
import networkx as nx


# ============================================================
# CONFIGURACIÓN DE LA APP FLASK
# ============================================================
# Crear la aplicación Flask
app = Flask(__name__)

# Directorio donde están los archivos JSON de datos
DATA_DIR = Path(__file__).parent / "data"


# ============================================================
# CARGA DE DATOS
# ============================================================
# Variables globales donde se guardan los datos cargados
NODOS = []      # Lista de todos los nodos (intersecciones de calles)
ARISTAS = []    # Lista de todas las aristas (calles que conectan nodos)
ESCUELAS = []   # Lista de los 19 refugios/escuelas
GRAFO = None    # El grafo de NetworkX (la red de calles)
NODOS_DICT = {} # Diccionario rápido: {id_nodo: datos_del_nodo}


def cargar_datos():
    """
    Lee los 3 archivos JSON y construye el grafo de NetworkX.
    
    Esta función se ejecuta UNA VEZ al iniciar la aplicación.
    Carga:
      - nodos_calles.json: cada intersección con su latitud/longitud
      - aristas_calles.json: cada calle con origen, destino y distancia
      - escuelas.json: los 19 refugios con sus coordenadas verificadas
    """
    global NODOS, ARISTAS, ESCUELAS, GRAFO, NODOS_DICT
    
    # Leer los archivos JSON
    with open(DATA_DIR / "nodos_calles.json", "r", encoding="utf-8") as f:
        NODOS = json.load(f)
    
    with open(DATA_DIR / "aristas_calles.json", "r", encoding="utf-8") as f:
        ARISTAS = json.load(f)
    
    with open(DATA_DIR / "escuelas.json", "r", encoding="utf-8") as f:
        ESCUELAS = json.load(f)
    
    # Crear diccionario de nodos para acceso rápido por ID
    # Esto permite buscar un nodo por su ID en O(1) en vez de O(n)
    NODOS_DICT = {n["id"]: n for n in NODOS}
    
    # ---- CONSTRUIR EL GRAFO CON NETWORKX ----
    # Un grafo es una estructura de datos con:
    #   - Nodos: puntos (intersecciones de calles)
    #   - Aristas: conexiones entre nodos (calles), con peso (distancia en metros)
    GRAFO = nx.Graph()
    
    # Agregar cada nodo al grafo con sus atributos (coordenadas, nombre)
    for nodo in NODOS:
        GRAFO.add_node(
            nodo["id"],           # ID único del nodo
            lat=nodo["lat"],      # Latitud (coordenada Y)
            lon=nodo["lon"],      # Longitud (coordenada X)
            nombre=nodo["nombre"],# Nombre de la calle/intersección
            tipo=nodo["tipo"]     # Tipo: "interseccion" o "escuela"
        )
    
    # Agregar cada arista (calle) al grafo
    for arista in ARISTAS:
        GRAFO.add_edge(
            arista["origen"],              # Nodo de inicio
            arista["destino"],             # Nodo de fin
            weight=arista["distancia_m"],  # Peso = distancia en metros
            nombre=arista["nombre_calle"]  # Nombre de la calle
        )
    
    print(f"Datos cargados: {GRAFO.number_of_nodes()} nodos, "
          f"{GRAFO.number_of_edges()} aristas, {len(ESCUELAS)} refugios")


# ============================================================
# ALGORITMO A* (A-ESTRELLA)
# ============================================================
# A* es un algoritmo de búsqueda de ruta óptima que combina:
#   - g(n): costo real desde el origen hasta el nodo n
#   - h(n): estimación (heurística) del costo desde n hasta el destino
#   - f(n) = g(n) + h(n): costo total estimado
# 
# Siempre expande el nodo con menor f(n), lo que garantiza
# encontrar la ruta más corta si la heurística es admisible
# (nunca sobreestima el costo real).

def heuristica(nodo_a, nodo_b):
    """
    Calcula la distancia en línea recta entre dos nodos (en metros).
    
    Esta es la HEURÍSTICA del algoritmo A*. Usamos la distancia
    euclidiana entre las coordenadas geográficas.
    
    La heurística debe ser ADMISIBLE: nunca puede sobreestimar
    la distancia real. La línea recta siempre es menor o igual
    que cualquier camino por calles, así que es admisible.
    
    Conversión de grados a metros:
      - 1 grado de latitud ≈ 111,000 metros
      - 1 grado de longitud ≈ 99,900 metros (en la latitud de Acapulco)
    """
    n1 = NODOS_DICT[nodo_a]
    n2 = NODOS_DICT[nodo_b]
    
    # Convertir diferencia de coordenadas a metros
    delta_lat = (n2["lat"] - n1["lat"]) * 111000    # Diferencia en latitud → metros
    delta_lon = (n2["lon"] - n1["lon"]) * 99900     # Diferencia en longitud → metros
    
    # Distancia euclidiana (teorema de Pitágoras)
    return sqrt(delta_lat**2 + delta_lon**2)


def algoritmo_astar(nodo_origen, nodo_destino):
    """
    Implementación del algoritmo A* para encontrar la ruta más corta.
    
    Parámetros:
        nodo_origen: ID del nodo donde está el usuario
        nodo_destino: ID del nodo del refugio
    
    Retorna:
        (lista_de_nodos, distancia_total) si encontró ruta
        (None, infinito) si no hay ruta
    
    CÓMO FUNCIONA A*:
    1. Empezamos en el nodo origen
    2. Miramos todos los vecinos y calculamos f = g + h para cada uno
    3. Elegimos el vecino con menor f (usando cola de prioridad)
    4. Repetimos hasta llegar al destino
    5. Reconstruimos la ruta siguiendo los "padres" de cada nodo
    """
    # Verificar que ambos nodos existan en el grafo
    if nodo_origen not in GRAFO or nodo_destino not in GRAFO:
        return None, float('inf')
    
    # Caso especial: origen y destino son el mismo nodo
    if nodo_origen == nodo_destino:
        return [nodo_origen], 0
    
    # ---- ESTRUCTURAS DE DATOS DEL ALGORITMO ----
    
    # Cola de prioridad (min-heap): siempre extraemos el nodo con menor f
    # Cada elemento es una tupla: (f_score, contador, nodo_id)
    # El contador evita problemas cuando dos nodos tienen el mismo f
    contador = 0
    cola_prioridad = [(0, contador, nodo_origen)]
    
    # Diccionario de "padres": para reconstruir la ruta al final
    # padre[B] = A significa "llegamos a B desde A"
    padre = {}
    
    # g_score[n] = costo real acumulado desde el origen hasta n
    g_score = {nodo_origen: 0}
    
    # Conjunto de nodos en la cola (para verificación rápida)
    en_cola = {nodo_origen}
    
    # ---- BUCLE PRINCIPAL DE A* ----
    while cola_prioridad:
        # Extraer el nodo con menor f_score de la cola
        f_actual, _, nodo_actual = heapq.heappop(cola_prioridad)
        
        # ¿Llegamos al destino? → Reconstruir y retornar la ruta
        if nodo_actual == nodo_destino:
            ruta = [nodo_actual]
            while nodo_actual in padre:
                nodo_actual = padre[nodo_actual]
                ruta.append(nodo_actual)
            ruta.reverse()  # La ruta se construyó al revés
            return ruta, g_score[nodo_destino]
        
        en_cola.discard(nodo_actual)
        
        # Explorar todos los VECINOS del nodo actual
        # (vecino = nodo conectado por una calle)
        for vecino in GRAFO.neighbors(nodo_actual):
            # Obtener el peso (distancia) de la arista actual → vecino
            datos_arista = GRAFO.get_edge_data(nodo_actual, vecino)
            distancia_arista = datos_arista["weight"]
            
            # Calcular g tentativo: costo acumulado si vamos por este camino
            g_tentativo = g_score[nodo_actual] + distancia_arista
            
            # ¿Este camino es MEJOR que el que ya conocíamos?
            if g_tentativo < g_score.get(vecino, float('inf')):
                # ¡Sí! Actualizamos
                padre[vecino] = nodo_actual
                g_score[vecino] = g_tentativo
                
                # f = g + h (costo real + estimación al destino)
                f_score = g_tentativo + heuristica(vecino, nodo_destino)
                
                # Agregar a la cola si no está
                if vecino not in en_cola:
                    contador += 1
                    heapq.heappush(cola_prioridad, (f_score, contador, vecino))
                    en_cola.add(vecino)
    
    # Si llegamos aquí, no hay ruta posible
    return None, float('inf')


# ============================================================
# INSTRUCCIONES PASO A PASO
# ============================================================

def calcular_bearing(nodo_a, nodo_b):
    """
    Calcula el ángulo de dirección entre dos nodos.
    0° = Norte, 90° = Este, 180° = Sur, 270° = Oeste
    """
    n1 = NODOS_DICT[nodo_a]
    n2 = NODOS_DICT[nodo_b]
    angulo = degrees(atan2(n2["lon"] - n1["lon"], n2["lat"] - n1["lat"]))
    return angulo % 360


def determinar_giro(bearing_anterior, bearing_siguiente):
    """
    Compara dos ángulos de dirección para determinar si hay giro.
    Retorna texto descriptivo: "Continúa recto", "Gira a la derecha", etc.
    """
    diferencia = (bearing_siguiente - bearing_anterior + 360) % 360
    
    if diferencia < 30 or diferencia > 330:
        return "Continúa recto"
    elif 30 <= diferencia < 150:
        return "Gira a la derecha"
    elif 150 <= diferencia <= 210:
        return "Da vuelta"
    else:
        return "Gira a la izquierda"


def generar_instrucciones(ruta):
    """
    Genera instrucciones paso a paso para la ruta.
    Agrupa segmentos consecutivos de la misma calle en un solo paso.
    
    Ejemplo de salida:
      Paso 1: Sal caminando por Calle Costa Azul (120 m)
      Paso 2: Gira a la derecha hacia Av. Escudero (340 m)
      Paso 3: Continúa por Calle Nuxco hasta el refugio (85 m)
      Paso 4: ¡Llegaste al refugio!
    """
    if len(ruta) < 2:
        return []
    
    instrucciones = []
    calle_actual = None       # Nombre de la calle por la que vamos
    distancia_calle = 0       # Distancia acumulada en esta calle
    numero_paso = 0
    acumulado_total = 0       # Distancia total recorrida
    
    # Recorrer cada par de nodos consecutivos en la ruta
    for i in range(len(ruta) - 1):
        nodo_a = ruta[i]
        nodo_b = ruta[i + 1]
        
        # Obtener datos de la arista (calle) entre estos dos nodos
        datos = GRAFO.get_edge_data(nodo_a, nodo_b)
        nombre_calle = datos.get("nombre", "Sin nombre") if datos else "Sin nombre"
        distancia = datos.get("weight", 0) if datos else 0
        
        if calle_actual is None:
            # Primera calle de la ruta
            calle_actual = nombre_calle
            distancia_calle = distancia
        elif nombre_calle == calle_actual:
            # Seguimos en la misma calle, acumular distancia
            distancia_calle += distancia
        else:
            # ¡Cambio de calle! Generar instrucción del tramo anterior
            numero_paso += 1
            acumulado_total += distancia_calle
            
            # Determinar si hay giro
            if i >= 2:
                b_prev = calcular_bearing(ruta[i-2], ruta[i-1])
                b_next = calcular_bearing(ruta[i-1], ruta[i])
                giro = determinar_giro(b_prev, b_next)
            else:
                giro = "Camina por"
            
            # Crear texto de la instrucción
            if numero_paso == 1:
                texto = f"Sal caminando por {calle_actual} ({round(distancia_calle)} m)"
            else:
                texto = f"{giro} hacia {nombre_calle} ({round(distancia_calle)} m por {calle_actual})"
            
            instrucciones.append({
                "paso": numero_paso,
                "instruccion": texto,
                "calle": calle_actual,
                "distancia_m": round(distancia_calle, 1),
                "acumulado_m": round(acumulado_total, 1)
            })
            
            # Comenzar nuevo tramo
            calle_actual = nombre_calle
            distancia_calle = distancia
    
    # Último tramo
    if calle_actual and distancia_calle > 0:
        numero_paso += 1
        acumulado_total += distancia_calle
        instrucciones.append({
            "paso": numero_paso,
            "instruccion": f"Continúa por {calle_actual} hasta el refugio ({round(distancia_calle)} m)",
            "calle": calle_actual,
            "distancia_m": round(distancia_calle, 1),
            "acumulado_m": round(acumulado_total, 1)
        })
    
    # Paso final
    numero_paso += 1
    instrucciones.append({
        "paso": numero_paso,
        "instruccion": "¡Llegaste al refugio!",
        "calle": "Destino",
        "distancia_m": 0,
        "acumulado_m": round(acumulado_total, 1)
    })
    
    return instrucciones


# ============================================================
# BÚSQUEDA DE NODOS POR NOMBRE
# ============================================================

def normalizar_texto(texto):
    """
    Quita acentos y convierte a minúsculas para búsqueda tolerante.
    Ejemplo: "Cuauhtémoc" → "cuauhtemoc"
    """
    nfkd = unicodedata.normalize('NFKD', texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower()


def buscar_nodos_por_nombre(consulta):
    """
    Busca nodos cuyo nombre de calle contenga la consulta.
    No necesitas escribir "Calle" ni "Avenida", solo el nombre.
    Tolerante a acentos: "Cuauhtemoc" encuentra "Cuauhtémoc".
    """
    if not consulta or len(consulta) < 2:
        return []
    
    consulta_norm = normalizar_texto(consulta)
    resultados = []
    ids_vistos = set()
    
    # Búsqueda directa en nombres de nodos
    for nodo in NODOS:
        if nodo["nombre"] and consulta_norm in normalizar_texto(nodo["nombre"]):
            if nodo["id"] not in ids_vistos:
                ids_vistos.add(nodo["id"])
                resultados.append(nodo)
                if len(resultados) >= 25:
                    break
    
    # Si hay pocos resultados, buscar quitando prefijos como "Calle", "Avenida"
    if len(resultados) < 10:
        prefijos = ["calle ", "avenida ", "andador ", "privada ",
                     "cerrada ", "cerca de "]
        for nodo in NODOS:
            if nodo["id"] in ids_vistos or not nodo["nombre"]:
                continue
            nombre_norm = normalizar_texto(nodo["nombre"])
            for prefijo in prefijos:
                if nombre_norm.startswith(prefijo) and consulta_norm in nombre_norm[len(prefijo):]:
                    ids_vistos.add(nodo["id"])
                    resultados.append(nodo)
                    break
            if len(resultados) >= 25:
                break
    
    return resultados


# ============================================================
# LISTA DE SUGERENCIAS DE EMERGENCIA
# ============================================================
SUGERENCIAS_EMERGENCIA = [
    "Agua embotellada (al menos 3 litros por persona)",
    "Documentos importantes en bolsa impermeable (INE, CURP, actas)",
    "Botiquín de primeros auxilios",
    "Linterna con pilas extra",
    "Radio portátil de pilas",
    "Alimentos no perecederos (enlatados, barras, galletas)",
    "Medicamentos personales (si aplica)",
    "Ropa extra y cobija ligera",
    "Cargador portátil para celular",
    "Silbato de emergencia",
    "Dinero en efectivo (billetes y monedas)",
    "Copia de llaves de casa",
    "Artículos de higiene (papel, jabón, gel antibacterial)",
    "Mascarilla o cubrebocas",
    "Bolsas de plástico (proteger documentos)",
]


# ============================================================
# RUTAS DE LA API (ENDPOINTS)
# ============================================================
# Estos son los "endpoints" que el frontend llama para obtener datos.
# Flask convierte cada función en una URL accesible por el navegador.

@app.route("/api/escuelas")
def api_escuelas():
    """Retorna la lista de los 19 refugios."""
    return jsonify(ESCUELAS)


@app.route("/api/grafo/stats")
def api_stats():
    """Retorna estadísticas del grafo."""
    return jsonify({
        "total_nodos": GRAFO.number_of_nodes(),
        "total_aristas": GRAFO.number_of_edges(),
        "total_escuelas": len(ESCUELAS),
        "conectado": nx.is_connected(GRAFO)
    })


@app.route("/api/buscar-nodos")
def api_buscar():
    """Busca nodos por nombre de calle."""
    consulta = request.args.get("q", "")
    resultados = buscar_nodos_por_nombre(consulta)
    return jsonify([{
        "id": n["id"], "nombre": n["nombre"],
        "lat": n["lat"], "lon": n["lon"], "tipo": n["tipo"]
    } for n in resultados])


@app.route("/api/nodo-cercano", methods=["POST"])
def api_nodo_cercano():
    """
    Dado un punto lat/lon (click en el mapa), encuentra el nodo más cercano.
    Usa búsqueda lineal con distancia euclidiana.
    """
    datos = request.get_json()
    lat = datos["lat"]
    lon = datos["lon"]
    
    mejor_nodo = None
    mejor_dist = float("inf")
    
    for nodo in NODOS:
        # Distancia euclidiana en metros
        dlat = (nodo["lat"] - lat) * 111000
        dlon = (nodo["lon"] - lon) * 99900
        d = sqrt(dlat**2 + dlon**2)
        if d < mejor_dist:
            mejor_dist = d
            mejor_nodo = nodo
    
    return jsonify({
        "id": mejor_nodo["id"], "nombre": mejor_nodo["nombre"],
        "lat": mejor_nodo["lat"], "lon": mejor_nodo["lon"],
        "tipo": mejor_nodo["tipo"]
    })


@app.route("/api/calcular-ruta", methods=["POST"])
def api_calcular_ruta():
    """
    ENDPOINT PRINCIPAL: calcula la ruta A* desde el nodo origen
    a TODOS los refugios, y retorna el más cercano con instrucciones.
    """
    datos = request.get_json()
    nodo_origen = datos["nodo_origen"]
    
    # Verificar que el nodo existe
    if nodo_origen not in GRAFO:
        return jsonify({"exito": False, "mensaje": "Nodo no encontrado"}), 400
    
    # Calcular ruta A* a CADA refugio
    todas_rutas = []
    
    for escuela in ESCUELAS:
        nodo_destino = escuela["nodo_id"]
        
        # Ejecutar A*
        ruta, distancia = algoritmo_astar(nodo_origen, nodo_destino)
        
        if ruta:
            # Obtener coordenadas de cada nodo en la ruta (para dibujar en el mapa)
            ruta_coords = []
            for nid in ruta:
                if nid in NODOS_DICT:
                    n = NODOS_DICT[nid]
                    ruta_coords.append({"lat": n["lat"], "lon": n["lon"]})
            
            # Tiempo estimado caminando (5 km/h = 83.33 m/min)
            tiempo = distancia / 83.33
            
            # Generar instrucciones paso a paso
            instrucciones = generar_instrucciones(ruta)
            
            todas_rutas.append({
                "escuela": escuela,
                "distancia_total": round(distancia, 2),
                "tiempo_minutos": round(tiempo, 1),
                "ruta_coordenadas": ruta_coords,
                "instrucciones": instrucciones
            })
    
    if not todas_rutas:
        return jsonify({"exito": False, "mensaje": "No se encontró ruta"})
    
    # Ordenar por distancia (el primero es el más cercano)
    todas_rutas.sort(key=lambda r: r["distancia_total"])
    
    return jsonify({
        "exito": True,
        "mensaje": f"Refugio más cercano: {todas_rutas[0]['escuela']['nombre']}",
        "mejor_ruta": todas_rutas[0],
        "todas_rutas": todas_rutas,
        "sugerencias_emergencia": SUGERENCIAS_EMERGENCIA
    })


# ============================================================
# PÁGINA PRINCIPAL (HTML + CSS + JAVASCRIPT)
# ============================================================
# Todo el frontend está en un solo string HTML para simplicidad.
# Usa Leaflet.js para el mapa interactivo.

@app.route("/")
def pagina_principal():
    """Sirve la página HTML principal con el mapa interactivo."""
    return render_template_string(PAGINA_HTML)


# ============================================================
# HTML DE LA APLICACIÓN
# ============================================================
PAGINA_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Refugios A* - Ciudad Renacimiento</title>
    
    <!-- Leaflet CSS: librería de mapas interactivos -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    
    <!-- Fuente tipográfica -->
    <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    
    <style>
        /* ===== ESTILOS GENERALES ===== */
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'DM Sans', sans-serif; background: #F4F5F7; overflow: hidden; }
        
        /* ===== MAPA (ocupa toda la pantalla) ===== */
        #mapa { width: 100vw; height: 100vh; z-index: 0; }
        
        /* ===== PANEL LATERAL (vidrio esmerilado) ===== */
        .panel {
            position: absolute; top: 20px; left: 20px;
            width: 370px; max-height: calc(100vh - 40px);
            background: rgba(255,255,255,0.92);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(0,0,0,0.1);
            border-radius: 16px;
            box-shadow: 0 4px 24px rgba(0,0,0,0.08);
            z-index: 1000; display: flex; flex-direction: column;
            overflow: hidden;
            transition: transform 0.3s ease;
        }
        .panel.oculto { transform: translateX(-400px); }
        .panel-body { padding: 20px; overflow-y: auto; flex: 1; }
        .panel-footer {
            border-top: 1px solid #E2E8F0; padding: 10px 20px;
            background: rgba(248,250,252,0.5);
            display: flex; justify-content: space-between;
            font-size: 11px; color: #94A3B8;
        }
        
        /* ===== BOTÓN TOGGLE PANEL ===== */
        .btn-toggle {
            position: absolute; top: 20px; z-index: 1001;
            background: rgba(255,255,255,0.92); border: 1px solid rgba(0,0,0,0.1);
            border-radius: 12px; padding: 8px 10px; cursor: pointer;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            font-size: 18px; color: #64748B;
            transition: left 0.3s ease;
        }
        .btn-toggle:hover { background: #F1F5F9; }
        
        /* ===== TÍTULO ===== */
        h1 { font-size: 20px; font-weight: 700; color: #1E293B; display: flex; align-items: center; gap: 8px; }
        h1 span { color: #2563EB; }
        .subtitulo { font-size: 12px; color: #94A3B8; margin-top: 4px; }
        
        /* ===== CAMPO DE BÚSQUEDA ===== */
        .search-box {
            position: relative; margin-top: 12px;
        }
        .search-box input {
            width: 100%; padding: 11px 14px 11px 38px;
            border: 1px solid #CBD5E1; border-radius: 10px;
            font-family: 'DM Sans', sans-serif; font-size: 14px;
            outline: none; transition: border-color 0.2s;
        }
        .search-box input:focus { border-color: #2563EB; box-shadow: 0 0 0 3px rgba(37,99,235,0.1); }
        .search-icon { position: absolute; left: 12px; top: 50%; transform: translateY(-50%); color: #94A3B8; }
        
        /* ===== DROPDOWN DE RESULTADOS ===== */
        .dropdown {
            position: absolute; top: 100%; left: 0; right: 0;
            background: white; border: 1px solid #E2E8F0;
            border-radius: 10px; margin-top: 4px; max-height: 240px;
            overflow-y: auto; box-shadow: 0 8px 24px rgba(0,0,0,0.1);
            z-index: 100; display: none;
        }
        .dropdown.visible { display: block; }
        .dropdown-item {
            padding: 10px 14px; cursor: pointer;
            border-bottom: 1px solid #F1F5F9;
            font-size: 13px; color: #334155;
        }
        .dropdown-item:hover { background: #EFF6FF; }
        .dropdown-item small { color: #94A3B8; display: block; margin-top: 2px; font-size: 11px; }
        
        /* ===== BOTONES ===== */
        .btn-gps {
            flex: 1; padding: 8px; border-radius: 8px; border: 1px solid #BAE6FD;
            background: #F0F9FF; color: #0284C7; font-size: 12px; font-weight: 600;
            cursor: pointer; transition: background 0.2s;
        }
        .btn-gps:hover { background: #E0F2FE; }
        .btn-primary {
            width: 100%; padding: 12px; border: none; border-radius: 10px;
            background: #2563EB; color: white; font-size: 14px; font-weight: 600;
            cursor: pointer; transition: all 0.2s; font-family: 'DM Sans', sans-serif;
        }
        .btn-primary:hover { background: #1D4ED8; box-shadow: 0 4px 12px rgba(37,99,235,0.3); }
        .btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
        
        /* ===== RESULTADO ===== */
        .resultado { margin-top: 16px; }
        .route-card {
            background: linear-gradient(135deg, rgba(37,99,235,0.06), rgba(14,165,233,0.04));
            border: 1px solid rgba(37,99,235,0.2); border-radius: 12px; padding: 14px;
        }
        .route-card h3 { font-size: 14px; color: #1E293B; font-weight: 600; margin-top: 4px; }
        .route-card .tipo { font-size: 11px; color: #64748B; text-transform: uppercase; margin-top: 6px;
            display: inline-block; background: #F1F5F9; padding: 2px 8px; border-radius: 4px; }
        .route-card .direccion { font-size: 11px; color: #94A3B8; margin-top: 6px; }
        
        .metricas { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 12px; }
        .metrica {
            background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; padding: 12px;
        }
        .metrica-label { font-family: 'JetBrains Mono', monospace; font-size: 9px;
            text-transform: uppercase; letter-spacing: 0.15em; color: #94A3B8; }
        .metrica-valor { font-family: 'JetBrains Mono', monospace; font-size: 20px;
            font-weight: 600; color: #1E293B; margin-top: 4px; }
        
        /* ===== SECCIONES DESPLEGABLES ===== */
        .toggle-btn {
            width: 100%; padding: 8px; background: none; border: none;
            color: #64748B; font-size: 13px; cursor: pointer;
            display: flex; align-items: center; justify-content: center; gap: 6px;
        }
        .toggle-btn:hover { color: #2563EB; }
        .toggle-btn.emergencia { color: #DC2626; }
        .toggle-btn.emergencia:hover { color: #B91C1C; }
        
        .seccion-contenido { display: none; margin-top: 8px; }
        .seccion-contenido.visible { display: block; }
        
        /* Instrucciones paso a paso */
        .paso { display: flex; gap: 10px; padding: 8px 0; }
        .paso-num {
            width: 22px; height: 22px; border-radius: 50%; flex-shrink: 0;
            display: flex; align-items: center; justify-content: center;
            font-size: 11px; font-weight: 700; font-family: 'JetBrains Mono', monospace;
            background: #F1F5F9; color: #64748B;
        }
        .paso-num.final { background: #16A34A; color: white; }
        .paso-texto { font-size: 13px; color: #475569; line-height: 1.4; }
        .paso-dist { font-size: 11px; color: #94A3B8; font-family: 'JetBrains Mono', monospace; }
        
        /* Kit de emergencia */
        .kit-box {
            background: #FEF2F2; border: 1px solid #FECACA; border-radius: 10px;
            padding: 14px; max-height: 200px; overflow-y: auto;
        }
        .kit-item { font-size: 13px; color: #64748B; padding: 3px 0; display: flex; gap: 6px; }
        .kit-dot { color: #EF4444; flex-shrink: 0; }
        
        /* Lista de refugios */
        .refugio-item {
            display: flex; justify-content: space-between; align-items: center;
            padding: 8px 10px; background: #F8FAFC; border: 1px solid #E2E8F0;
            border-radius: 8px; margin-top: 6px; font-size: 12px;
        }
        .refugio-item .nombre { color: #334155; font-weight: 500; flex: 1; overflow: hidden;
            text-overflow: ellipsis; white-space: nowrap; }
        .refugio-item .dist { color: #2563EB; font-family: 'JetBrains Mono', monospace;
            font-weight: 600; margin-left: 8px; }
        
        /* Leyenda */
        .leyenda {
            position: absolute; bottom: 20px; right: 20px; z-index: 1000;
            background: rgba(255,255,255,0.92); backdrop-filter: blur(20px);
            border: 1px solid rgba(0,0,0,0.1); border-radius: 12px;
            padding: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }
        .leyenda-titulo { font-size: 9px; text-transform: uppercase; letter-spacing: 0.15em;
            color: #94A3B8; margin-bottom: 8px; font-family: 'JetBrains Mono', monospace; }
        .leyenda-item { display: flex; align-items: center; gap: 8px; margin-top: 4px; font-size: 12px; color: #64748B; }
        .leyenda-dot { width: 10px; height: 10px; border-radius: 50%; border: 1.5px solid white; box-shadow: 0 1px 3px rgba(0,0,0,0.2); }
        .leyenda-line { width: 24px; height: 3px; border-radius: 2px; }
        
        /* Tooltips del mapa */
        .school-tooltip { background: white !important; border: 1px solid rgba(220,38,38,0.3) !important;
            border-radius: 6px !important; padding: 3px 8px !important; box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important; }
        .school-tooltip-text { color: #DC2626; font-size: 10px; font-weight: 600; font-family: 'DM Sans', sans-serif; }
        
        .info-vacia { text-align: center; padding: 20px 0; color: #94A3B8; font-size: 13px; }
        .nodo-seleccionado { font-size: 12px; color: #0284C7; margin-top: 6px; }
        .error-msg { background: #FEF2F2; border: 1px solid #FECACA; border-radius: 8px;
            padding: 10px; color: #DC2626; font-size: 13px; margin-top: 12px; }
    </style>
</head>
<body>
    <!-- MAPA -->
    <div id="mapa"></div>
    
    <!-- BOTÓN TOGGLE PANEL -->
    <button class="btn-toggle" id="btnToggle" onclick="togglePanel()">◀</button>
    
    <!-- PANEL LATERAL -->
    <div class="panel" id="panel">
        <div class="panel-body">
            <h1><span>▶</span> Refugios A*</h1>
            <p class="subtitulo">Ciudad Renacimiento, Acapulco</p>
            
            <!-- Búsqueda -->
            <div class="search-box">
                <span class="search-icon">🔍</span>
                <input type="text" id="inputBuscar" placeholder="Escribe tu calle (ej: Escudero, Costa Azul...)"
                    oninput="buscarCalle(this.value)" onfocus="mostrarDropdown()">
                <div class="dropdown" id="dropdown"></div>
            </div>
            
            <!-- GPS y click -->
            <div style="display:flex; gap:8px; align-items:center; margin-top:8px;">
                <button class="btn-gps" onclick="usarGPS()">📍 Usar mi GPS</button>
                <span style="font-size:11px; color:#94A3B8;">o click en mapa</span>
            </div>
            <div class="nodo-seleccionado" id="nodoInfo" style="display:none;"></div>
            
            <!-- Botón calcular -->
            <button class="btn-primary" id="btnCalcular" onclick="calcularRuta()" disabled style="margin-top:12px;">
                Encontrar refugio más cercano
            </button>
            
            <!-- Error -->
            <div class="error-msg" id="error" style="display:none;"></div>
            
            <!-- Resultado -->
            <div class="resultado" id="resultado" style="display:none;"></div>
            
            <!-- Info vacía -->
            <div class="info-vacia" id="infoVacia">
                Escribe tu calle, usa GPS o haz click en el mapa
            </div>
        </div>
        <div class="panel-footer">
            <span id="statNodos">0 puntos</span>
            <span id="statRefugios">0 refugios</span>
            <span>A* Algorithm</span>
        </div>
    </div>
    
    <!-- LEYENDA -->
    <div class="leyenda">
        <div class="leyenda-titulo">Leyenda</div>
        <div class="leyenda-item"><div class="leyenda-dot" style="background:#0EA5E9;"></div> Tu ubicación</div>
        <div class="leyenda-item"><div class="leyenda-dot" style="background:#DC2626;"></div> Refugio</div>
        <div class="leyenda-item"><div class="leyenda-dot" style="background:#16A34A;"></div> Más cercano</div>
        <div class="leyenda-item"><div class="leyenda-line" style="background:#2563EB;"></div> Ruta</div>
    </div>
    
    <!-- Leaflet JS -->
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    
    <script>
    // ===== VARIABLES GLOBALES =====
    const API = "";  // Flask corre en el mismo servidor
    let mapa, nodoSeleccionado = null, marcadorUsuario = null, lineaRuta = null;
    let marcadoresEscuelas = [];
    
    // ===== INICIALIZAR MAPA =====
    mapa = L.map('mapa').setView([16.8971, -99.8199], 15);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap'
    }).addTo(mapa);
    
    // Click en mapa para seleccionar ubicación
    mapa.on('click', function(e) {
        fetch(API + '/api/nodo-cercano', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({lat: e.latlng.lat, lon: e.latlng.lng})
        })
        .then(r => r.json())
        .then(nodo => seleccionarNodo(nodo));
    });
    
    // ===== CARGAR DATOS INICIALES =====
    fetch(API + '/api/escuelas').then(r => r.json()).then(escuelas => {
        escuelas.forEach(esc => {
            let marker = L.circleMarker([esc.lat, esc.lon], {
                radius: 7, fillColor: '#DC2626', color: '#FFF', weight: 2, fillOpacity: 0.9
            }).addTo(mapa);
            marker.bindTooltip(esc.nombre.length > 30 ? esc.nombre.slice(0,28)+'...' : esc.nombre, {
                permanent: true, direction: 'top', offset: [0,-10], className: 'school-tooltip'
            });
            marker.bindPopup('<b style="color:#2563EB">' + esc.nombre + '</b>' +
                (esc.direccion ? '<br><small style="color:#94A3B8">' + esc.direccion + '</small>' : '') +
                '<br><span style="font-size:11px;color:#DC2626;text-transform:uppercase">' + esc.tipo + '</span>');
            marker.escuelaId = esc.id;
            marcadoresEscuelas.push(marker);
        });
    });
    
    fetch(API + '/api/grafo/stats').then(r => r.json()).then(s => {
        document.getElementById('statNodos').textContent = s.total_nodos + ' puntos';
        document.getElementById('statRefugios').textContent = s.total_escuelas + ' refugios';
    });
    
    // ===== FUNCIONES =====
    let timerBusqueda;
    function buscarCalle(texto) {
        clearTimeout(timerBusqueda);
        if (texto.length < 2) { document.getElementById('dropdown').className = 'dropdown'; return; }
        timerBusqueda = setTimeout(() => {
            fetch(API + '/api/buscar-nodos?q=' + encodeURIComponent(texto))
            .then(r => r.json()).then(resultados => {
                let dd = document.getElementById('dropdown');
                if (resultados.length === 0) { dd.className = 'dropdown'; return; }
                dd.innerHTML = resultados.map((n,i) =>
                    '<div class="dropdown-item" onclick="seleccionarDesdeDropdown(' + i + ')">' +
                    n.nombre + '<small>' + (n.tipo === 'escuela' ? 'Refugio' : 'Intersección') + '</small></div>'
                ).join('');
                dd.className = 'dropdown visible';
                window._resultadosBusqueda = resultados;
            });
        }, 300);
    }
    
    function mostrarDropdown() {
        let dd = document.getElementById('dropdown');
        if (dd.innerHTML) dd.className = 'dropdown visible';
    }
    
    function seleccionarDesdeDropdown(idx) {
        let nodo = window._resultadosBusqueda[idx];
        document.getElementById('inputBuscar').value = nodo.nombre;
        document.getElementById('dropdown').className = 'dropdown';
        seleccionarNodo(nodo);
    }
    
    function seleccionarNodo(nodo) {
        nodoSeleccionado = nodo;
        if (marcadorUsuario) mapa.removeLayer(marcadorUsuario);
        marcadorUsuario = L.circleMarker([nodo.lat, nodo.lon], {
            radius: 10, fillColor: '#0EA5E9', color: '#FFF', weight: 3, fillOpacity: 1
        }).addTo(mapa).bindTooltip('Tu ubicación', {permanent:true, direction:'bottom', offset:[0,10]});
        mapa.setView([nodo.lat, nodo.lon], 15);
        document.getElementById('nodoInfo').style.display = 'block';
        document.getElementById('nodoInfo').textContent = '📍 ' + nodo.nombre;
        document.getElementById('inputBuscar').value = nodo.nombre;
        document.getElementById('btnCalcular').disabled = false;
        document.getElementById('error').style.display = 'none';
        document.getElementById('resultado').style.display = 'none';
        document.getElementById('infoVacia').style.display = 'block';
    }
    
    function usarGPS() {
        if (!navigator.geolocation) { mostrarError('Tu navegador no soporta GPS'); return; }
        navigator.geolocation.getCurrentPosition(pos => {
            fetch(API + '/api/nodo-cercano', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({lat: pos.coords.latitude, lon: pos.coords.longitude})
            }).then(r => r.json()).then(nodo => seleccionarNodo(nodo));
        }, err => { mostrarError(err.code === 1 ? 'Permiso GPS denegado' : 'Error GPS'); },
        {enableHighAccuracy: true, timeout: 10000});
    }
    
    function mostrarError(msg) {
        document.getElementById('error').textContent = msg;
        document.getElementById('error').style.display = 'block';
    }
    
    function calcularRuta() {
        if (!nodoSeleccionado) return;
        document.getElementById('btnCalcular').disabled = true;
        document.getElementById('btnCalcular').textContent = 'Calculando...';
        document.getElementById('error').style.display = 'none';
        
        fetch(API + '/api/calcular-ruta', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({nodo_origen: nodoSeleccionado.id})
        })
        .then(r => r.json())
        .then(data => {
            document.getElementById('btnCalcular').disabled = false;
            document.getElementById('btnCalcular').textContent = 'Encontrar refugio más cercano';
            
            if (!data.exito) { mostrarError(data.mensaje); return; }
            
            let m = data.mejor_ruta;
            
            // Dibujar ruta en el mapa
            if (lineaRuta) mapa.removeLayer(lineaRuta);
            lineaRuta = L.polyline(m.ruta_coordenadas.map(c => [c.lat, c.lon]), {
                color: '#2563EB', weight: 5, opacity: 0.85
            }).addTo(mapa);
            
            // Resaltar escuela destino
            marcadoresEscuelas.forEach(mk => {
                if (mk.escuelaId === m.escuela.id) {
                    mk.setStyle({fillColor: '#16A34A', radius: 10});
                } else {
                    mk.setStyle({fillColor: '#DC2626', radius: 7});
                }
            });
            
            // Centrar mapa en la ruta
            let coords = m.ruta_coordenadas;
            let mid = coords[Math.floor(coords.length/2)];
            mapa.setView([mid.lat, mid.lon], 15);
            
            // Mostrar resultado
            let distStr = m.distancia_total >= 1000 ? (m.distancia_total/1000).toFixed(1)+' km' : Math.round(m.distancia_total)+' m';
            let timeStr = m.tiempo_minutos >= 60 ? Math.floor(m.tiempo_minutos/60)+'h '+Math.round(m.tiempo_minutos%60)+'m' : Math.round(m.tiempo_minutos)+' min';
            
            let html = '<div class="route-card">';
            html += '<div style="font-size:9px;color:#94A3B8;text-transform:uppercase;letter-spacing:0.1em;">Refugio más cercano</div>';
            html += '<h3>' + m.escuela.nombre + '</h3>';
            if (m.escuela.direccion) html += '<div class="direccion">' + m.escuela.direccion + '</div>';
            html += '<span class="tipo">' + m.escuela.tipo + '</span></div>';
            
            html += '<div class="metricas">';
            html += '<div class="metrica"><div class="metrica-label">Distancia</div><div class="metrica-valor">' + distStr + '</div></div>';
            html += '<div class="metrica"><div class="metrica-label">Caminando</div><div class="metrica-valor">' + timeStr + '</div></div>';
            html += '</div>';
            
            // Instrucciones
            html += '<button class="toggle-btn" onclick="toggleSeccion(\'instrucciones\')">📋 Ver instrucciones (' + m.instrucciones.length + ' pasos) ▼</button>';
            html += '<div class="seccion-contenido" id="instrucciones">';
            m.instrucciones.forEach(p => {
                let esFinal = p.distancia_m === 0;
                html += '<div class="paso"><div class="paso-num ' + (esFinal?'final':'') + '">' + (esFinal?'✓':p.paso) + '</div>';
                html += '<div><div class="paso-texto">' + p.instruccion + '</div>';
                if (!esFinal) html += '<div class="paso-dist">' + Math.round(p.distancia_m) + 'm · total: ' + Math.round(p.acumulado_m) + 'm</div>';
                html += '</div></div>';
            });
            html += '</div>';
            
            // Kit emergencia
            html += '<button class="toggle-btn emergencia" onclick="toggleSeccion(\'kit\')">🎒 Qué llevar al refugio ▼</button>';
            html += '<div class="seccion-contenido" id="kit"><div class="kit-box">';
            data.sugerencias_emergencia.forEach(s => {
                html += '<div class="kit-item"><span class="kit-dot">●</span>' + s + '</div>';
            });
            html += '</div></div>';
            
            // Todos los refugios
            html += '<button class="toggle-btn" onclick="toggleSeccion(\'todos\')">📋 Ver todos (' + data.todas_rutas.length + ' refugios) ▼</button>';
            html += '<div class="seccion-contenido" id="todos" style="max-height:200px;overflow-y:auto;">';
            data.todas_rutas.forEach((r,i) => {
                let d = r.distancia_total >= 1000 ? (r.distancia_total/1000).toFixed(1)+'km' : Math.round(r.distancia_total)+'m';
                html += '<div class="refugio-item"><span class="nombre">' + (i+1) + '. ' + r.escuela.nombre + '</span>';
                html += '<span class="dist">' + d + '</span></div>';
            });
            html += '</div>';
            
            document.getElementById('resultado').innerHTML = html;
            document.getElementById('resultado').style.display = 'block';
            document.getElementById('infoVacia').style.display = 'none';
        })
        .catch(() => {
            document.getElementById('btnCalcular').disabled = false;
            document.getElementById('btnCalcular').textContent = 'Encontrar refugio más cercano';
            mostrarError('Error al calcular la ruta');
        });
    }
    
    function toggleSeccion(id) {
        let el = document.getElementById(id);
        el.className = el.className.includes('visible') ? 'seccion-contenido' : 'seccion-contenido visible';
    }
    
    function togglePanel() {
        let panel = document.getElementById('panel');
        let btn = document.getElementById('btnToggle');
        if (panel.className.includes('oculto')) {
            panel.className = 'panel';
            btn.textContent = '◀';
            btn.style.left = '400px';
        } else {
            panel.className = 'panel oculto';
            btn.textContent = '▶';
            btn.style.left = '20px';
        }
    }
    document.getElementById('btnToggle').style.left = '400px';
    
    // Cerrar dropdown al hacer click fuera
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.search-box')) document.getElementById('dropdown').className = 'dropdown';
    });
    </script>
</body>
</html>
"""


# ============================================================
# INICIAR LA APLICACIÓN
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("  REFUGIOS A* - Ciudad Renacimiento, Acapulco")
    print("  Cargando datos...")
    print("=" * 60)
    
    # Cargar los datos al iniciar
    cargar_datos()
    
    print()
    print("  ✓ Aplicación lista")
    print("  ✓ Abre tu navegador en: http://localhost:5000")
    print("=" * 60)
    
    # Iniciar el servidor Flask
    # debug=False para producción, host="0.0.0.0" para acceso en red local
    app.run(host="0.0.0.0", port=5000, debug=False)
