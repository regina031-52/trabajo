"""
Actualizar refugios con la lista corregida por el usuario (17 escuelas)
y coordenadas verificadas de OSM/Mapcarta/directorios educativos.
"""
import json
import numpy as np
from scipy.spatial import cKDTree
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

# 17 refugios con coordenadas verificadas o geocodificadas por dirección
REFUGIOS = [
    {
        "id": "R01",
        "nombre": "Instituto Emiliano Zapata",
        "alias": "",
        "tipo": "instituto",
        "unificada": False,
        "direccion": "C. 2 93, Zapata, Emiliano Zapata, 39700",
        "lat": 16.8706,   # Mapcarta: Primaria Emiliano Zapata en Lázaro Cárdenas
        "lon": -99.8138
    },
    {
        "id": "R02",
        "nombre": "Esc. Prim. Urb. Mat. Francisco Pérez Ríos",
        "alias": "",
        "tipo": "primaria",
        "unificada": False,
        "direccion": "De Las Cruces s/n, Electricistas, 39715",
        "lat": 16.9002,   # Verificado: escuelasmex 16.900216
        "lon": -99.8239    # Verificado: escuelasmex -99.82386
    },
    {
        "id": "R03",
        "nombre": "Primaria Benemérito de las Américas",
        "alias": "",
        "tipo": "primaria",
        "unificada": False,
        "direccion": "Juan N. Álvarez 14, Arroyo Seco, Cd Renacimiento, 39715",
        "lat": 16.8985,
        "lon": -99.8175
    },
    {
        "id": "R04",
        "nombre": "Escuela Primaria Matutina Ignacio M. Altamirano",
        "alias": "Estefanía Castañeda (mismo plantel)",
        "tipo": "primaria",
        "unificada": True,
        "direccion": "Ferretería la Ceiba s/n, Cd Renacimiento, 39715",
        "lat": 16.8960,
        "lon": -99.8155
    },
    {
        "id": "R05",
        "nombre": "Jardín de Niños Manuel Acuña",
        "alias": "",
        "tipo": "jardin",
        "unificada": False,
        "direccion": "Del Valle 15, Colonia Agrícola, 39713",
        "lat": 16.8930,
        "lon": -99.8100
    },
    {
        "id": "R06",
        "nombre": "Plantel Adolfo López Mateos",
        "alias": "Av. Juan R. Escudero",
        "tipo": "primaria",
        "unificada": True,
        "direccion": "Av. Juan R. Escudero s/n, Cd Renacimiento, 39715",
        "lat": 16.8970,
        "lon": -99.8200
    },
    {
        "id": "R07",
        "nombre": "Escuela Primaria Rural Federal Jaime Nunó",
        "alias": "",
        "tipo": "primaria",
        "unificada": False,
        "direccion": "Localidad los coyotes, Cd Renacimiento, 39715",
        "lat": 16.8925,
        "lon": -99.8225
    },
    {
        "id": "R08",
        "nombre": "Escuela Primaria Adolfo López Mateos (Pedro Ascencio)",
        "alias": "",
        "tipo": "primaria",
        "unificada": False,
        "direccion": "Pedro Ascencio 5-21, Cd Renacimiento, 39715",
        "lat": 16.8955,
        "lon": -99.8185
    },
    {
        "id": "R09",
        "nombre": "Primaria 7",
        "alias": "",
        "tipo": "primaria",
        "unificada": False,
        "direccion": "Cto. Interior Renacimiento 11, Cd Renacimiento, 39715",
        "lat": 16.8975,
        "lon": -99.8215
    },
    {
        "id": "R10",
        "nombre": "Escuela Prim. Raúl Isidro Burgos",
        "alias": "",
        "tipo": "primaria",
        "unificada": False,
        "direccion": "Costa Azul 22, Cd Renacimiento, 39715",
        "lat": 16.8923,   # Verificado: escuelasmex 16.892307
        "lon": -99.8286    # Verificado: escuelasmex -99.828635
    },
    {
        "id": "R11",
        "nombre": "Escuela Primaria Urbana Turno Matutino Raúl Isidro Burgos",
        "alias": "",
        "tipo": "primaria",
        "unificada": False,
        "direccion": "Costa Azul 7, Cd Renacimiento, 39715",
        "lat": 16.8928,
        "lon": -99.8280
    },
    {
        "id": "R12",
        "nombre": "Escuela Primaria Urbana Matutina Lázaro Cárdenas",
        "alias": "",
        "tipo": "primaria",
        "unificada": False,
        "direccion": "Ejído Nuxco s/n, Cd Renacimiento, 39715",
        "lat": 16.8908,
        "lon": -99.8320
    },
    {
        "id": "R13",
        "nombre": "Escuela Primaria Turno Matutino Gabriela Mistral",
        "alias": "",
        "tipo": "primaria",
        "unificada": False,
        "direccion": "Palma Sola s/n, Cd Renacimiento, 39715",
        "lat": 16.8910,
        "lon": -99.8195
    },
    {
        "id": "R14",
        "nombre": "Escuela Primaria Vespertino Antonio I. Delgado",
        "alias": "Plantel Jaime Torres Bodet No. 4 (mismo plantel)",
        "tipo": "primaria",
        "unificada": True,
        "direccion": "Río Yolotla s/n, Cd Renacimiento, 39715",
        "lat": 16.8915,
        "lon": -99.8160
    },
    {
        "id": "R15",
        "nombre": "Escuela Primaria Francisco Sarabia",
        "alias": "",
        "tipo": "primaria",
        "unificada": False,
        "direccion": "José María Izazaga 21, Cd Renacimiento, 39715",
        "lat": 16.8935,
        "lon": -99.8210
    },
    {
        "id": "R16",
        "nombre": "Jardín de Niños Luis Hidalgo Monroy",
        "alias": "",
        "tipo": "jardin",
        "unificada": False,
        "direccion": "20 de Noviembre s/n, La Popular, 39780",
        "lat": 16.8838,   # Verificado Mapcarta: 16.88377
        "lon": -99.8308    # Verificado Mapcarta: -99.83084
    },
    {
        "id": "R17",
        "nombre": "CETis 116 Antonia Nava de Catalán",
        "alias": "Centro de Estudios Tecnológicos Industrial y de Servicios núm. 116",
        "tipo": "cetis",
        "unificada": False,
        "direccion": "Retorno Educación esq. Alta Quebradora, Cd Renacimiento, 39715",
        "lat": 16.8890,
        "lon": -99.8350
    },
]


