# Refugios A* - PRD

## Problem Statement
Aplicación para encontrar la ruta más corta al refugio (escuela) más cercano usando el algoritmo A*. Colonia Renacimiento, Acapulco, Guerrero. Red peatonal real de OpenStreetMap.

## Architecture
- **Backend**: FastAPI + NetworkX + OSMnx
- **Frontend**: React + Leaflet (react-leaflet) + Tailwind CSS
- **Database**: MongoDB (available)
- **Algorithm**: A* pathfinding (custom implementation)
- **Standalone**: Script Python para compartir con compañeros

## What's Been Implemented (Feb 2026)
- [x] Red peatonal real OSM (1792 nodos, 2355 aristas)
- [x] 18 escuelas/refugios con unificación doble turno
- [x] Algoritmo A* personalizado
- [x] Mapa interactivo Leaflet (CartoDB Dark Matter)
- [x] Búsqueda por calle con autocompletado (tolerante a acentos)
- [x] Nombres reales en intersecciones y escuelas
- [x] **Click en mapa** para seleccionar ubicación
- [x] **Instrucciones paso a paso** (giros, calles, distancias)
- [x] **Sugerencias de emergencia** (kit de 15 items)
- [x] **Script Python standalone** (refugios_astar_standalone.py)
- [x] Distancia y tiempo estimado caminando
- [x] Lista ordenada de 18 escuelas por distancia

## Prioritized Backlog
- P1: Geolocalización GPS del navegador
- P2: Exportar ruta como imagen/PDF
- P2: Modo offline (PWA)
