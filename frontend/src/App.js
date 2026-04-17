import { useState, useEffect, useCallback, useRef } from "react";
import "@/App.css";
import axios from "axios";
import { MapContainer, TileLayer, Polyline, CircleMarker, Popup, Tooltip, useMap, useMapEvents } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import {
  MapPin, Path, Timer, Ruler, Buildings, NavigationArrow,
  Warning, List, MagnifyingGlass, X, CaretDown, CaretUp,
  Crosshair, FirstAid, Backpack, ArrowBendDownRight, FlagCheckered, MapTrifold
} from "@phosphor-icons/react";
import { ScrollArea } from "@/components/ui/scroll-area";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

/* ===== Map Controller ===== */
function MapController({ center, zoom }) {
  const map = useMap();
  useEffect(() => {
    if (center) map.setView(center, zoom || 15);
  }, [center, zoom, map]);
  return null;
}

/* ===== Click Handler on Map ===== */
function MapClickHandler({ onMapClick }) {
  useMapEvents({
    click(e) {
      onMapClick(e.latlng.lat, e.latlng.lng);
    }
  });
  return null;
}

/* ===== Search Input ===== */
function SearchInput({ onSelect, selectedNode, onClear }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const debounceRef = useRef(null);
  const wrapperRef = useRef(null);

  useEffect(() => {
    function handleClickOutside(e) {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) setIsOpen(false);
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Sync input when node selected via map click
  useEffect(() => {
    if (selectedNode) setQuery(selectedNode.nombre);
  }, [selectedNode]);

  const buscar = useCallback(async (texto) => {
    if (texto.length < 2) { setResults([]); setIsOpen(false); return; }
    setLoading(true);
    try {
      const res = await axios.get(`${API}/buscar-nodos`, { params: { q: texto } });
      setResults(res.data);
      setIsOpen(res.data.length > 0);
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  }, []);

  const handleChange = (e) => {
    const val = e.target.value;
    setQuery(val);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => buscar(val), 300);
  };

  const handleSelect = (nodo) => {
    setQuery(nodo.nombre);
    setIsOpen(false);
    setResults([]);
    onSelect(nodo);
  };

  const handleClear = () => {
    setQuery("");
    setResults([]);
    setIsOpen(false);
    onClear();
  };

  return (
    <div ref={wrapperRef} className="relative" data-testid="search-wrapper">
      <div className="relative">
        <MagnifyingGlass weight="bold" className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400" size={18} />
        <input
          type="text"
          value={query}
          onChange={handleChange}
          onFocus={() => { if (results.length > 0) setIsOpen(true); }}
          placeholder="Escribe tu calle o haz click en el mapa"
          className="custom-select pl-10 pr-10"
          data-testid="search-input"
        />
        {(query || selectedNode) && (
          <button onClick={handleClear} className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-white transition-colors" data-testid="search-clear-btn">
            <X size={16} />
          </button>
        )}
      </div>
      {loading && (
        <div className="absolute right-10 top-1/2 -translate-y-1/2">
          <div className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }} />
        </div>
      )}
      {isOpen && results.length > 0 && (
        <div className="absolute top-full left-0 right-0 mt-1 max-h-60 overflow-y-auto rounded-lg z-50" style={{ background: "rgba(9,9,11,0.95)", backdropFilter: "blur(16px)", border: "1px solid rgba(255,255,255,0.15)" }} data-testid="search-results">
          {results.map((nodo, idx) => (
            <button key={nodo.id} onClick={() => handleSelect(nodo)} className="w-full text-left px-4 py-3 hover:bg-white/10 transition-colors border-b border-white/5 last:border-0" data-testid={`search-result-${idx}`}>
              <p className="text-white text-sm font-medium truncate">{nodo.nombre}</p>
              <p className="text-zinc-500 text-xs mt-0.5">{nodo.tipo === "escuela" ? "Refugio" : "Interseccion"}</p>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

/* ===== Instrucciones Paso a Paso ===== */
function InstruccionesPanel({ instrucciones }) {
  const [abierto, setAbierto] = useState(false);

  if (!instrucciones || instrucciones.length === 0) return null;

  return (
    <div data-testid="instrucciones-panel">
      <button
        className="w-full flex items-center justify-center gap-2 py-2 text-zinc-400 hover:text-white transition-colors text-sm"
        onClick={() => setAbierto(!abierto)}
        data-testid="toggle-instrucciones-btn"
      >
        <ArrowBendDownRight weight="bold" />
        {abierto ? "Ocultar" : "Ver"} instrucciones paso a paso ({instrucciones.length})
        {abierto ? <CaretUp size={14} /> : <CaretDown size={14} />}
      </button>

      {abierto && (
        <ScrollArea className="h-56" data-testid="instrucciones-list">
          <div className="space-y-0 pr-4">
            {instrucciones.map((paso, idx) => {
              const esUltimo = idx === instrucciones.length - 1;
              return (
                <div key={idx} className="flex gap-3 py-2" data-testid={`instruccion-${idx}`}>
                  {/* Línea vertical + punto */}
                  <div className="flex flex-col items-center w-6 flex-shrink-0">
                    <div className={`w-5 h-5 rounded-full flex items-center justify-center text-xs font-mono font-bold ${esUltimo ? "bg-[#CCFF00] text-black" : "bg-white/10 text-zinc-300"}`}>
                      {esUltimo ? <FlagCheckered size={12} /> : paso.paso}
                    </div>
                    {!esUltimo && <div className="w-px flex-1 bg-white/10 mt-1" />}
                  </div>
                  {/* Texto */}
                  <div className="flex-1 min-w-0 pb-1">
                    <p className={`text-sm leading-snug ${esUltimo ? "text-[#CCFF00] font-semibold" : "text-zinc-200"}`}>
                      {paso.instruccion}
                    </p>
                    {!esUltimo && (
                      <p className="text-xs text-zinc-500 font-mono mt-0.5">
                        {paso.distancia_m >= 1000 ? `${(paso.distancia_m/1000).toFixed(1)} km` : `${Math.round(paso.distancia_m)} m`}
                        {" · "}total: {paso.acumulado_m >= 1000 ? `${(paso.acumulado_m/1000).toFixed(1)} km` : `${Math.round(paso.acumulado_m)} m`}
                      </p>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </ScrollArea>
      )}
    </div>
  );
}

/* ===== Sugerencias de Emergencia ===== */
function SugerenciasPanel({ sugerencias }) {
  const [abierto, setAbierto] = useState(false);

  if (!sugerencias || sugerencias.length === 0) return null;

  return (
    <div data-testid="sugerencias-panel">
      <button
        className="w-full flex items-center justify-center gap-2 py-2 text-[#FF0055] hover:text-[#FF3377] transition-colors text-sm font-medium"
        onClick={() => setAbierto(!abierto)}
        data-testid="toggle-sugerencias-btn"
      >
        <Backpack weight="bold" />
        {abierto ? "Ocultar" : "Que llevar al refugio"}
        {abierto ? <CaretUp size={14} /> : <CaretDown size={14} />}
      </button>

      {abierto && (
        <div className="mt-2 p-4 rounded-xl" style={{ background: "rgba(255,0,85,0.08)", border: "1px solid rgba(255,0,85,0.2)" }} data-testid="sugerencias-list">
          <div className="flex items-center gap-2 mb-3">
            <FirstAid weight="fill" className="text-[#FF0055]" size={18} />
            <p className="text-white text-sm font-semibold">Kit de emergencia recomendado</p>
          </div>
          <ScrollArea className="h-40">
            <ul className="space-y-2 pr-4">
              {sugerencias.map((item, idx) => (
                <li key={idx} className="flex items-start gap-2 text-sm text-zinc-300" data-testid={`sugerencia-${idx}`}>
                  <span className="text-[#FF0055] mt-0.5 flex-shrink-0">&#9679;</span>
                  {item}
                </li>
              ))}
            </ul>
          </ScrollArea>
        </div>
      )}
    </div>
  );
}

/* ===== APP PRINCIPAL ===== */
function App() {
  const [escuelas, setEscuelas] = useState([]);
  const [nodoSeleccionado, setNodoSeleccionado] = useState(null);
  const [resultado, setResultado] = useState(null);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState(null);
  const [mapCenter, setMapCenter] = useState([16.8697, -99.8827]);
  const [mostrarTodas, setMostrarTodas] = useState(false);
  const [stats, setStats] = useState(null);
  const [buscandoNodo, setBuscandoNodo] = useState(false);

  // Cargar datos iniciales
  useEffect(() => {
    const cargarDatos = async () => {
      try {
        const [escuelasRes, statsRes] = await Promise.all([
          axios.get(`${API}/escuelas`),
          axios.get(`${API}/grafo/stats`)
        ]);
        setEscuelas(escuelasRes.data);
        setStats(statsRes.data);
      } catch (err) {
        console.error("Error cargando datos:", err);
        setError("Error al cargar los datos de la red");
      }
    };
    cargarDatos();
  }, []);

  // Click en mapa -> encontrar nodo cercano
  const handleMapClick = useCallback(async (lat, lng) => {
    setBuscandoNodo(true);
    try {
      const res = await axios.post(`${API}/nodo-cercano`, { lat, lon: lng });
      setNodoSeleccionado(res.data);
      setMapCenter([res.data.lat, res.data.lon]);
      setResultado(null);
      setError(null);
    } catch (err) {
      console.error("Error buscando nodo cercano:", err);
    } finally {
      setBuscandoNodo(false);
    }
  }, []);

  const handleNodeSelect = (nodo) => {
    setNodoSeleccionado(nodo);
    setMapCenter([nodo.lat, nodo.lon]);
    setResultado(null);
    setError(null);
  };

  const handleClear = () => {
    setNodoSeleccionado(null);
    setResultado(null);
    setError(null);
  };

  const calcularRuta = useCallback(async () => {
    if (!nodoSeleccionado) { setError("Selecciona tu ubicacion primero"); return; }
    setCargando(true);
    setError(null);
    setResultado(null);
    try {
      const response = await axios.post(`${API}/calcular-ruta`, { nodo_origen: nodoSeleccionado.id });
      if (response.data.exito) {
        setResultado(response.data);
        if (response.data.mejor_ruta?.ruta_coordenadas?.length > 0) {
          const coords = response.data.mejor_ruta.ruta_coordenadas;
          const midIndex = Math.floor(coords.length / 2);
          setMapCenter([coords[midIndex].lat, coords[midIndex].lon]);
        }
      } else {
        setError(response.data.mensaje);
      }
    } catch (err) {
      console.error("Error:", err);
      setError("Error al calcular la ruta");
    } finally {
      setCargando(false);
    }
  }, [nodoSeleccionado]);

  return (
    <div className="relative w-screen h-screen overflow-hidden" data-testid="app-container">
      {/* Mapa */}
      <MapContainer center={mapCenter} zoom={15} className="w-full h-full z-0" zoomControl={true} data-testid="leaflet-map">
        <MapController center={mapCenter} zoom={15} />
        <MapClickHandler onMapClick={handleMapClick} />

        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        />

        {/* Ruta */}
        {resultado?.mejor_ruta?.ruta_coordenadas && (
          <Polyline
            positions={resultado.mejor_ruta.ruta_coordenadas.map(c => [c.lat, c.lon])}
            color="#CCFF00" weight={5} opacity={0.9}
          />
        )}

        {/* Escuelas */}
        {escuelas.map(escuela => {
          const esMejor = resultado?.mejor_ruta?.escuela?.id === escuela.id;
          return (
            <CircleMarker
              key={escuela.id}
              center={[escuela.lat, escuela.lon]}
              radius={esMejor ? 10 : 7}
              fillColor={esMejor ? "#CCFF00" : "#FF0055"}
              color="#FFFFFF" weight={esMejor ? 3 : 2} fillOpacity={0.9}
              data-testid={`school-marker-${escuela.id}`}
            >
              <Tooltip permanent direction="top" offset={[0, -10]} className="school-tooltip">
                <span className="school-tooltip-text">
                  {escuela.nombre.length > 30 ? escuela.nombre.substring(0, 28) + "..." : escuela.nombre}
                </span>
              </Tooltip>
              <Popup className="custom-popup">
                <div className="text-sm" style={{ maxWidth: 220 }}>
                  <strong style={{ color: "#CCFF00" }}>{escuela.nombre}</strong>
                  {escuela.alias && <p style={{ color: "#A1A1AA", fontSize: 11, marginTop: 4 }}>{escuela.alias}</p>}
                  <p style={{ color: "#FF0055", fontSize: 11, marginTop: 4, textTransform: "uppercase" }}>
                    {escuela.tipo}{escuela.unificada && " (doble turno)"}
                  </p>
                </div>
              </Popup>
            </CircleMarker>
          );
        })}

        {/* Ubicación del usuario */}
        {nodoSeleccionado && (
          <CircleMarker
            center={[nodoSeleccionado.lat, nodoSeleccionado.lon]}
            radius={10} fillColor="#00E5FF" color="#FFFFFF" weight={3} fillOpacity={1}
            data-testid="user-location-marker"
          >
            <Tooltip permanent direction="bottom" offset={[0, 10]} className="user-tooltip">
              <span className="user-tooltip-text">Tu ubicacion</span>
            </Tooltip>
          </CircleMarker>
        )}
      </MapContainer>

      {/* Indicador de búsqueda por click */}
      {buscandoNodo && (
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-20 glass-panel px-6 py-3 flex items-center gap-3">
          <div className="spinner" />
          <span className="text-white text-sm">Buscando punto cercano...</span>
        </div>
      )}

      {/* Panel de control */}
      <div className="glass-panel absolute top-6 left-6 w-96 max-h-[calc(100vh-48px)] overflow-hidden animate-slide-in z-10 flex flex-col" data-testid="control-panel">
        <div className="p-6 space-y-4 overflow-y-auto flex-1">
          {/* Header */}
          <div>
            <h1 className="font-heading text-2xl font-semibold text-white tracking-tight flex items-center gap-2">
              <NavigationArrow weight="bold" className="text-[#CCFF00]" />
              Refugios A*
            </h1>
            <p className="text-zinc-400 text-sm mt-1">Colonia Renacimiento, Acapulco</p>
          </div>

          {/* Búsqueda */}
          <div className="space-y-2">
            <label className="data-label flex items-center gap-2">
              <MapPin weight="bold" className="text-[#00E5FF]" />
              Tu ubicacion
            </label>
            <SearchInput onSelect={handleNodeSelect} selectedNode={nodoSeleccionado} onClear={handleClear} />
            {nodoSeleccionado && (
              <p className="text-xs text-[#00E5FF] mt-1 flex items-center gap-1">
                <MapPin weight="fill" size={12} />
                {nodoSeleccionado.nombre}
              </p>
            )}
            {!nodoSeleccionado && (
              <p className="text-xs text-zinc-500 flex items-center gap-1 mt-1">
                <Crosshair size={12} />
                Tambien puedes hacer click en el mapa
              </p>
            )}
          </div>

          {/* Botón calcular */}
          <button
            className="btn-primary w-full flex items-center justify-center gap-2"
            onClick={calcularRuta}
            disabled={cargando || !nodoSeleccionado}
            data-testid="calculate-route-btn"
          >
            {cargando ? (
              <><div className="spinner" />Calculando...</>
            ) : (
              <><Path weight="bold" />Encontrar refugio mas cercano</>
            )}
          </button>

          {/* Error */}
          {error && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 flex items-start gap-3" data-testid="error-message">
              <Warning weight="fill" className="text-red-500 flex-shrink-0 mt-0.5" />
              <p className="text-red-400 text-sm">{error}</p>
            </div>
          )}

          {/* Resultado */}
          {resultado?.mejor_ruta && (
            <div className="space-y-3 animate-slide-in" data-testid="route-result">
              {/* Escuela más cercana */}
              <div className="route-card">
                <div className="flex items-start gap-3">
                  <Buildings weight="fill" className="text-[#FF0055] text-xl flex-shrink-0 mt-1" />
                  <div className="flex-1 min-w-0">
                    <p className="data-label mb-1">Refugio mas cercano</p>
                    <h3 className="text-white font-medium text-base leading-tight" data-testid="nearest-school-name">
                      {resultado.mejor_ruta.escuela.nombre}
                    </h3>
                    {resultado.mejor_ruta.escuela.alias && (
                      <p className="text-zinc-500 text-xs mt-1">{resultado.mejor_ruta.escuela.alias}</p>
                    )}
                    <span className="inline-block mt-2 px-2 py-1 bg-white/10 rounded text-xs text-zinc-300 uppercase">
                      {resultado.mejor_ruta.escuela.tipo}
                    </span>
                  </div>
                </div>
              </div>

              {/* Métricas */}
              <div className="grid grid-cols-2 gap-3">
                <div className="metric-card" data-testid="distance-metric">
                  <div className="flex items-center gap-2 mb-2">
                    <Ruler weight="bold" className="text-[#CCFF00]" />
                    <span className="data-label">Distancia</span>
                  </div>
                  <p className="data-value" style={{ fontSize: 24 }}>
                    {resultado.mejor_ruta.distancia_total >= 1000
                      ? `${(resultado.mejor_ruta.distancia_total / 1000).toFixed(1)} km`
                      : `${Math.round(resultado.mejor_ruta.distancia_total)} m`}
                  </p>
                </div>
                <div className="metric-card" data-testid="time-metric">
                  <div className="flex items-center gap-2 mb-2">
                    <Timer weight="bold" className="text-[#00E5FF]" />
                    <span className="data-label">Caminando</span>
                  </div>
                  <p className="data-value" style={{ fontSize: 24 }}>
                    {resultado.mejor_ruta.tiempo_minutos >= 60
                      ? `${Math.floor(resultado.mejor_ruta.tiempo_minutos / 60)}h ${Math.round(resultado.mejor_ruta.tiempo_minutos % 60)}m`
                      : `${Math.round(resultado.mejor_ruta.tiempo_minutos)} min`}
                  </p>
                </div>
              </div>

              {/* Instrucciones paso a paso */}
              <InstruccionesPanel instrucciones={resultado.mejor_ruta.instrucciones} />

              {/* Sugerencias de emergencia */}
              <SugerenciasPanel sugerencias={resultado.sugerencias_emergencia} />

              {/* Todas las escuelas */}
              <button
                className="w-full flex items-center justify-center gap-2 py-2 text-zinc-400 hover:text-white transition-colors text-sm"
                onClick={() => setMostrarTodas(!mostrarTodas)}
                data-testid="toggle-all-routes-btn"
              >
                <List weight="bold" />
                {mostrarTodas ? "Ocultar" : "Ver"} todas las escuelas ({resultado.todas_rutas.length})
              </button>

              {mostrarTodas && (
                <ScrollArea className="h-48" data-testid="all-schools-list">
                  <div className="space-y-2 pr-4">
                    {resultado.todas_rutas.map((ruta, idx) => (
                      <div key={ruta.escuela.id} className="school-item">
                        <div className="flex items-start justify-between">
                          <div className="flex-1 min-w-0">
                            <p className="text-white text-sm font-medium truncate">
                              {idx + 1}. {ruta.escuela.nombre}
                            </p>
                            <p className="text-zinc-500 text-xs">{ruta.escuela.tipo}</p>
                          </div>
                          <div className="text-right flex-shrink-0 ml-2">
                            <p className="text-[#CCFF00] font-mono text-sm">
                              {ruta.distancia_total >= 1000 ? `${(ruta.distancia_total / 1000).toFixed(1)}km` : `${Math.round(ruta.distancia_total)}m`}
                            </p>
                            <p className="text-zinc-500 text-xs">{Math.round(ruta.tiempo_minutos)} min</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              )}
            </div>
          )}

          {/* Info inicial */}
          {!resultado && !error && (
            <div className="text-center py-4">
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-white/5 flex items-center justify-center">
                <MapTrifold weight="duotone" className="text-3xl text-zinc-500" />
              </div>
              <p className="text-zinc-500 text-sm">
                Escribe tu calle o haz click en el mapa para encontrar el refugio mas cercano
              </p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-white/10 px-6 py-3 bg-black/30">
          <div className="flex items-center justify-between text-xs text-zinc-500">
            <span>{stats?.total_nodos || 0} puntos</span>
            <span>{stats?.total_escuelas || 0} refugios</span>
            <span>A* Algorithm</span>
          </div>
        </div>
      </div>

      {/* Leyenda */}
      <div className="glass-panel absolute bottom-6 right-6 p-4 z-10" data-testid="legend">
        <p className="data-label mb-3">Leyenda</p>
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-[#00E5FF] border-2 border-white" />
            <span className="text-zinc-300 text-xs">Tu ubicacion</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-[#FF0055] border-2 border-white" />
            <span className="text-zinc-300 text-xs">Refugio/Escuela</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-[#CCFF00] border-2 border-white" />
            <span className="text-zinc-300 text-xs">Refugio mas cercano</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-1 bg-[#CCFF00] rounded" />
            <span className="text-zinc-300 text-xs">Ruta optima</span>
          </div>
          <div className="flex items-center gap-2">
            <Crosshair size={14} className="text-zinc-300" />
            <span className="text-zinc-300 text-xs">Click en mapa = seleccionar</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
