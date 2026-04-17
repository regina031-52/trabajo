# Refugios A* - PRD

## Problem Statement
App para encontrar ruta más corta al refugio (escuela) más cercano usando A*. Colonia Renacimiento, Acapulco, Guerrero.

## Architecture
- Backend: FastAPI + NetworkX + OSMnx
- Frontend: React + Leaflet + Tailwind CSS
- Standalone: refugios_astar_standalone.py + data/ (4 JSONs)

## Implemented (Feb 2026)
- [x] Red peatonal real OSM (1792 nodos, 4766 aristas)
- [x] 18 escuelas/refugios con doble turno
- [x] Algoritmo A* personalizado
- [x] Mapa interactivo Leaflet (CartoDB Dark Matter)
- [x] Búsqueda por calle sin prefijo (tolerante a acentos)
- [x] Click en mapa para seleccionar ubicación
- [x] Geolocalización GPS del navegador
- [x] Panel colapsable (ocultar/mostrar)
- [x] Instrucciones paso a paso con giros
- [x] Kit de emergencia (15 items)
- [x] Script Python standalone para compañeros
- [x] 1790 nodos con nombres de calles reales
- [x] Etiquetas permanentes de escuelas en mapa

## Backlog
- P2: Exportar ruta como imagen/PDF
- P2: Modo offline (PWA)
- P3: Compartir ruta por WhatsApp
