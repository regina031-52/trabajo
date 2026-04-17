"""
Script para enriquecer los nombres de los nodos usando los nombres de calles
de las aristas que conectan a cada nodo.
"""

import json
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path(__file__).parent / "data"

def enrich_node_names():
    """
    Asigna nombres descriptivos a cada nodo basándose en las calles
    que se cruzan en esa intersección.
    """
    # Cargar datos
    with open(DATA_DIR / "nodos_calles.json", "r", encoding="utf-8") as f:
        nodos = json.load(f)
    
    with open(DATA_DIR / "aristas_calles.json", "r", encoding="utf-8") as f:
        aristas = json.load(f)
    
    with open(DATA_DIR / "escuelas.json", "r", encoding="utf-8") as f:
        escuelas = json.load(f)
    
    # Crear mapa de nodo_id -> set de nombres de calles
    nodo_calles = defaultdict(set)
    
    for arista in aristas:
        nombre = arista["nombre_calle"]
        if nombre and nombre != "Sin nombre":
            # Limpiar nombres compuestos (separados por coma)
            for parte in nombre.split(","):
                parte = parte.strip()
                if parte:
                    nodo_calles[arista["origen"]].add(parte)
                    nodo_calles[arista["destino"]].add(parte)
    
    # Crear set de nodos que son escuelas
    nodos_escuela = {}
    for esc in escuelas:
        nodos_escuela[esc["nodo_id"]] = esc["nombre"]
    
    # Actualizar nombres de nodos
    sin_nombre_count = 0
    for nodo in nodos:
        nodo_id = nodo["id"]
        
        # Si es escuela, mantener nombre de escuela
        if nodo_id in nodos_escuela:
            nodo["nombre"] = nodos_escuela[nodo_id]
            nodo["tipo"] = "escuela"
            continue
        
        # Si tiene calles asociadas, usar nombres de calles
        calles = nodo_calles.get(nodo_id, set())
        if calles:
            calles_list = sorted(calles)
            if len(calles_list) >= 2:
                # Intersección: mostrar las 2 primeras calles
                nodo["nombre"] = f"{calles_list[0]} / {calles_list[1]}"
            else:
                nodo["nombre"] = calles_list[0]
        else:
            sin_nombre_count += 1
            nodo["nombre"] = f"Punto {sin_nombre_count}"
    
    # Guardar nodos actualizados
    with open(DATA_DIR / "nodos_calles.json", "w", encoding="utf-8") as f:
        json.dump(nodos, f, ensure_ascii=False, indent=2)
    
    # Estadísticas
    con_calle = sum(1 for n in nodos if "/" in n["nombre"] or any(
        n["nombre"].startswith(p) for p in ["Calle", "Avenida", "Andador", "Privada", "Cerrada", "Escalera"]
    ))
    print(f"Nodos totales: {len(nodos)}")
    print(f"Nodos con nombre de calle: {con_calle}")
    print(f"Nodos sin nombre: {sin_nombre_count}")
    print(f"Nodos escuela: {len(nodos_escuela)}")
    
    # Mostrar algunos ejemplos
    print("\nEjemplos de nombres:")
    ejemplos = [n for n in nodos if "/" in n["nombre"]][:10]
    for n in ejemplos:
        print(f"  {n['id']}: {n['nombre']}")

if __name__ == "__main__":
    enrich_node_names()
