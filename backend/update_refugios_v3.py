"""
Actualizar refugios con coordenadas VERIFICADAS por el usuario.
"""
import json
import numpy as np
from scipy.spatial import cKDTree
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path(__file__).parent / "data"

# ============================================================
# REFUGIOS CON COORDENADAS VERIFICADAS
# ============================================================

REFUGIOS = [
    # --- DENTRO DE RENACIMIENTO ---
    {
        "id": "R01", "nombre": "Primaria Benemérito de las Américas",
        "alias": "", "tipo": "primaria", "unificada": False,
        "direccion": "Calle Leonardo Bravo No. 1, Col. Ciudad Renacimiento, CP 39715",
        "estatus": "dentro", "lat": 16.89678152, "lon": -99.81578521
    },
    {
        "id": "R02", "nombre": "Primaria Ignacio M. Altamirano / Estefanía Castañeda",
        "alias": "Estefanía Castañeda (mismo plantel)", "tipo": "primaria", "unificada": True,
        "direccion": "Av. Ferretería la Ceiba, Arroyo Seco, CP 39715",
        "estatus": "dentro", "lat": 16.900421, "lon": -99.812858
    },
    {
        "id": "R03", "nombre": "Plantel Adolfo López Mateos / Carlos A. Carrillo",
        "alias": "Mismo plantel físico", "tipo": "primaria", "unificada": True,
        "direccion": "Av. Juan R. Escudero, Renacimiento, CP 39715",
        "estatus": "dentro", "lat": 16.896285, "lon": -99.82244
    },
    {
        "id": "R04", "nombre": "Jardín de Niños Moisés Guevara",
        "alias": "", "tipo": "jardin", "unificada": False,
        "direccion": "Calle Juan R. Escudero, Renacimiento, CP 39715",
        "estatus": "dentro", "lat": 16.896835, "lon": -99.821913
    },
    {
        "id": "R05", "nombre": "Escuela Primaria Prof. Raúl Isidro Burgos",
        "alias": "", "tipo": "primaria", "unificada": False,
        "direccion": "Calle Costa Azul, Renacimiento, CP 39715",
        "estatus": "dentro", "lat": 16.892307, "lon": -99.828635
    },
    {
        "id": "R06", "nombre": "Plantel Jaime Torres Bodet / Antonio I. Delgado",
        "alias": "Mismo plantel físico", "tipo": "primaria", "unificada": True,
        "direccion": "Río Yolotla 101, Renacimiento, CP 39715",
        "estatus": "dentro", "lat": 16.885551, "lon": -99.824772
    },
    {
        "id": "R07", "nombre": "Escuela Primaria Gabriela Mistral",
        "alias": "", "tipo": "primaria", "unificada": False,
        "direccion": "Av. Palmasola, Renacimiento, CP 39715",
        "estatus": "dentro", "lat": 16.890145, "lon": -99.825202
    },
    {
        "id": "R08", "nombre": "Escuela Primaria Lázaro Cárdenas",
        "alias": "", "tipo": "primaria", "unificada": False,
        "direccion": "Calle Nuxco, Renacimiento, CP 39715",
        "estatus": "dentro", "lat": 16.890551, "lon": -99.833422
    },
    {
        "id": "R09", "nombre": "Escuela Primaria Francisco Sarabia",
        "alias": "", "tipo": "primaria", "unificada": False,
        "direccion": "Calle José María Izazaga 14, Renacimiento, CP 39715",
        "estatus": "dentro", "lat": 16.890378, "lon": -99.819624
    },
    {
        "id": "R10", "nombre": "CETis 90 Julián Blanco Jiménez",
        "alias": "", "tipo": "cetis", "unificada": False,
        "direccion": "Calle Alta Quebradora, Renacimiento, CP 39715",
        "estatus": "dentro", "lat": 16.890039, "lon": -99.834641
    },
    {
        "id": "R11", "nombre": "CETis 116 Antonia Nava de Catalán",
        "alias": "", "tipo": "cetis", "unificada": False,
        "direccion": "Blvd. Gral. Vicente Guerrero Saldaña No. 1, CP 39715",
        "estatus": "pegado", "lat": 16.88854, "lon": -99.836197
    },
    {
        "id": "R12", "nombre": "Secundaria General N. 49 Margarito Damián Vargas",
        "alias": "", "tipo": "secundaria", "unificada": False,
        "direccion": "Calle Alta Laja s/n, Renacimiento, CP 39715",
        "estatus": "dentro", "lat": 16.888673, "lon": -99.82771
    },
    {
        "id": "R13", "nombre": "Desarrollo Infantil y Juvenil Renacimiento A.C.",
        "alias": "", "tipo": "centro_educativo", "unificada": False,
        "direccion": "Calle Juan R. Escudero, Renacimiento, CP 39715",
        "estatus": "dentro", "lat": 16.895401, "lon": -99.82392
    },
    {
        "id": "R14", "nombre": "Secundaria Técnica 68 Renacimiento",
        "alias": "", "tipo": "secundaria", "unificada": False,
        "direccion": "And. 24 de Febrero s/n, Col. Fidel Velázquez, CP 39715",
        "estatus": "pegado", "lat": 16.88919015, "lon": -99.83428247
    },
    {
        "id": "R15", "nombre": "Jardín de Niños Adolfo López Mateos",
        "alias": "", "tipo": "jardin", "unificada": False,
        "direccion": "Calle Olímpica 630, Renacimiento, CP 39715",
        "estatus": "dentro", "lat": 16.888435, "lon": -99.827162
    },
    # --- FUERA DE RENACIMIENTO (mencionados por usuario) ---
    {
        "id": "R16", "nombre": "Jardín de Niños Manuel Acuña",
        "alias": "", "tipo": "jardin", "unificada": False,
        "direccion": "Calle Del Valle s/n, Col. Agrícola, CP 39713",
        "estatus": "fuera", "lat": 16.90665589, "lon": -99.81274317
    },
    {
        "id": "R17", "nombre": "Jardín de Niños Luis Hidalgo Monroy",
        "alias": "", "tipo": "jardin", "unificada": False,
        "direccion": "Calle 20 de Noviembre, Col. La Popular, CP 39780",
        "estatus": "fuera", "lat": 16.884017, "lon": -99.830993
    },
    # --- REVISAR ---
    {
        "id": "R18", "nombre": "Esc. Prim. Francisco Pérez Ríos",
        "alias": "Ubicación a revisar", "tipo": "primaria", "unificada": False,
        "direccion": "Calle Las Cruces s/n, Col. Renacimiento / Electricistas, CP 39715",
        "estatus": "revisar", "lat": 16.90048029, "lon": -99.82373754
    },
]


