#!/usr/bin/env python3
"""
========================================================================
  REFUGIOS A* - Script Standalone
  Encuentra el refugio (escuela) más cercano usando el algoritmo A*
  Colonia Renacimiento, Acapulco, Guerrero
  
  INSTRUCCIONES PARA COMPAÑEROS:
  1. Instalar dependencias: pip install networkx matplotlib
  2. Ejecutar: python refugios_astar_standalone.py
  3. Seguir las instrucciones en pantalla
========================================================================
"""

import json
import heapq
from math import sqrt, atan2, degrees
from pathlib import Path

# ============================================================
# DATOS: Escuelas / Refugios
# ============================================================

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
    "Artículos de higiene básicos (papel, jabón, gel antibacterial)",
    "Mascarilla o cubrebocas",
    "Bolsas de plástico (para proteger documentos)",
]

# ============================================================
# CLASE: Grafo con NetworkX
# ============================================================

try:
    import networkx as nx
    TIENE_NETWORKX = True
except ImportError:
    TIENE_NETWORKX = False
    print("AVISO: networkx no está instalado. Usando implementación propia del grafo.")
    print("Para instalar: pip install networkx")
    print()


class GrafoSimple:
    """
    Implementación simple de grafo para cuando no está disponible networkx.
    """
    def __init__(self):
        self.nodos = {}       # {id: {lat, lon, nombre, tipo}}
        self.aristas = {}     # {id: {vecino_id: {weight, nombre}}}

    def agregar_nodo(self, nodo_id, **attrs):
        self.nodos[nodo_id] = attrs
        if nodo_id not in self.aristas:
            self.aristas[nodo_id] = {}

    def agregar_arista(self, u, v, **attrs):
        if u not in self.aristas:
            self.aristas[u] = {}
        if v not in self.aristas:
            self.aristas[v] = {}
        self.aristas[u][v] = attrs
        self.aristas[v][u] = attrs  # Grafo no dirigido

    def vecinos(self, nodo_id):
        return self.aristas.get(nodo_id, {}).keys()

    def peso_arista(self, u, v):
        return self.aristas.get(u, {}).get(v, {}).get("weight", float('inf'))

    def nombre_arista(self, u, v):
        return self.aristas.get(u, {}).get(v, {}).get("nombre", "Sin nombre")

    def tiene_nodo(self, nodo_id):
        return nodo_id in self.nodos

    def total_nodos(self):
        return len(self.nodos)

    def total_aristas(self):
        return sum(len(v) for v in self.aristas.values()) // 2


# ============================================================
# FUNCIONES: Cargar datos
# ============================================================

def cargar_datos(data_dir=None):
    """
    Carga los archivos JSON con los datos de la red.
    Busca en el directorio actual o en el directorio especificado.
    """
    if data_dir is None:
        # Buscar en varias ubicaciones posibles
        posibles = [
            Path(__file__).parent / "data",
            Path(__file__).parent / "backend" / "data",
            Path("data"),
            Path("backend/data"),
        ]
        for p in posibles:
            if (p / "nodos_calles.json").exists():
                data_dir = p
                break

    if data_dir is None:
        print("ERROR: No se encontraron los archivos de datos JSON.")
        print("Asegúrate de que existan los archivos:")
        print("  - nodos_calles.json")
        print("  - aristas_calles.json")
        print("  - escuelas.json")
        return None, None, None

    data_dir = Path(data_dir)

    with open(data_dir / "nodos_calles.json", "r", encoding="utf-8") as f:
        nodos = json.load(f)

    with open(data_dir / "aristas_calles.json", "r", encoding="utf-8") as f:
        aristas = json.load(f)

    with open(data_dir / "escuelas.json", "r", encoding="utf-8") as f:
        escuelas = json.load(f)

    print(f"Datos cargados: {len(nodos)} nodos, {len(aristas)} aristas, {len(escuelas)} escuelas")
    return nodos, aristas, escuelas