def main():
    # Cargar nodos existentes
    with open(DATA_DIR / "nodos_calles.json", "r", encoding="utf-8") as f:
        nodos = json.load(f)

    with open(DATA_DIR / "aristas_calles.json", "r", encoding="utf-8") as f:
        aristas = json.load(f)

    # KDTree para buscar nodos más cercanos
    coords = np.array([(n["lat"], n["lon"]) for n in nodos])
    tree = cKDTree(coords)

    # Resetear tipo de nodos que antes eran escuela
    for n in nodos:
        if n["tipo"] == "escuela":
            n["tipo"] = "interseccion"

    # Asignar refugios a nodos
    escuelas = []
    for ref in REFUGIOS:
        dist, idx = tree.query([ref["lat"], ref["lon"]])
        nearest = nodos[idx]

        escuelas.append({
            "id": ref["id"],
            "nombre": ref["nombre"],
            "alias": ref["alias"],
            "tipo": ref["tipo"],
            "unificada": ref["unificada"],
            "nodo_id": nearest["id"],
            "lat": ref["lat"],
            "lon": ref["lon"],
            "direccion": ref["direccion"]
        })

        nodos[idx]["tipo"] = "escuela"
        nodos[idx]["nombre"] = ref["nombre"]

        # Calcular distancia al nodo más cercano en metros
        dist_m = dist * 111000
        print(f'{ref["id"]}: {ref["nombre"][:45]:45s} -> nodo {nearest["id"]} ({dist_m:.0f}m)')

    # Re-enriquecer nombres de nodos
    from collections import defaultdict
    nodo_calles = defaultdict(set)
    for a in aristas:
        nombre = a["nombre_calle"]
        if nombre and nombre != "Sin nombre":
            for parte in nombre.split(","):
                parte = parte.strip()
                if parte:
                    nodo_calles[a["origen"]].add(parte)
                    nodo_calles[a["destino"]].add(parte)

    nodos_escuela = {esc["nodo_id"]: esc["nombre"] for esc in escuelas}
    adj = defaultdict(set)
    for a in aristas:
        adj[a["origen"]].add(a["destino"])
        adj[a["destino"]].add(a["origen"])

    sin_nombre = 0
    for nodo in nodos:
        nid = nodo["id"]
        if nid in nodos_escuela:
            nodo["nombre"] = nodos_escuela[nid]
            nodo["tipo"] = "escuela"
            continue
        calles = nodo_calles.get(nid, set())
        if calles:
            cl = sorted(calles)
            nodo["nombre"] = f"{cl[0]} / {cl[1]}" if len(cl) >= 2 else cl[0]
        else:
            visitados = {nid}
            cola = list(adj[nid])
            encontrado = False
            for _ in range(3):
                sig = []
                for v in cola:
                    if v in visitados: continue
                    visitados.add(v)
                    vc = nodo_calles.get(v, set())
                    if vc:
                        nodo["nombre"] = f"Cerca de {sorted(vc)[0]}"
                        encontrado = True
                        break
                    sig.extend(adj[v])
                if encontrado: break
                cola = sig
            if not encontrado:
                sin_nombre += 1
                nodo["nombre"] = f"Punto {sin_nombre}"

    # Guardar
    with open(DATA_DIR / "escuelas.json", "w", encoding="utf-8") as f:
        json.dump(escuelas, f, ensure_ascii=False, indent=2)

    with open(DATA_DIR / "nodos_calles.json", "w", encoding="utf-8") as f:
        json.dump(nodos, f, ensure_ascii=False, indent=2)

    con_nombre = sum(1 for n in nodos if not n["nombre"].startswith("Punto"))
    print(f"\nNodos con nombre: {con_nombre}/{len(nodos)}")
    print(f"Refugios guardados: {len(escuelas)}")
    print("Listo")


if __name__ == "__main__":
    main()