def main():
    with open(DATA_DIR / "nodos_calles.json", "r", encoding="utf-8") as f:
        nodos = json.load(f)
    with open(DATA_DIR / "aristas_calles.json", "r", encoding="utf-8") as f:
        aristas = json.load(f)

    # Reset school nodes
    for n in nodos:
        if n["tipo"] == "escuela":
            n["tipo"] = "interseccion"

    # KDTree
    coords = np.array([(n["lat"], n["lon"]) for n in nodos])
    tree = cKDTree(coords)

    escuelas = []
    for ref in REFUGIOS:
        dist, idx = tree.query([ref["lat"], ref["lon"]])
        nearest = nodos[idx]
        dist_m = dist * 111000

        escuelas.append({
            "id": ref["id"],
            "nombre": ref["nombre"],
            "alias": ref["alias"],
            "tipo": ref["tipo"],
            "unificada": ref["unificada"],
            "nodo_id": nearest["id"],
            "lat": ref["lat"],
            "lon": ref["lon"],
            "direccion": ref["direccion"],
            "estatus": ref["estatus"]
        })

        nodos[idx]["tipo"] = "escuela"
        nodos[idx]["nombre"] = ref["nombre"]
        print(f'{ref["id"]}: {ref["nombre"][:45]:45s} -> nodo {nearest["id"]} ({dist_m:.0f}m) [{ref["estatus"]}]')

    # Enrich node names
    nodo_calles = defaultdict(set)
    for a in aristas:
        nombre = a["nombre_calle"]
        if nombre and nombre != "Sin nombre":
            for parte in nombre.split(","):
                p = parte.strip()
                if p:
                    nodo_calles[a["origen"]].add(p)
                    nodo_calles[a["destino"]].add(p)

    nodos_esc = {e["nodo_id"]: e["nombre"] for e in escuelas}
    adj = defaultdict(set)
    for a in aristas:
        adj[a["origen"]].add(a["destino"])
        adj[a["destino"]].add(a["origen"])

    sin = 0
    for nodo in nodos:
        nid = nodo["id"]
        if nid in nodos_esc:
            nodo["nombre"] = nodos_esc[nid]
            nodo["tipo"] = "escuela"
            continue
        calles = nodo_calles.get(nid, set())
        if calles:
            cl = sorted(calles)
            nodo["nombre"] = f"{cl[0]} / {cl[1]}" if len(cl) >= 2 else cl[0]
        else:
            visitados = {nid}
            cola = list(adj[nid])
            ok = False
            for _ in range(3):
                sig = []
                for v in cola:
                    if v in visitados: continue
                    visitados.add(v)
                    vc = nodo_calles.get(v, set())
                    if vc:
                        nodo["nombre"] = f"Cerca de {sorted(vc)[0]}"
                        ok = True
                        break
                    sig.extend(adj[v])
                if ok: break
                cola = sig
            if not ok:
                sin += 1
                nodo["nombre"] = f"Punto {sin}"

    with open(DATA_DIR / "escuelas.json", "w", encoding="utf-8") as f:
        json.dump(escuelas, f, ensure_ascii=False, indent=2)
    with open(DATA_DIR / "nodos_calles.json", "w", encoding="utf-8") as f:
        json.dump(nodos, f, ensure_ascii=False, indent=2)

    con = sum(1 for n in nodos if not n["nombre"].startswith("Punto"))
    print(f"\nNodos con nombre: {con}/{len(nodos)}")
    print(f"Refugios: {len(escuelas)}")


if __name__ == "__main__":
    main()