def construir_grafo(nodos, aristas):
    """
    Construye el grafo a partir de los datos.
    Usa networkx si está disponible, si no usa implementación propia.
    """
    if TIENE_NETWORKX:
        G = nx.Graph()
        for nodo in nodos:
            G.add_node(nodo["id"], lat=nodo["lat"], lon=nodo["lon"],
                       nombre=nodo["nombre"], tipo=nodo["tipo"])
        for arista in aristas:
            G.add_edge(arista["origen"], arista["destino"],
                       weight=arista["distancia_m"], nombre=arista["nombre_calle"])
        return G
    else:
        G = GrafoSimple()
        for nodo in nodos:
            G.agregar_nodo(nodo["id"], lat=nodo["lat"], lon=nodo["lon"],
                           nombre=nodo["nombre"], tipo=nodo["tipo"])
        for arista in aristas:
            G.agregar_arista(arista["origen"], arista["destino"],
                             weight=arista["distancia_m"], nombre=arista["nombre_calle"])
        return G


# ============================================================
# ALGORITMO A*
# ============================================================

def heuristica(nodo1_id, nodo2_id, nodos_dict):
    """
    Heurística para A*: distancia euclidiana en metros.
    """
    n1 = nodos_dict[nodo1_id]
    n2 = nodos_dict[nodo2_id]
    lat_factor = 111000
    lon_factor = 111000 * 0.9
    dlat = (n2["lat"] - n1["lat"]) * lat_factor
    dlon = (n2["lon"] - n1["lon"]) * lon_factor
    return sqrt(dlat**2 + dlon**2)


def astar(G, origen, destino, nodos_dict):
    """
    Algoritmo A* para encontrar la ruta más corta.
    
    Parámetros:
        G: Grafo (networkx o GrafoSimple)
        origen: ID del nodo de inicio
        destino: ID del nodo destino
        nodos_dict: Diccionario {id: {lat, lon, ...}}
    
    Retorna:
        (ruta, distancia) donde ruta es lista de IDs y distancia es float
        (None, inf) si no hay ruta
    """
    if TIENE_NETWORKX:
        tiene_origen = origen in G
        tiene_destino = destino in G
    else:
        tiene_origen = G.tiene_nodo(origen)
        tiene_destino = G.tiene_nodo(destino)

    if not tiene_origen or not tiene_destino:
        return None, float('inf')

    if origen == destino:
        return [origen], 0

    # Cola de prioridad: (f_score, contador, nodo)
    contador = 0
    open_set = [(0, contador, origen)]
    came_from = {}
    g_score = {origen: 0}
    f_score = {origen: heuristica(origen, destino, nodos_dict)}
    open_set_hash = {origen}

    while open_set:
        _, _, current = heapq.heappop(open_set)

        if current == destino:
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()
            return path, g_score[destino]

        open_set_hash.discard(current)

        # Obtener vecinos
        if TIENE_NETWORKX:
            vecinos = G.neighbors(current)
        else:
            vecinos = G.vecinos(current)

        for neighbor in vecinos:
            if TIENE_NETWORKX:
                edge_data = G.get_edge_data(current, neighbor)
                weight = edge_data.get("weight", 1)
            else:
                weight = G.peso_arista(current, neighbor)

            tentative_g = g_score[current] + weight

            if tentative_g < g_score.get(neighbor, float('inf')):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f = tentative_g + heuristica(neighbor, destino, nodos_dict)
                f_score[neighbor] = f

                if neighbor not in open_set_hash:
                    contador += 1
                    heapq.heappush(open_set, (f, contador, neighbor))
                    open_set_hash.add(neighbor)

    return None, float('inf')


# ============================================================
# INSTRUCCIONES PASO A PASO
# ============================================================

def obtener_bearing(lat1, lon1, lat2, lon2):
    """Calcula ángulo de dirección entre dos puntos."""
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    angle = degrees(atan2(dlon, dlat))
    return angle % 360


