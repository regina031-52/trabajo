# Refugios A* - PRD

## Problem Statement
Aplicación para encontrar la ruta más corta al refugio (escuela) más cercano usando el algoritmo A*. Colonia Renacimiento, Acapulco, Guerrero. Red peatonal real descargada de OpenStreetMap via OSMnx.

## Architecture
- **Backend**: FastAPI + NetworkX + OSMnx
- **Frontend**: React + Leaflet (react-leaflet) + Tailwind CSS
- **Database**: MongoDB (available, not heavily used - data from JSON files)
- **Algorithm**: A* pathfinding (custom implementation)

## User Personas
- Residentes de Colonia Renacimiento buscando el refugio/escuela más cercano
- Protección civil/autoridades planificando rutas de evacuación

## Core Requirements
1. Grafo real de calles de OpenStreetMap
2. 18 escuelas como refugios fijos (con unificación de doble turno)
3. Algoritmo A* para ruta más corta
4. Mapa interactivo con Leaflet
5. Búsqueda por nombre de calle
6. Distancia y tiempo estimado de caminata

## What's Been Implemented (Feb 2026)
- [x] Descarga de red peatonal OSM (1792 nodos, 2355 aristas)
- [x] 18 escuelas/refugios con datos del usuario
- [x] Algoritmo A* personalizado
- [x] Mapa interactivo con CartoDB Dark Matter
- [x] Búsqueda por calle con autocompletado (tolerante a acentos)
- [x] Nombres de calles reales en intersecciones
- [x] Etiquetas permanentes de escuelas en el mapa
- [x] Distancia y tiempo estimado
- [x] Lista ordenada de todas las escuelas
- [x] Diseño Control Room con glassmorphism

## Prioritized Backlog
- P1: Geolocalización del navegador (GPS)
- P1: Click en el mapa para seleccionar ubicación
- P2: Exportar ruta como imagen/PDF
- P2: Modo offline (PWA)
- P3: Instrucciones paso a paso de la ruta
