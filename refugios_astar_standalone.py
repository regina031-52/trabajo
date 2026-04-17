#!/usr/bin/env python3
"""
========================================================================
  REFUGIOS A* - Script Standalone
  Encuentra el refugio (escuela) más cercano usando el algoritmo A*
  Ciudad Renacimiento, Acapulco de Juárez, Guerrero (CP 39715)

  INSTRUCCIONES PARA COMPAÑEROS:
  1. Instalar dependencias: pip install networkx matplotlib
  2. Poner la carpeta "data/" junto a este archivo con los 3 JSON:
     - escuelas.json
     - nodos_calles.json
     - aristas_calles.json
  3. Ejecutar: python refugios_astar_standalone.py
  4. Seguir las instrucciones en pantalla
========================================================================
"""

import json
import heapq
from math import sqrt, atan2, degrees
from pathlib import Path

# ============================================================
# DATOS: 17 Refugios de Ciudad Renacimiento
# ============================================================

REFUGIOS_INFO = [
    {"id": "R01", "nombre": "Instituto Emiliano Zapata",
     "direccion": "C. 2 93, Zapata, Emiliano Zapata, 39700"},
    {"id": "R02", "nombre": "Esc. Prim. Urb. Mat. Francisco Pérez Ríos",
     "direccion": "De Las Cruces s/n, Electricistas, 39715"},
    {"id": "R03", "nombre": "Primaria Benemérito de las Américas",
     "direccion": "Juan N. Álvarez 14, Arroyo Seco, Cd Renacimiento, 39715"},
    {"id": "R04", "nombre": "Escuela Primaria Matutina Ignacio M. Altamirano",
     "direccion": "Ferretería la Ceiba s/n, Cd Renacimiento, 39715"},
    {"id": "R05", "nombre": "Jardín de Niños Manuel Acuña",
     "direccion": "Del Valle 15, Colonia Agrícola, 39713"},
    {"id": "R06", "nombre": "Plantel Adolfo López Mateos",
     "direccion": "Av. Juan R. Escudero s/n, Cd Renacimiento, 39715"},
    {"id": "R07", "nombre": "Escuela Primaria Rural Federal Jaime Nunó",
     "direccion": "Localidad los coyotes, Cd Renacimiento, 39715"},
    {"id": "R08", "nombre": "Escuela Primaria Adolfo López Mateos (Pedro Ascencio)",
     "direccion": "Pedro Ascencio 5-21, Cd Renacimiento, 39715"},
    {"id": "R09", "nombre": "Primaria 7",
     "direccion": "Cto. Interior Renacimiento 11, Cd Renacimiento, 39715"},
    {"id": "R10", "nombre": "Escuela Prim. Raúl Isidro Burgos",
     "direccion": "Costa Azul 22, Cd Renacimiento, 39715"},
    {"id": "R11", "nombre": "Escuela Primaria Urbana Turno Matutino Raúl Isidro Burgos",
     "direccion": "Costa Azul 7, Cd Renacimiento, 39715"},
    {"id": "R12", "nombre": "Escuela Primaria Urbana Matutina Lázaro Cárdenas",
     "direccion": "Ejído Nuxco s/n, Cd Renacimiento, 39715"},
    {"id": "R13", "nombre": "Escuela Primaria Turno Matutino Gabriela Mistral",
     "direccion": "Palma Sola s/n, Cd Renacimiento, 39715"},
    {"id": "R14", "nombre": "Escuela Primaria Vespertino Antonio I. Delgado",
     "direccion": "Río Yolotla s/n, Cd Renacimiento, 39715"},
    {"id": "R15", "nombre": "Escuela Primaria Francisco Sarabia",
     "direccion": "José María Izazaga 21, Cd Renacimiento, 39715"},
    {"id": "R16", "nombre": "Jardín de Niños Luis Hidalgo Monroy",
     "direccion": "20 de Noviembre s/n, La Popular, 39780"},
    {"id": "R17", "nombre": "CETis 116 Antonia Nava de Catalán",
     "direccion": "Retorno Educación esq. Alta Quebradora, Cd Renacimiento, 39715"},
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
# CLASE: Grafo (implementación propia si no hay networkx)
# ============================================================

try:
    import networkx as nx
    TIENE_NETWORKX = True
except ImportError:
    TIENE_NETWORKX = False
    print("AVISO: networkx no instalado. Usando implementación propia.")
    print("Para instalar: pip install networkx\n")


class GrafoSimple:
    """Grafo no dirigido simple cuando no hay networkx."""
    def __init__(self):
        self.nodos = {}
        self.aristas = {}

    def agregar_nodo(self, nodo_id, **attrs):
        self.nodos[nodo_id] = attrs
        if nodo_id not in self.aristas:
            self.aristas[nodo_id] = {}

    def agregar_arista(self, u, v, **attrs):
        if u not in self.aristas: self.aristas[u] = {}
        if v not in self.aristas: self.aristas[v] = {}
        self.aristas[u][v] = attrs
        self.aristas[v][u] = attrs

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
# FUNCIONES: Cargar datos JSON
# ============================================================

def cargar_datos(data_dir=None):
    """Carga los archivos JSON. Busca en varias ubicaciones."""
    if data_dir is None:
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
        print("Asegúrate de tener la carpeta 'data/' con:")
        print("  - escuelas.json")
        print("  - nodos_calles.json")
        print("  - aristas_calles.json")
        return None, None, None

    data_dir = Path(data_dir)
    with open(data_dir / "nodos_calles.json", "r", encoding="utf-8") as f:
        nodos = json.load(f)
    with open(data_dir / "aristas_calles.json", "r", encoding="utf-8") as f:
        aristas = json.load(f)
    with open(data_dir / "escuelas.json", "r", encoding="utf-8") as f:
        escuelas = json.load(f)

    print(f"Datos cargados: {len(nodos)} nodos, {len(aristas)} aristas, {len(escuelas)} refugios")
    return nodos, aristas, escuelas


def construir_grafo(nodos, aristas):
    """Construye el grafo con networkx o implementación propia."""
    if TIENE_NETWORKX:
        G = nx.Graph()
        for n in nodos:
            G.add_node(n["id"], lat=n["lat"], lon=n["lon"], nombre=n["nombre"], tipo=n["tipo"])
        for a in aristas:
            G.add_edge(a["origen"], a["destino"], weight=a["distancia_m"], nombre=a["nombre_calle"])
        return G
    else:
        G = GrafoSimple()
        for n in nodos:
            G.agregar_nodo(n["id"], lat=n["lat"], lon=n["lon"], nombre=n["nombre"], tipo=n["tipo"])
        for a in aristas:
            G.agregar_arista(a["origen"], a["destino"], weight=a["distancia_m"], nombre=a["nombre_calle"])
        return G


# ============================================================
# ALGORITMO A*
# ============================================================

def heuristica(nodo1_id, nodo2_id, nodos_dict):
    """Distancia euclidiana en metros (heurística admisible)."""
    n1, n2 = nodos_dict[nodo1_id], nodos_dict[nodo2_id]
    dlat = (n2["lat"] - n1["lat"]) * 111000
    dlon = (n2["lon"] - n1["lon"]) * 111000 * 0.9
    return sqrt(dlat**2 + dlon**2)


def astar(G, origen, destino, nodos_dict):
    """
    Algoritmo A* - Encuentra la ruta más corta entre dos nodos.
    Retorna (lista_nodos, distancia) o (None, inf) si no hay ruta.
    """
    if TIENE_NETWORKX:
        if origen not in G or destino not in G:
            return None, float('inf')
    else:
        if not G.tiene_nodo(origen) or not G.tiene_nodo(destino):
            return None, float('inf')

    if origen == destino:
        return [origen], 0

    contador = 0
    open_set = [(0, contador, origen)]
    came_from = {}
    g_score = {origen: 0}
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
        vecinos = G.neighbors(current) if TIENE_NETWORKX else G.vecinos(current)

        for neighbor in vecinos:
            if TIENE_NETWORKX:
                weight = G.get_edge_data(current, neighbor).get("weight", 1)
            else:
                weight = G.peso_arista(current, neighbor)

            tentative_g = g_score[current] + weight
            if tentative_g < g_score.get(neighbor, float('inf')):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f = tentative_g + heuristica(neighbor, destino, nodos_dict)
                if neighbor not in open_set_hash:
                    contador += 1
                    heapq.heappush(open_set, (f, contador, neighbor))
                    open_set_hash.add(neighbor)

    return None, float('inf')


# ============================================================
# INSTRUCCIONES PASO A PASO
# ============================================================

def obtener_bearing(lat1, lon1, lat2, lon2):
    return degrees(atan2(lon2 - lon1, lat2 - lat1)) % 360

def obtener_giro(bp, bn):
    diff = (bn - bp + 360) % 360
    if diff < 30 or diff > 330: return "Continúa recto"
    elif 30 <= diff < 150: return "Gira a la derecha"
    elif 150 <= diff <= 210: return "Da vuelta"
    else: return "Gira a la izquierda"

def generar_instrucciones(ruta, G, nodos_dict):
    """Genera instrucciones paso a paso agrupando segmentos de la misma calle."""
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
                p0, p1, p2 = nodos_dict[ruta[i-2]], nodos_dict[ruta[i-1]], nodos_dict[ruta[i]]
                giro = obtener_giro(
                    obtener_bearing(p0["lat"], p0["lon"], p1["lat"], p1["lon"]),
                    obtener_bearing(p1["lat"], p1["lon"], p2["lat"], p2["lon"]))
            else:
                giro = "Camina por"

            texto = f"Sal caminando por {calle_actual} ({round(dist_calle)} m)" if paso_num == 1 \
                else f"{giro} hacia {nombre_calle} (recorriste {round(dist_calle)} m por {calle_actual})"
            instrucciones.append({"paso": paso_num, "texto": texto, "distancia": round(dist_calle)})
            calle_actual = nombre_calle
            dist_calle = dist_seg

    if calle_actual and dist_calle > 0:
        paso_num += 1
        instrucciones.append({"paso": paso_num,
            "texto": f"Continúa por {calle_actual} hasta llegar al refugio ({round(dist_calle)} m)",
            "distancia": round(dist_calle)})

    paso_num += 1
    instrucciones.append({"paso": paso_num, "texto": "¡Has llegado al refugio!", "distancia": 0})
    return instrucciones


# ============================================================
# BUSCAR POR NOMBRE DE CALLE
# ============================================================

def buscar_nodo(nodos, texto):
    """Busca nodos por nombre de calle (tolerante a acentos)."""
    import unicodedata
    def norm(t):
        return "".join(c for c in unicodedata.normalize('NFKD', t) if not unicodedata.combining(c)).lower()

    q = norm(texto)
    # Búsqueda directa
    resultados = [n for n in nodos if n["nombre"] and q in norm(n["nombre"])][:20]

    # Si pocos resultados, buscar sin prefijos
    if len(resultados) < 10:
        prefijos = ["calle ", "avenida ", "andador ", "privada ", "cerrada ", "cerca de "]
        vistos = {r["id"] for r in resultados}
        for n in nodos:
            if n["id"] in vistos or not n["nombre"]: continue
            nn = norm(n["nombre"])
            for pref in prefijos:
                if nn.startswith(pref) and q in nn[len(pref):]:
                    resultados.append(n)
                    vistos.add(n["id"])
                    break
            if len(resultados) >= 20: break

    return resultados


# ============================================================
# VISUALIZACIÓN (requiere matplotlib)
# ============================================================

def dibujar_grafo(nodos, aristas, escuelas, ruta_coords=None, nodo_origen=None, escuela_destino=None):
    """Dibuja el grafo resaltando la ruta óptima. Guarda como ruta_refugio.png"""
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib no instalado. Instalar: pip install matplotlib")
        return

    fig, ax = plt.subplots(1, 1, figsize=(14, 10))
    fig.patch.set_facecolor('#09090B')
    ax.set_facecolor('#09090B')

    nodos_dict = {n["id"]: n for n in nodos}

    # Calles
    for a in aristas:
        n1, n2 = nodos_dict.get(a["origen"]), nodos_dict.get(a["destino"])
        if n1 and n2:
            ax.plot([n1["lon"], n2["lon"]], [n1["lat"], n2["lat"]], color='#333333', linewidth=0.5, alpha=0.5)

    # Ruta óptima
    if ruta_coords:
        ax.plot([c["lon"] for c in ruta_coords], [c["lat"] for c in ruta_coords],
                color='#CCFF00', linewidth=3, alpha=0.9, zorder=5)

    # Escuelas
    for esc in escuelas:
        es_destino = escuela_destino and esc["id"] == escuela_destino["id"]
        ax.scatter(esc["lon"], esc["lat"], c='#CCFF00' if es_destino else '#FF0055',
                   s=80 if es_destino else 50, zorder=10, edgecolors='white', linewidths=1.5)
        nombre_corto = esc["nombre"][:28] + "..." if len(esc["nombre"]) > 28 else esc["nombre"]
        ax.annotate(nombre_corto, (esc["lon"], esc["lat"]), textcoords="offset points",
                    xytext=(8, 8), fontsize=5, color='#FF0055', fontweight='bold')

    # Ubicación del usuario
    if nodo_origen:
        ax.scatter(nodo_origen["lon"], nodo_origen["lat"], c='#00E5FF', s=120,
                   zorder=15, edgecolors='white', linewidths=2, marker='*')
        ax.annotate("TU UBICACIÓN", (nodo_origen["lon"], nodo_origen["lat"]),
                    textcoords="offset points", xytext=(10, -15), fontsize=8, color='#00E5FF', fontweight='bold')

    ax.set_title("Refugios A* - Ciudad Renacimiento, Acapulco", color='white', fontsize=14, fontweight='bold', pad=15)
    ax.tick_params(colors='#555555', labelsize=7)
    for spine in ax.spines.values(): spine.set_color('#333333')

    plt.tight_layout()
    plt.savefig("ruta_refugio.png", dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
    print("\nMapa guardado como: ruta_refugio.png")
    plt.close()


# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================

def main():
    print("=" * 65)
    print("  REFUGIOS A* - Ciudad Renacimiento, Acapulco (CP 39715)")
    print("  Encuentra el refugio más cercano a tu ubicación")
    print("=" * 65)
    print()

    # 1. Cargar datos
    nodos, aristas, escuelas = cargar_datos()
    if nodos is None:
        return

    # 2. Construir grafo
    print("Construyendo grafo...")
    G = construir_grafo(nodos, aristas)
    nodos_dict = {n["id"]: n for n in nodos}

    n_nodos = G.number_of_nodes() if TIENE_NETWORKX else G.total_nodos()
    n_aristas = G.number_of_edges() if TIENE_NETWORKX else G.total_aristas()
    print(f"Grafo: {n_nodos} nodos, {n_aristas} aristas, {len(escuelas)} refugios\n")

    # 3. Seleccionar ubicación
    print("PASO 1: Escribe el nombre de tu calle")
    print("  (Ejemplo: Escudero, Zaragoza, Canal, Costa Azul, Cuauhtémoc)")
    print("  No necesitas escribir 'Calle' ni 'Avenida', solo el nombre.\n")

    while True:
        texto = input("  Buscar calle: ").strip()
        if not texto:
            continue

        resultados = buscar_nodo(nodos, texto)
        if not resultados:
            print(f"  No encontré '{texto}'. Intenta otro nombre.\n")
            continue

        print(f"\n  {len(resultados)} puntos encontrados:")
        for i, r in enumerate(resultados):
            print(f"    [{i+1}] {r['nombre']}")

        try:
            opcion = int(input("\n  Selecciona un número: ")) - 1
            if 0 <= opcion < len(resultados):
                nodo_origen = resultados[opcion]
                break
            print("  Número fuera de rango.")
        except ValueError:
            print("  Escribe un número.")

    print(f"\n  Ubicación: {nodo_origen['nombre']}")
    print(f"  Coordenadas: {nodo_origen['lat']:.5f}, {nodo_origen['lon']:.5f}\n")

    # 4. Calcular rutas A*
    print(f"PASO 2: Calculando ruta A* a los {len(escuelas)} refugios...\n")

    resultados_rutas = []
    for esc in escuelas:
        ruta, distancia = astar(G, nodo_origen["id"], esc["nodo_id"], nodos_dict)
        if ruta:
            resultados_rutas.append({
                "escuela": esc,
                "ruta": ruta,
                "distancia": round(distancia, 1),
                "tiempo": round(distancia / 83.33, 1)  # 5 km/h
            })

    if not resultados_rutas:
        print("ERROR: No se encontró ruta a ningún refugio.")
        return

    resultados_rutas.sort(key=lambda r: r["distancia"])
    mejor = resultados_rutas[0]

    # 5. Resultado
    print("=" * 65)
    print("  RESULTADO: REFUGIO MÁS CERCANO")
    print("=" * 65)
    print(f"\n  Refugio:    {mejor['escuela']['nombre']}")
    if mejor['escuela'].get('alias'):
        print(f"  Alias:      {mejor['escuela']['alias']}")
    if mejor['escuela'].get('direccion'):
        print(f"  Dirección:  {mejor['escuela']['direccion']}")
    print(f"  Tipo:       {mejor['escuela']['tipo']}")
    if mejor['escuela'].get('unificada'):
        print(f"  Nota:       Plantel de doble turno (mismo edificio)")
    print(f"  Distancia:  {mejor['distancia']} m ({mejor['distancia']/1000:.1f} km)")
    print(f"  Tiempo:     {mejor['tiempo']} min caminando")
    print(f"  Nodos:      {len(mejor['ruta'])} puntos en la ruta\n")

    # 6. Instrucciones paso a paso
    instrucciones = generar_instrucciones(mejor['ruta'], G, nodos_dict)
    print("-" * 65)
    print("  INSTRUCCIONES PASO A PASO")
    print("-" * 65)
    for inst in instrucciones:
        marca = ">>>" if inst["distancia"] == 0 else "   "
        print(f"  {marca} Paso {inst['paso']}: {inst['texto']}")
    print()

    # 7. Lista de todos los refugios
    print("-" * 65)
    print("  TODOS LOS REFUGIOS (ordenados por distancia)")
    print("-" * 65)
    for i, r in enumerate(resultados_rutas):
        marca = " <<<" if i == 0 else ""
        d = f"{r['distancia']/1000:.1f} km" if r['distancia'] >= 1000 else f"{round(r['distancia'])} m"
        print(f"  {i+1:2d}. {r['escuela']['nombre'][:42]:42s} | {d:>8s} | {r['tiempo']:5.1f} min{marca}")
    print()

    # 8. Kit de emergencia
    print("=" * 65)
    print("  QUÉ LLEVAR AL REFUGIO (Kit de emergencia)")
    print("=" * 65)
    for i, sug in enumerate(SUGERENCIAS_EMERGENCIA):
        print(f"  {i+1:2d}. {sug}")
    print()

    # 9. Dibujar mapa
    ruta_coords = [nodos_dict[nid] for nid in mejor['ruta'] if nid in nodos_dict]
    dibujar_grafo(nodos, aristas, escuelas, ruta_coords=ruta_coords,
                  nodo_origen=nodo_origen, escuela_destino=mejor['escuela'])

    print("=" * 65)
    print("  ¡Listo! Camina con precaución hacia tu refugio.")
    print("=" * 65)


if __name__ == "__main__":
    main()