def obtener_giro(bearing_prev, bearing_next):
    """Determina dirección del giro."""
    diff = (bearing_next - bearing_prev + 360) % 360
    if diff < 30 or diff > 330:
        return "Continúa recto"
    elif 30 <= diff < 150:
        return "Gira a la derecha"
    elif 150 <= diff <= 210:
        return "Da vuelta"
    else:
        return "Gira a la izquierda"


def generar_instrucciones(ruta, G, nodos_dict):
    """
    Genera instrucciones paso a paso para la ruta.
    """
    if len(ruta) < 2:
        return []

    instrucciones = []
    calle_actual = None
    dist_calle = 0
    paso_num = 0

    for i in range(len(ruta) - 1):
        n1, n2 = ruta[i], ruta[i + 1]

        if TIENE_NETWORKX:
            edge = G.get_edge_data(n1, n2)
            nombre_calle = edge.get("nombre", "Sin nombre") if edge else "Sin nombre"
            dist_seg = edge.get("weight", 0) if edge else 0
        else:
            nombre_calle = G.nombre_arista(n1, n2)
            dist_seg = G.peso_arista(n1, n2)

        if calle_actual is None:
            calle_actual = nombre_calle
            dist_calle = dist_seg
        elif nombre_calle == calle_actual:
            dist_calle += dist_seg
        else:
            paso_num += 1
            if i >= 2:
                p0 = nodos_dict[ruta[i-2]]
                p1 = nodos_dict[ruta[i-1]]
                p2 = nodos_dict[ruta[i]]
                bp = obtener_bearing(p0["lat"], p0["lon"], p1["lat"], p1["lon"])
                bn = obtener_bearing(p1["lat"], p1["lon"], p2["lat"], p2["lon"])
                giro = obtener_giro(bp, bn)
            else:
                giro = "Camina por"

            if paso_num == 1:
                texto = f"Sal caminando por {calle_actual} ({round(dist_calle)} m)"
            else:
                texto = f"{giro} hacia {nombre_calle} (recorriste {round(dist_calle)} m por {calle_actual})"

            instrucciones.append({"paso": paso_num, "texto": texto, "calle": calle_actual, "distancia": round(dist_calle)})
            calle_actual = nombre_calle
            dist_calle = dist_seg

    if calle_actual and dist_calle > 0:
        paso_num += 1
        instrucciones.append({"paso": paso_num, "texto": f"Continúa por {calle_actual} hasta llegar al refugio ({round(dist_calle)} m)", "calle": calle_actual, "distancia": round(dist_calle)})

    paso_num += 1
    instrucciones.append({"paso": paso_num, "texto": "¡Has llegado al refugio!", "calle": "Destino", "distancia": 0})

    return instrucciones


# ============================================================
# BUSCAR NODO MÁS CERCANO
# ============================================================

def buscar_nodo_cercano(nodos, texto):
    """
    Busca nodos por nombre de calle (tolerante a acentos y mayúsculas).
    """
    import unicodedata
    def normalizar(t):
        nfkd = unicodedata.normalize('NFKD', t)
        return "".join(c for c in nfkd if not unicodedata.combining(c)).lower()

    texto_norm = normalizar(texto)
    resultados = []

    for nodo in nodos:
        if nodo["nombre"] and texto_norm in normalizar(nodo["nombre"]):
            resultados.append(nodo)
            if len(resultados) >= 20:
                break

    return resultados


# ============================================================
# VISUALIZACIÓN (opcional, requiere matplotlib)
# ============================================================

