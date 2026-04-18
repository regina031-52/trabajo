#!/usr/bin/env python3
"""
========================================================================
  REFUGIOS A* - Script Standalone
  Encuentra el refugio (escuela) más cercano usando el algoritmo A*
  Ciudad Renacimiento, Acapulco de Juárez, Guerrero (CP 39715)

  INSTRUCCIONES:
  1. pip install networkx matplotlib
  2. Poner carpeta "data/" con los 3 JSON junto a este archivo
  3. python refugios_astar_standalone.py
========================================================================
"""

import json, heapq, unicodedata
from math import sqrt, atan2, degrees
from pathlib import Path

SUGERENCIAS = [
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

try:
    import networkx as nx
    HAS_NX = True
except ImportError:
    HAS_NX = False
    print("AVISO: networkx no instalado → pip install networkx\n")

class Grafo:
    def __init__(self):
        self.nodos, self.adj = {}, {}
    def add_node(self, nid, **a):
        self.nodos[nid] = a
        if nid not in self.adj: self.adj[nid] = {}
    def add_edge(self, u, v, **a):
        for x in (u, v):
            if x not in self.adj: self.adj[x] = {}
        self.adj[u][v] = a; self.adj[v][u] = a
    def neighbors(self, n): return self.adj.get(n, {}).keys()
    def weight(self, u, v): return self.adj.get(u, {}).get(v, {}).get("weight", 1e9)
    def edge_name(self, u, v): return self.adj.get(u, {}).get(v, {}).get("nombre", "Sin nombre")
    def has(self, n): return n in self.nodos
    def n_nodes(self): return len(self.nodos)
    def n_edges(self): return sum(len(v) for v in self.adj.values()) // 2

def cargar_datos(d=None):
    if d is None:
        for p in [Path(__file__).parent/"data", Path("data"), Path("backend/data")]:
            if (p/"nodos_calles.json").exists(): d = p; break
    if d is None:
        print("ERROR: No se encontró carpeta data/ con los JSON"); return None, None, None
    d = Path(d)
    nodos = json.loads((d/"nodos_calles.json").read_text("utf-8"))
    aristas = json.loads((d/"aristas_calles.json").read_text("utf-8"))
    escuelas = json.loads((d/"escuelas.json").read_text("utf-8"))
    print(f"Datos: {len(nodos)} nodos, {len(aristas)} aristas, {len(escuelas)} refugios")
    return nodos, aristas, escuelas

def construir_grafo(nodos, aristas):
    if HAS_NX:
        G = nx.Graph()
        for n in nodos: G.add_node(n["id"], **{k: n[k] for k in ("lat","lon","nombre","tipo")})
        for a in aristas: G.add_edge(a["origen"], a["destino"], weight=a["distancia_m"], nombre=a["nombre_calle"])
        return G
    G = Grafo()
    for n in nodos: G.add_node(n["id"], lat=n["lat"], lon=n["lon"], nombre=n["nombre"], tipo=n["tipo"])
    for a in aristas: G.add_edge(a["origen"], a["destino"], weight=a["distancia_m"], nombre=a["nombre_calle"])
    return G

def h(a, b, nd):
    n1, n2 = nd[a], nd[b]
    return sqrt(((n2["lat"]-n1["lat"])*111000)**2 + ((n2["lon"]-n1["lon"])*99900)**2)

def astar(G, s, t, nd):
    if HAS_NX:
        ok = s in G and t in G
    else:
        ok = G.has(s) and G.has(t)
    if not ok: return None, 1e9
    if s == t: return [s], 0
    c = 0; pq = [(0, c, s)]; cf = {}; gs = {s: 0}; vis = {s}
    while pq:
        _, _, u = heapq.heappop(pq)
        if u == t:
            p = [u]
            while u in cf: u = cf[u]; p.append(u)
            return p[::-1], gs[t]
        vis.discard(u)
        for v in (G.neighbors(u)):
            w = G[u][v]["weight"] if HAS_NX else G.weight(u, v)
            g = gs[u] + w
            if g < gs.get(v, 1e9):
                cf[v] = u; gs[v] = g
                if v not in vis: c += 1; heapq.heappush(pq, (g + h(v, t, nd), c, v)); vis.add(v)
    return None, 1e9

def bearing(a, b, nd):
    n1, n2 = nd[a], nd[b]
    return degrees(atan2(n2["lon"]-n1["lon"], n2["lat"]-n1["lat"])) % 360

def giro(bp, bn):
    d = (bn - bp + 360) % 360
    if d < 30 or d > 330: return "Continúa recto"
    elif d < 150: return "Gira a la derecha"
    elif d <= 210: return "Da vuelta"
    else: return "Gira a la izquierda"

def instrucciones(ruta, G, nd):
    if len(ruta) < 2: return []
    pasos = []; ca = None; dc = 0; pn = 0
    for i in range(len(ruta)-1):
        e = G[ruta[i]][ruta[i+1]] if HAS_NX else None
        nm = (e.get("nombre","?") if e else G.edge_name(ruta[i], ruta[i+1]))
        ds = (e.get("weight",0) if e else G.weight(ruta[i], ruta[i+1]))
        if ca is None: ca, dc = nm, ds
        elif nm == ca: dc += ds
        else:
            pn += 1
            g = giro(bearing(ruta[i-2], ruta[i-1], nd), bearing(ruta[i-1], ruta[i], nd)) if i >= 2 else "Camina por"
            t = f"Sal caminando por {ca} ({round(dc)} m)" if pn == 1 else f"{g} hacia {nm} ({round(dc)} m por {ca})"
            pasos.append({"p": pn, "t": t, "d": round(dc)}); ca, dc = nm, ds
    if ca and dc > 0:
        pn += 1; pasos.append({"p": pn, "t": f"Continúa por {ca} hasta el refugio ({round(dc)} m)", "d": round(dc)})
    pn += 1; pasos.append({"p": pn, "t": "¡Llegaste al refugio!", "d": 0})
    return pasos

def buscar(nodos, q):
    def n(t): return "".join(c for c in unicodedata.normalize('NFKD', t) if not unicodedata.combining(c)).lower()
    qn = n(q); r = []; v = set()
    for nd in nodos:
        if nd["nombre"] and qn in n(nd["nombre"]) and nd["id"] not in v:
            v.add(nd["id"]); r.append(nd)
            if len(r) >= 20: break
    if len(r) < 10:
        for nd in nodos:
            if nd["id"] in v or not nd["nombre"]: continue
            nn = n(nd["nombre"])
            for pf in ["calle ","avenida ","andador ","privada ","cerrada ","cerca de "]:
                if nn.startswith(pf) and qn in nn[len(pf):]:
                    v.add(nd["id"]); r.append(nd); break
            if len(r) >= 20: break
    return r

def dibujar(nodos, aristas, escuelas, rc=None, orig=None, dest=None):
    try:
        import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    except ImportError: print("matplotlib no instalado"); return
    fig, ax = plt.subplots(figsize=(14, 10)); ax.set_facecolor('#F4F5F7'); fig.patch.set_facecolor('#F4F5F7')
    nd = {n["id"]: n for n in nodos}
    for a in aristas:
        n1, n2 = nd.get(a["origen"]), nd.get(a["destino"])
        if n1 and n2: ax.plot([n1["lon"],n2["lon"]], [n1["lat"],n2["lat"]], color='#CBD5E1', lw=0.5, alpha=0.6)
    if rc: ax.plot([c["lon"] for c in rc], [c["lat"] for c in rc], color='#2563EB', lw=3.5, alpha=0.9, zorder=5)
    for e in escuelas:
        es_d = dest and e["id"] == dest["id"]
        ax.scatter(e["lon"], e["lat"], c='#16A34A' if es_d else '#DC2626', s=80 if es_d else 45, zorder=10, edgecolors='white', lw=1.5)
        ax.annotate(e["nombre"][:28]+("..." if len(e["nombre"])>28 else ""), (e["lon"], e["lat"]),
                    xytext=(8,8), textcoords="offset points", fontsize=5, color='#DC2626', fontweight='bold')
    if orig:
        ax.scatter(orig["lon"], orig["lat"], c='#0EA5E9', s=120, zorder=15, edgecolors='white', lw=2, marker='*')
        ax.annotate("TU UBICACIÓN", (orig["lon"], orig["lat"]), xytext=(10,-15), textcoords="offset points", fontsize=8, color='#0EA5E9', fontweight='bold')
    ax.set_title("Refugios A* — Ciudad Renacimiento, Acapulco", fontsize=14, fontweight='bold', color='#1E293B', pad=15)
    ax.tick_params(colors='#94A3B8', labelsize=7)
    for s in ax.spines.values(): s.set_color('#E2E8F0')
    plt.tight_layout(); plt.savefig("ruta_refugio.png", dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
    print("\nMapa guardado: ruta_refugio.png"); plt.close()

def main():
    print("=" * 65)
    print("  REFUGIOS A* — Ciudad Renacimiento, Acapulco (CP 39715)")
    print("  Encuentra el refugio más cercano a tu ubicación")
    print("=" * 65, "\n")
    nodos, aristas, escuelas = cargar_datos()
    if not nodos: return
    G = construir_grafo(nodos, aristas)
    nd = {n["id"]: n for n in nodos}
    nn = G.number_of_nodes() if HAS_NX else G.n_nodes()
    ne = G.number_of_edges() if HAS_NX else G.n_edges()
    print(f"Grafo: {nn} nodos, {ne} aristas, {len(escuelas)} refugios\n")

    print("PASO 1: Escribe el nombre de tu calle")
    print("  (Solo el nombre: Escudero, Costa Azul, Zaragoza, Río Yolotla...)\n")
    while True:
        q = input("  Buscar: ").strip()
        if not q: continue
        res = buscar(nodos, q)
        if not res: print(f"  '{q}' no encontrado. Intenta otro.\n"); continue
        print(f"\n  {len(res)} resultados:")
        for i, r in enumerate(res): print(f"    [{i+1}] {r['nombre']}")
        try:
            op = int(input("\n  Número: ")) - 1
            if 0 <= op < len(res): orig = res[op]; break
            print("  Fuera de rango.")
        except ValueError: print("  Escribe un número.")
    print(f"\n  Ubicación: {orig['nombre']}\n")

    print(f"PASO 2: Calculando A* a {len(escuelas)} refugios...\n")
    rutas = []
    for e in escuelas:
        r, d = astar(G, orig["id"], e["nodo_id"], nd)
        if r: rutas.append({"esc": e, "ruta": r, "dist": round(d, 1), "min": round(d/83.33, 1)})
    if not rutas: print("No se encontró ruta."); return
    rutas.sort(key=lambda x: x["dist"]); m = rutas[0]

    print("=" * 65)
    print("  REFUGIO MÁS CERCANO")
    print("=" * 65)
    print(f"\n  {m['esc']['nombre']}")
    if m['esc'].get('alias'): print(f"  ({m['esc']['alias']})")
    if m['esc'].get('direccion'): print(f"  Dir: {m['esc']['direccion']}")
    print(f"  Tipo: {m['esc']['tipo']}  |  Estatus: {m['esc'].get('estatus','')}")
    print(f"  Distancia: {m['dist']} m ({m['dist']/1000:.1f} km)  |  Tiempo: {m['min']} min\n")

    ins = instrucciones(m['ruta'], G, nd)
    print("-" * 65)
    print("  INSTRUCCIONES PASO A PASO")
    print("-" * 65)
    for i in ins: print(f"  {'>>>' if i['d']==0 else '   '} Paso {i['p']}: {i['t']}")

    print(f"\n{'-'*65}")
    print("  TODOS LOS REFUGIOS (por distancia)")
    print("-" * 65)
    for i, r in enumerate(rutas):
        d = f"{r['dist']/1000:.1f}km" if r['dist'] >= 1000 else f"{round(r['dist'])}m"
        print(f"  {i+1:2d}. {r['esc']['nombre'][:42]:42s} | {d:>7s} | {r['min']:5.1f}min{'  <<<' if i==0 else ''}")

    print(f"\n{'='*65}")
    print("  QUÉ LLEVAR AL REFUGIO")
    print("=" * 65)
    for i, s in enumerate(SUGERENCIAS): print(f"  {i+1:2d}. {s}")

    rc = [nd[n] for n in m['ruta'] if n in nd]
    dibujar(nodos, aristas, escuelas, rc, orig, m['esc'])
    print(f"\n{'='*65}")
    print("  ¡Camina con precaución hacia tu refugio!")
    print("=" * 65)

if __name__ == "__main__":
    main()
