import { useState, useEffect, useCallback, useRef } from "react";
import "@/App.css";
import axios from "axios";
import { MapContainer, TileLayer, Polyline, CircleMarker, Popup, Tooltip, useMap, useMapEvents } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import {
  MapPin, Path, Timer, Ruler, Buildings, NavigationArrow,
  Warning, List, MagnifyingGlass, X, CaretDown, CaretUp,
  Crosshair, FirstAid, Backpack, ArrowBendDownRight, FlagCheckered,
  MapTrifold, CaretLeft, CaretRight, GpsFix
} from "@phosphor-icons/react";
import { ScrollArea } from "@/components/ui/scroll-area";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function MapController({ center, zoom }) {
  const map = useMap();
  useEffect(() => { if (center) map.setView(center, zoom || 15); }, [center, zoom, map]);
  return null;
}

function MapClickHandler({ onMapClick }) {
  useMapEvents({ click(e) { onMapClick(e.latlng.lat, e.latlng.lng); } });
  return null;
}

function SearchInput({ onSelect, selectedNode, onClear }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const debounceRef = useRef(null);
  const wrapperRef = useRef(null);

  useEffect(() => {
    const h = (e) => { if (wrapperRef.current && !wrapperRef.current.contains(e.target)) setIsOpen(false); };
    document.addEventListener("mousedown", h);
    return () => document.removeEventListener("mousedown", h);
  }, []);

  useEffect(() => { if (selectedNode) setQuery(selectedNode.nombre); }, [selectedNode]);

  const buscar = useCallback(async (texto) => {
    if (texto.length < 2) { setResults([]); setIsOpen(false); return; }
    setLoading(true);
    try {
      const res = await axios.get(`${API}/buscar-nodos`, { params: { q: texto } });
      setResults(res.data); setIsOpen(res.data.length > 0);
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  }, []);

  const handleChange = (e) => {
    const val = e.target.value; setQuery(val);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => buscar(val), 300);
  };

  return (
    <div ref={wrapperRef} className="relative" data-testid="search-wrapper">
      <div className="relative">
        <MagnifyingGlass weight="bold" className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
        <input type="text" value={query} onChange={handleChange}
          onFocus={() => { if (results.length > 0) setIsOpen(true); }}
          placeholder="Escribe tu calle (ej: Escudero, Costa Azul...)"
          className="custom-select pl-10 pr-10" data-testid="search-input" />
        {(query || selectedNode) && (
          <button onClick={() => { setQuery(""); setResults([]); setIsOpen(false); onClear(); }}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors" data-testid="search-clear-btn">
            <X size={16} />
          </button>
        )}
      </div>
      {loading && <div className="absolute right-10 top-1/2 -translate-y-1/2"><div className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }} /></div>}
      {isOpen && results.length > 0 && (
        <div className="absolute top-full left-0 right-0 mt-1 max-h-60 overflow-y-auto rounded-xl z-50 bg-white border border-slate-200 shadow-lg" data-testid="search-results">
          {results.map((nodo, idx) => (
            <button key={nodo.id} onClick={() => { setQuery(nodo.nombre); setIsOpen(false); setResults([]); onSelect(nodo); }}
              className="w-full text-left px-4 py-3 hover:bg-blue-50 transition-colors border-b border-slate-100 last:border-0" data-testid={`search-result-${idx}`}>
              <p className="text-slate-800 text-sm font-medium truncate">{nodo.nombre}</p>
              <p className="text-slate-400 text-xs mt-0.5">{nodo.tipo === "escuela" ? "Refugio" : "Interseccion"}</p>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function InstruccionesPanel({ instrucciones }) {
  const [abierto, setAbierto] = useState(false);
  if (!instrucciones || instrucciones.length === 0) return null;
  return (
    <div data-testid="instrucciones-panel">
      <button className="w-full flex items-center justify-center gap-2 py-2 text-slate-500 hover:text-blue-600 transition-colors text-sm font-medium"
        onClick={() => setAbierto(!abierto)} data-testid="toggle-instrucciones-btn">
        <ArrowBendDownRight weight="bold" size={16} />
        {abierto ? "Ocultar" : "Ver"} instrucciones ({instrucciones.length} pasos)
        {abierto ? <CaretUp size={14} /> : <CaretDown size={14} />}
      </button>
      {abierto && (
        <ScrollArea className="h-52" data-testid="instrucciones-list">
          <div className="space-y-0 pr-3">
            {instrucciones.map((paso, idx) => {
              const esUltimo = idx === instrucciones.length - 1;
              return (
                <div key={idx} className="flex gap-3 py-2">
                  <div className="flex flex-col items-center w-6 flex-shrink-0">
                    <div className={`w-5 h-5 rounded-full flex items-center justify-center text-xs font-mono font-bold ${esUltimo ? "bg-green-500 text-white" : "bg-slate-100 text-slate-500"}`}>
                      {esUltimo ? <FlagCheckered size={12} /> : paso.paso}
                    </div>
                    {!esUltimo && <div className="w-px flex-1 bg-slate-200 mt-1" />}
                  </div>
                  <div className="flex-1 min-w-0 pb-1">
                    <p className={`text-sm leading-snug ${esUltimo ? "text-green-600 font-semibold" : "text-slate-700"}`}>{paso.instruccion}</p>
                    {!esUltimo && (
                      <p className="text-xs text-slate-400 font-mono mt-0.5">
                        {paso.distancia_m >= 1000 ? `${(paso.distancia_m/1000).toFixed(1)} km` : `${Math.round(paso.distancia_m)} m`}
                        {" · total: "}{paso.acumulado_m >= 1000 ? `${(paso.acumulado_m/1000).toFixed(1)} km` : `${Math.round(paso.acumulado_m)} m`}
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

function SugerenciasPanel({ sugerencias }) {
  const [abierto, setAbierto] = useState(false);
  if (!sugerencias || sugerencias.length === 0) return null;
  return (
    <div data-testid="sugerencias-panel">
      <button className="w-full flex items-center justify-center gap-2 py-2 text-red-500 hover:text-red-600 transition-colors text-sm font-medium"
        onClick={() => setAbierto(!abierto)} data-testid="toggle-sugerencias-btn">
        <Backpack weight="bold" size={16} />
        {abierto ? "Ocultar kit" : "Que llevar al refugio"}
        {abierto ? <CaretUp size={14} /> : <CaretDown size={14} />}
      </button>
      {abierto && (
        <div className="mt-2 p-4 rounded-xl bg-red-50 border border-red-200" data-testid="sugerencias-list">
          <div className="flex items-center gap-2 mb-3">
            <FirstAid weight="fill" className="text-red-500" size={18} />
            <p className="text-slate-800 text-sm font-semibold">Kit de emergencia</p>
          </div>
          <ScrollArea className="h-36">
            <ul className="space-y-1.5 pr-3">
              {sugerencias.map((item, idx) => (
                <li key={idx} className="flex items-start gap-2 text-sm text-slate-600">
                  <span className="text-red-400 mt-0.5 flex-shrink-0 text-xs">&#9679;</span>{item}
                </li>
              ))}
            </ul>
          </ScrollArea>
        </div>
      )}
    </div>
  );
}

function App() {
  const [escuelas, setEscuelas] = useState([]);
  const [nodoSeleccionado, setNodoSeleccionado] = useState(null);
  const [resultado, setResultado] = useState(null);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState(null);
  const [mapCenter, setMapCenter] = useState([16.8971, -99.8199]);
  const [mostrarTodas, setMostrarTodas] = useState(false);
  const [stats, setStats] = useState(null);
  const [buscandoNodo, setBuscandoNodo] = useState(false);
  const [panelVisible, setPanelVisible] = useState(true);
  const [gpsLoading, setGpsLoading] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const [e, s] = await Promise.all([axios.get(`${API}/escuelas`), axios.get(`${API}/grafo/stats`)]);
        setEscuelas(e.data); setStats(s.data);
      } catch (err) { setError("Error al cargar datos"); }
    })();
  }, []);

  const handleMapClick = useCallback(async (lat, lng) => {
    setBuscandoNodo(true);
    try {
      const res = await axios.post(`${API}/nodo-cercano`, { lat, lon: lng });
      setNodoSeleccionado(res.data); setMapCenter([res.data.lat, res.data.lon]);
      setResultado(null); setError(null); setPanelVisible(true);
    } catch (err) { console.error(err); }
    finally { setBuscandoNodo(false); }
  }, []);

  const usarGPS = useCallback(() => {
    if (!navigator.geolocation) { setError("Tu navegador no soporta GPS"); return; }
    setGpsLoading(true); setError(null);
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        try {
          const res = await axios.post(`${API}/nodo-cercano`, { lat: pos.coords.latitude, lon: pos.coords.longitude });
          setNodoSeleccionado(res.data); setMapCenter([res.data.lat, res.data.lon]);
          setResultado(null); setPanelVisible(true);
        } catch { setError("No se encontro punto cercano a tu GPS"); }
        finally { setGpsLoading(false); }
      },
      (err) => { setGpsLoading(false); setError(err.code === 1 ? "Permiso GPS denegado" : "Error GPS"); },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  }, []);

  const calcularRuta = useCallback(async () => {
    if (!nodoSeleccionado) { setError("Selecciona tu ubicacion primero"); return; }
    setCargando(true); setError(null); setResultado(null);
    try {
      const r = await axios.post(`${API}/calcular-ruta`, { nodo_origen: nodoSeleccionado.id });
      if (r.data.exito) {
        setResultado(r.data);
        const c = r.data.mejor_ruta?.ruta_coordenadas;
        if (c?.length > 0) setMapCenter([c[Math.floor(c.length/2)].lat, c[Math.floor(c.length/2)].lon]);
      } else setError(r.data.mensaje);
    } catch { setError("Error al calcular"); }
    finally { setCargando(false); }
  }, [nodoSeleccionado]);

  const estatusBadge = (est) => {
    const map = { dentro: "badge-dentro", pegado: "badge-pegado", fuera: "badge-fuera", revisar: "badge-revisar" };
    return map[est] || "badge-dentro";
  };

  return (
    <div className="relative w-screen h-screen overflow-hidden bg-slate-100" data-testid="app-container">
      <MapContainer center={mapCenter} zoom={15} className="w-full h-full z-0" zoomControl={true}>
        <MapController center={mapCenter} zoom={15} />
        <MapClickHandler onMapClick={handleMapClick} />
        <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>' />

        {resultado?.mejor_ruta?.ruta_coordenadas && (
          <Polyline positions={resultado.mejor_ruta.ruta_coordenadas.map(c => [c.lat, c.lon])}
            color="#2563EB" weight={5} opacity={0.85} />
        )}

        {escuelas.map(esc => {
          const esMejor = resultado?.mejor_ruta?.escuela?.id === esc.id;
          return (
            <CircleMarker key={esc.id} center={[esc.lat, esc.lon]}
              radius={esMejor ? 10 : 7} fillColor={esMejor ? "#16A34A" : "#DC2626"}
              color="#FFFFFF" weight={esMejor ? 3 : 2} fillOpacity={0.9}>
              <Tooltip permanent direction="top" offset={[0, -10]} className="school-tooltip">
                <span className="school-tooltip-text">
                  {esc.nombre.length > 30 ? esc.nombre.substring(0, 28) + "..." : esc.nombre}
                </span>
              </Tooltip>
              <Popup>
                <div className="text-sm" style={{ maxWidth: 220 }}>
                  <strong className="text-blue-700">{esc.nombre}</strong>
                  {esc.alias && <p className="text-slate-500 text-xs mt-1">{esc.alias}</p>}
                  {esc.direccion && <p className="text-slate-400 text-xs mt-1">{esc.direccion}</p>}
                  <div className="flex gap-2 mt-2">
                    <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 uppercase">{esc.tipo}</span>
                    {esc.estatus && <span className={`text-xs px-2 py-0.5 rounded-full ${estatusBadge(esc.estatus)}`}>{esc.estatus}</span>}
                  </div>
                </div>
              </Popup>
            </CircleMarker>
          );
        })}

        {nodoSeleccionado && (
          <CircleMarker center={[nodoSeleccionado.lat, nodoSeleccionado.lon]}
            radius={10} fillColor="#0EA5E9" color="#FFFFFF" weight={3} fillOpacity={1}>
            <Tooltip permanent direction="bottom" offset={[0, 10]} className="user-tooltip">
              <span className="user-tooltip-text">Tu ubicacion</span>
            </Tooltip>
          </CircleMarker>
        )}
      </MapContainer>

      {buscandoNodo && (
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-20 glass-panel px-5 py-3 flex items-center gap-3">
          <div className="spinner" /><span className="text-slate-600 text-sm">Buscando punto...</span>
        </div>
      )}

      <button className="absolute z-20 glass-panel p-2 hover:bg-slate-100 transition-colors"
        style={{ top: 24, left: panelVisible ? 392 : 24 }}
        onClick={() => setPanelVisible(!panelVisible)} data-testid="toggle-panel-btn">
        {panelVisible ? <CaretLeft size={18} className="text-slate-500" /> : <CaretRight size={18} className="text-slate-500" />}
      </button>

      {panelVisible && (
        <div className="glass-panel absolute top-6 left-6 w-[370px] max-h-[calc(100vh-48px)] overflow-hidden animate-slide-in z-10 flex flex-col" data-testid="control-panel">
          <div className="p-5 space-y-4 overflow-y-auto flex-1">
            <div>
              <h1 className="font-heading text-xl font-bold text-slate-800 flex items-center gap-2">
                <NavigationArrow weight="bold" className="text-blue-600" />
                Refugios A*
              </h1>
              <p className="text-slate-400 text-xs mt-1">Ciudad Renacimiento, Acapulco</p>
            </div>

            <div className="space-y-2">
              <label className="data-label flex items-center gap-2">
                <MapPin weight="bold" className="text-sky-500" /> Tu ubicacion
              </label>
              <SearchInput onSelect={(n) => { setNodoSeleccionado(n); setMapCenter([n.lat, n.lon]); setResultado(null); setError(null); }}
                selectedNode={nodoSeleccionado}
                onClear={() => { setNodoSeleccionado(null); setResultado(null); setError(null); }} />
              <div className="flex items-center gap-2">
                <button onClick={usarGPS} disabled={gpsLoading}
                  className="flex-1 flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-xs font-medium transition-all bg-sky-50 border border-sky-200 text-sky-600 hover:bg-sky-100 disabled:opacity-50"
                  data-testid="gps-btn">
                  {gpsLoading ? <div className="spinner" style={{ width: 12, height: 12, borderWidth: 2 }} /> : <GpsFix weight="bold" size={14} />}
                  {gpsLoading ? "Obteniendo..." : "Usar mi GPS"}
                </button>
                <span className="text-slate-400 text-xs">o click en mapa</span>
              </div>
              {nodoSeleccionado && (
                <p className="text-xs text-sky-600 flex items-center gap-1">
                  <MapPin weight="fill" size={12} />{nodoSeleccionado.nombre}
                </p>
              )}
            </div>

            <button className="btn-primary w-full flex items-center justify-center gap-2"
              onClick={calcularRuta} disabled={cargando || !nodoSeleccionado} data-testid="calculate-route-btn">
              {cargando ? (<><div className="spinner" />Calculando...</>) : (<><Path weight="bold" />Encontrar refugio mas cercano</>)}
            </button>

            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-3 flex items-start gap-2" data-testid="error-message">
                <Warning weight="fill" className="text-red-500 flex-shrink-0 mt-0.5" size={16} />
                <p className="text-red-600 text-sm">{error}</p>
              </div>
            )}

            {resultado?.mejor_ruta && (
              <div className="space-y-3 animate-slide-in" data-testid="route-result">
                <div className="route-card">
                  <div className="flex items-start gap-3">
                    <Buildings weight="fill" className="text-green-600 text-lg flex-shrink-0 mt-1" />
                    <div className="flex-1 min-w-0">
                      <p className="data-label mb-1">Refugio mas cercano</p>
                      <h3 className="text-slate-800 font-semibold text-sm leading-tight" data-testid="nearest-school-name">
                        {resultado.mejor_ruta.escuela.nombre}
                      </h3>
                      {resultado.mejor_ruta.escuela.direccion && (
                        <p className="text-slate-400 text-xs mt-1">{resultado.mejor_ruta.escuela.direccion}</p>
                      )}
                      <div className="flex gap-2 mt-2">
                        <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 uppercase">{resultado.mejor_ruta.escuela.tipo}</span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div className="metric-card" data-testid="distance-metric">
                    <div className="flex items-center gap-1.5 mb-1">
                      <Ruler weight="bold" className="text-blue-600" size={14} /><span className="data-label">Distancia</span>
                    </div>
                    <p className="font-mono text-xl font-semibold text-slate-800">
                      {resultado.mejor_ruta.distancia_total >= 1000 ? `${(resultado.mejor_ruta.distancia_total / 1000).toFixed(1)} km` : `${Math.round(resultado.mejor_ruta.distancia_total)} m`}
                    </p>
                  </div>
                  <div className="metric-card" data-testid="time-metric">
                    <div className="flex items-center gap-1.5 mb-1">
                      <Timer weight="bold" className="text-sky-500" size={14} /><span className="data-label">Caminando</span>
                    </div>
                    <p className="font-mono text-xl font-semibold text-slate-800">
                      {resultado.mejor_ruta.tiempo_minutos >= 60 ? `${Math.floor(resultado.mejor_ruta.tiempo_minutos / 60)}h ${Math.round(resultado.mejor_ruta.tiempo_minutos % 60)}m` : `${Math.round(resultado.mejor_ruta.tiempo_minutos)} min`}
                    </p>
                  </div>
                </div>

                <InstruccionesPanel instrucciones={resultado.mejor_ruta.instrucciones} />
                <SugerenciasPanel sugerencias={resultado.sugerencias_emergencia} />

                <button className="w-full flex items-center justify-center gap-2 py-2 text-slate-400 hover:text-slate-600 transition-colors text-sm"
                  onClick={() => setMostrarTodas(!mostrarTodas)} data-testid="toggle-all-routes-btn">
                  <List weight="bold" />
                  {mostrarTodas ? "Ocultar" : "Ver"} todos los refugios ({resultado.todas_rutas.length})
                </button>

                {mostrarTodas && (
                  <ScrollArea className="h-44" data-testid="all-schools-list">
                    <div className="space-y-1.5 pr-3">
                      {resultado.todas_rutas.map((ruta, idx) => (
                        <div key={ruta.escuela.id} className="school-item">
                          <div className="flex items-start justify-between">
                            <div className="flex-1 min-w-0">
                              <p className="text-slate-700 text-xs font-medium truncate">{idx + 1}. {ruta.escuela.nombre}</p>
                              <p className="text-slate-400 text-xs">{ruta.escuela.tipo}</p>
                            </div>
                            <div className="text-right flex-shrink-0 ml-2">
                              <p className="text-blue-600 font-mono text-xs font-semibold">
                                {ruta.distancia_total >= 1000 ? `${(ruta.distancia_total / 1000).toFixed(1)}km` : `${Math.round(ruta.distancia_total)}m`}
                              </p>
                              <p className="text-slate-400 text-xs">{Math.round(ruta.tiempo_minutos)} min</p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                )}
              </div>
            )}

            {!resultado && !error && (
              <div className="text-center py-4">
                <div className="w-14 h-14 mx-auto mb-3 rounded-full bg-blue-50 flex items-center justify-center">
                  <MapTrifold weight="duotone" className="text-2xl text-blue-400" />
                </div>
                <p className="text-slate-400 text-sm">Escribe tu calle, usa GPS o haz click en el mapa</p>
              </div>
            )}
          </div>

          <div className="border-t border-slate-200 px-5 py-2.5 bg-slate-50/50">
            <div className="flex items-center justify-between text-xs text-slate-400">
              <span>{stats?.total_nodos || 0} puntos</span>
              <span>{stats?.total_escuelas || 0} refugios</span>
              <span>A* Algorithm</span>
            </div>
          </div>
        </div>
      )}

      <div className="glass-panel absolute bottom-6 right-6 p-3 z-10" data-testid="legend">
        <p className="data-label mb-2">Leyenda</p>
        <div className="space-y-1.5">
          <div className="flex items-center gap-2"><div className="w-2.5 h-2.5 rounded-full bg-sky-500 border border-white shadow-sm" /><span className="text-slate-500 text-xs">Tu ubicacion</span></div>
          <div className="flex items-center gap-2"><div className="w-2.5 h-2.5 rounded-full bg-red-600 border border-white shadow-sm" /><span className="text-slate-500 text-xs">Refugio</span></div>
          <div className="flex items-center gap-2"><div className="w-2.5 h-2.5 rounded-full bg-green-600 border border-white shadow-sm" /><span className="text-slate-500 text-xs">Mas cercano</span></div>
          <div className="flex items-center gap-2"><div className="w-6 h-0.5 bg-blue-600 rounded" /><span className="text-slate-500 text-xs">Ruta</span></div>
          <div className="flex items-center gap-2"><Crosshair size={12} className="text-slate-400" /><span className="text-slate-500 text-xs">Click = seleccionar</span></div>
        </div>
      </div>
    </div>
  );
}

export default App;