def dibujar_grafo(nodos, aristas, escuelas, ruta_coords=None, nodo_origen=None, escuela_destino=None):
    """
    Dibuja el grafo con matplotlib, resaltando la ruta óptima.
    """
    try:
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.use('Agg')  # Para servidores sin display
    except ImportError:
        print("matplotlib no está instalado. No se puede dibujar.")
        print("Instalar: pip install matplotlib")
        return

    fig, ax = plt.subplots(1, 1, figsize=(14, 10))
    fig.patch.set_facecolor('#09090B')
    ax.set_facecolor('#09090B')

    # Dibujar aristas (calles)
    nodos_dict = {n["id"]: n for n in nodos}
    for arista in aristas:
        n1 = nodos_dict.get(arista["origen"])
        n2 = nodos_dict.get(arista["destino"])
        if n1 and n2:
            ax.plot([n1["lon"], n2["lon"]], [n1["lat"], n2["lat"]],
                    color='#333333', linewidth=0.5, alpha=0.5)

    # Dibujar ruta óptima
    if ruta_coords:
        lons = [c["lon"] for c in ruta_coords]
        lats = [c["lat"] for c in ruta_coords]
        ax.plot(lons, lats, color='#CCFF00', linewidth=3, alpha=0.9, zorder=5)

    # Dibujar escuelas
    for esc in escuelas:
        color = '#CCFF00' if escuela_destino and esc["id"] == escuela_destino["id"] else '#FF0055'
        size = 80 if escuela_destino and esc["id"] == escuela_destino["id"] else 50
        ax.scatter(esc["lon"], esc["lat"], c=color, s=size, zorder=10,
                   edgecolors='white', linewidths=1.5)
        # Nombre de la escuela
        nombre_corto = esc["nombre"][:25] + "..." if len(esc["nombre"]) > 25 else esc["nombre"]
        ax.annotate(nombre_corto, (esc["lon"], esc["lat"]),
                    textcoords="offset points", xytext=(8, 8),
                    fontsize=6, color='#FF0055', fontweight='bold')

    # Dibujar nodo de origen
    if nodo_origen:
        ax.scatter(nodo_origen["lon"], nodo_origen["lat"], c='#00E5FF', s=120,
                   zorder=15, edgecolors='white', linewidths=2, marker='*')
        ax.annotate("TU UBICACIÓN", (nodo_origen["lon"], nodo_origen["lat"]),
                    textcoords="offset points", xytext=(10, -15),
                    fontsize=8, color='#00E5FF', fontweight='bold')

    ax.set_title("Refugios A* - Colonia Renacimiento, Acapulco",
                 color='white', fontsize=14, fontweight='bold', pad=15)
    ax.tick_params(colors='#555555', labelsize=7)
    for spine in ax.spines.values():
        spine.set_color('#333333')

    plt.tight_layout()
    plt.savefig("ruta_refugio.png", dpi=150, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    print("\nMapa guardado como: ruta_refugio.png")
    plt.close()


# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================

def main():
    print("=" * 60)
    print("  REFUGIOS A* - Colonia Renacimiento, Acapulco")
    print("  Encuentra el refugio más cercano a tu ubicación")
    print("=" * 60)
    print()

    # 1. Cargar datos
    nodos, aristas, escuelas = cargar_datos()
    if nodos is None:
        return

    # 2. Construir grafo
    print("Construyendo grafo...")
    G = construir_grafo(nodos, aristas)
    nodos_dict = {n["id"]: n for n in nodos}

    if TIENE_NETWORKX:
        print(f"Grafo construido: {G.number_of_nodes()} nodos, {G.number_of_edges()} aristas")
    else:
        print(f"Grafo construido: {G.total_nodos()} nodos, {G.total_aristas()} aristas")
    print()

    # 3. Seleccionar ubicación
    print("PASO 1: Escribe el nombre de tu calle para buscar tu ubicación")
    print("(Ejemplo: Zapata, Cuauhtémoc, Costera, Bugambilias)")
    print()

    while True:
        texto = input("Buscar calle: ").strip()
        if not texto:
            continue

        resultados = buscar_nodo_cercano(nodos, texto)

        if not resultados:
            print(f"  No se encontraron resultados para '{texto}'. Intenta otro nombre.")
            continue

        print(f"\n  Se encontraron {len(resultados)} puntos:")
        for i, r in enumerate(resultados):
            print(f"    [{i+1}] {r['nombre']}")

        try:
            opcion = int(input("\n  Selecciona un número: ")) - 1
            if 0 <= opcion < len(resultados):
                nodo_origen = resultados[opcion]
                break
            else:
                print("  Opción no válida.")
        except ValueError:
            print("  Escribe un número.")

    print(f"\n  Ubicación seleccionada: {nodo_origen['nombre']}")
    print(f"  Coordenadas: {nodo_origen['lat']}, {nodo_origen['lon']}")
    print()

    # 4. Calcular rutas A* a todas las escuelas
    print("PASO 2: Calculando ruta A* a las 18 escuelas...")
    print()

    resultados_rutas = []
    for esc in escuelas:
        ruta, distancia = astar(G, nodo_origen["id"], esc["nodo_id"], nodos_dict)
        if ruta:
            tiempo = distancia / 83.33  # 5 km/h
            resultados_rutas.append({
                "escuela": esc,
                "ruta": ruta,
                "distancia": round(distancia, 1),
                "tiempo": round(tiempo, 1)
            })

    if not resultados_rutas:
        print("ERROR: No se encontró ruta a ninguna escuela.")
        return

    # Ordenar por distancia
    resultados_rutas.sort(key=lambda r: r["distancia"])
    mejor = resultados_rutas[0]

    # 5. Mostrar resultado
    print("=" * 60)
    print("  RESULTADO: REFUGIO MÁS CERCANO")
    print("=" * 60)
    print()
    print(f"  Escuela:   {mejor['escuela']['nombre']}")
    if mejor['escuela']['alias']:
        print(f"  Alias:     {mejor['escuela']['alias']}")
    print(f"  Tipo:      {mejor['escuela']['tipo']}")
    if mejor['escuela']['unificada']:
        print(f"  Nota:      Plantel de doble turno (mismo edificio)")
    print(f"  Distancia: {mejor['distancia']} m ({mejor['distancia']/1000:.1f} km)")
    print(f"  Tiempo:    {mejor['tiempo']} min caminando")
    print(f"  Nodos:     {len(mejor['ruta'])} puntos en la ruta")
    print()

    # 6. Instrucciones paso a paso
    instrucciones = generar_instrucciones(mejor['ruta'], G, nodos_dict)
    print("-" * 60)
    print("  INSTRUCCIONES PASO A PASO")
    print("-" * 60)
    for inst in instrucciones:
        marca = ">>>" if inst["distancia"] == 0 else f"   "
        print(f"  {marca} Paso {inst['paso']}: {inst['texto']}")
    print()

    # 7. Lista de todas las escuelas
    print("-" * 60)
    print("  TODAS LAS ESCUELAS (ordenadas por distancia)")
    print("-" * 60)
    for i, r in enumerate(resultados_rutas):
        marca = " <<<" if i == 0 else ""
        dist_str = f"{r['distancia']/1000:.1f} km" if r['distancia'] >= 1000 else f"{round(r['distancia'])} m"
        print(f"  {i+1:2d}. {r['escuela']['nombre'][:45]:45s} | {dist_str:>8s} | {r['tiempo']:5.1f} min{marca}")
    print()

    # 8. Sugerencias de emergencia
    print("=" * 60)
    print("  QUÉ LLEVAR AL REFUGIO (Kit de emergencia)")
    print("=" * 60)
    for i, sug in enumerate(SUGERENCIAS_EMERGENCIA):
        print(f"  {i+1:2d}. {sug}")
    print()

    # 9. Dibujar mapa (si matplotlib está disponible)
    ruta_coords = [nodos_dict[nid] for nid in mejor['ruta'] if nid in nodos_dict]
    dibujar_grafo(nodos, aristas, escuelas,
                  ruta_coords=ruta_coords,
                  nodo_origen=nodo_origen,
                  escuela_destino=mejor['escuela'])

    print("=" * 60)
    print("  ¡Listo! Camina con precaución hacia tu refugio.")
    print("=" * 60)


if __name__ == "__main__":
    main()
