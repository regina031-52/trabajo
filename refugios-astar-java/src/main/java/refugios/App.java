package refugios;

import com.google.gson.*;
import com.sun.net.httpserver.*;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.util.*;

/**
 * ============================================================
 *  VERSIÓN WEB - Servidor con mapa interactivo
 * ============================================================
 * 
 * Usa el HttpServer integrado de Java (no necesita frameworks externos).
 * Sirve la API REST y la página HTML con el mapa de Leaflet.
 * 
 * Ejecutar:
 *   mvn compile exec:java -Dexec.mainClass="refugios.App"
 *   Abrir: http://localhost:5000
 */
public class App {

    static Datos datos;
    static Grafo grafo;
    static Gson gson = new GsonBuilder().create();

    static final String[] SUGERENCIAS = {
        "Agua embotellada (al menos 3 litros por persona)",
        "Documentos importantes en bolsa impermeable (INE, CURP, actas)",
        "Botiquín de primeros auxilios", "Linterna con pilas extra",
        "Radio portátil de pilas", "Alimentos no perecederos (enlatados, barras, galletas)",
        "Medicamentos personales (si aplica)", "Ropa extra y cobija ligera",
        "Cargador portátil para celular", "Silbato de emergencia",
        "Dinero en efectivo (billetes y monedas)", "Copia de llaves de casa",
        "Artículos de higiene (papel, jabón, gel antibacterial)",
        "Mascarilla o cubrebocas", "Bolsas de plástico (proteger documentos)"
    };

    public static void main(String[] args) throws Exception {
        System.out.println("=".repeat(60));
        System.out.println("  REFUGIOS A* - Ciudad Renacimiento, Acapulco");
        System.out.println("  Cargando datos...");
        System.out.println("=".repeat(60));

        // Cargar datos y construir grafo
        datos = new Datos("data");
        grafo = new Grafo(datos);

        // Crear servidor HTTP en puerto 5000
        HttpServer server = HttpServer.create(new InetSocketAddress(5000), 0);

        // Registrar endpoints (rutas de la API)
        server.createContext("/", App::paginaPrincipal);
        server.createContext("/api/escuelas", App::apiEscuelas);
        server.createContext("/api/grafo/stats", App::apiStats);
        server.createContext("/api/buscar-nodos", App::apiBuscar);
        server.createContext("/api/nodo-cercano", App::apiNodoCercano);
        server.createContext("/api/calcular-ruta", App::apiCalcularRuta);

        server.setExecutor(null);
        server.start();

        System.out.println();
        System.out.println("  ✓ Servidor listo");
        System.out.println("  ✓ Abre tu navegador en: http://localhost:5000");
        System.out.println("=".repeat(60));
    }

    // ===== HELPERS =====
    static void responderJson(HttpExchange ex, String json) throws IOException {
        byte[] bytes = json.getBytes(StandardCharsets.UTF_8);
        ex.getResponseHeaders().set("Content-Type", "application/json; charset=UTF-8");
        ex.getResponseHeaders().set("Access-Control-Allow-Origin", "*");
        ex.sendResponseHeaders(200, bytes.length);
        ex.getResponseBody().write(bytes);
        ex.getResponseBody().close();
    }

    static String leerBody(HttpExchange ex) throws IOException {
        return new String(ex.getRequestBody().readAllBytes(), StandardCharsets.UTF_8);
    }

    // ===== ENDPOINTS =====
    static void apiEscuelas(HttpExchange ex) throws IOException {
        responderJson(ex, gson.toJson(datos.escuelas));
    }

    static void apiStats(HttpExchange ex) throws IOException {
        Map<String, Object> stats = Map.of(
            "total_nodos", datos.nodos.size(),
            "total_aristas", datos.aristas.size(),
            "total_escuelas", datos.escuelas.size()
        );
        responderJson(ex, gson.toJson(stats));
    }

    static void apiBuscar(HttpExchange ex) throws IOException {
        String query = "";
        String rawQuery = ex.getRequestURI().getQuery();
        if (rawQuery != null) {
            for (String param : rawQuery.split("&")) {
                String[] kv = param.split("=", 2);
                if (kv[0].equals("q") && kv.length > 1)
                    query = URLDecoder.decode(kv[1], StandardCharsets.UTF_8);
            }
        }
        List<Datos.Nodo> res = datos.buscarPorNombre(query);
        List<Map<String, Object>> out = new ArrayList<>();
        for (Datos.Nodo n : res) {
            out.add(Map.of("id", n.id, "nombre", n.nombre, "lat", n.lat, "lon", n.lon, "tipo", n.tipo));
        }
        responderJson(ex, gson.toJson(out));
    }

    static void apiNodoCercano(HttpExchange ex) throws IOException {
        if ("OPTIONS".equals(ex.getRequestMethod())) { ex.sendResponseHeaders(200, -1); return; }
        JsonObject body = JsonParser.parseString(leerBody(ex)).getAsJsonObject();
        Datos.Nodo n = datos.nodoCercano(body.get("lat").getAsDouble(), body.get("lon").getAsDouble());
        responderJson(ex, gson.toJson(Map.of("id", n.id, "nombre", n.nombre, "lat", n.lat, "lon", n.lon, "tipo", n.tipo)));
    }

    static void apiCalcularRuta(HttpExchange ex) throws IOException {
        if ("OPTIONS".equals(ex.getRequestMethod())) { ex.sendResponseHeaders(200, -1); return; }
        JsonObject body = JsonParser.parseString(leerBody(ex)).getAsJsonObject();
        String nodoOrigen = body.get("nodo_origen").getAsString();

        List<Grafo.ResultadoRuta> rutas = grafo.calcularRutasATodas(nodoOrigen);

        if (rutas.isEmpty()) {
            responderJson(ex, gson.toJson(Map.of("exito", false, "mensaje", "No se encontró ruta")));
            return;
        }

        // Construir respuesta JSON
        Grafo.ResultadoRuta mejor = rutas.get(0);
        List<Map<String, Object>> todasRutas = new ArrayList<>();
        for (Grafo.ResultadoRuta r : rutas) {
            List<Map<String, Object>> instrList = new ArrayList<>();
            for (Grafo.Instruccion ins : r.instrucciones()) {
                instrList.add(Map.of("paso", ins.paso(), "instruccion", ins.texto(),
                    "calle", ins.calle(), "distancia_m", ins.distanciaM(), "acumulado_m", ins.acumuladoM()));
            }
            List<Map<String, Double>> coords = new ArrayList<>();
            for (double[] c : r.rutaCoordenadas()) coords.add(Map.of("lat", c[0], "lon", c[1]));

            Map<String, Object> rutaMap = new HashMap<>();
            rutaMap.put("escuela", r.escuela());
            rutaMap.put("distancia_total", r.distanciaTotal());
            rutaMap.put("tiempo_minutos", r.tiempoMinutos());
            rutaMap.put("ruta_coordenadas", coords);
            rutaMap.put("instrucciones", instrList);
            todasRutas.add(rutaMap);
        }

        Map<String, Object> resp = new HashMap<>();
        resp.put("exito", true);
        resp.put("mensaje", "Refugio más cercano: " + mejor.escuela().nombre);
        resp.put("mejor_ruta", todasRutas.get(0));
        resp.put("todas_rutas", todasRutas);
        resp.put("sugerencias_emergencia", Arrays.asList(SUGERENCIAS));

        responderJson(ex, gson.toJson(resp));
    }

    // ===== PÁGINA HTML (mismo diseño que la versión Python/Flask) =====
    static void paginaPrincipal(HttpExchange ex) throws IOException {
        // Servir el HTML con el mapa interactivo
        // Es el mismo HTML que la versión Flask
        byte[] bytes = PAGINA_HTML.getBytes(StandardCharsets.UTF_8);
        ex.getResponseHeaders().set("Content-Type", "text/html; charset=UTF-8");
        ex.sendResponseHeaders(200, bytes.length);
        ex.getResponseBody().write(bytes);
        ex.getResponseBody().close();
    }

    static final String PAGINA_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Refugios A* - Ciudad Renacimiento (Java)</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box;margin:0;padding:0}body{font-family:'DM Sans',sans-serif;background:#F4F5F7;overflow:hidden}
#mapa{width:100vw;height:100vh;z-index:0}
.panel{position:absolute;top:20px;left:20px;width:370px;max-height:calc(100vh - 40px);background:rgba(255,255,255,.92);backdrop-filter:blur(20px);border:1px solid rgba(0,0,0,.1);border-radius:16px;box-shadow:0 4px 24px rgba(0,0,0,.08);z-index:1000;display:flex;flex-direction:column;overflow:hidden;transition:transform .3s ease}
.panel.oculto{transform:translateX(-400px)}.panel-body{padding:20px;overflow-y:auto;flex:1}
.panel-footer{border-top:1px solid #E2E8F0;padding:10px 20px;background:rgba(248,250,252,.5);display:flex;justify-content:space-between;font-size:11px;color:#94A3B8}
.btn-toggle{position:absolute;top:20px;z-index:1001;background:rgba(255,255,255,.92);border:1px solid rgba(0,0,0,.1);border-radius:12px;padding:8px 10px;cursor:pointer;box-shadow:0 2px 8px rgba(0,0,0,.08);font-size:18px;color:#64748B;transition:left .3s ease}
.btn-toggle:hover{background:#F1F5F9}
h1{font-size:20px;font-weight:700;color:#1E293B;display:flex;align-items:center;gap:8px}h1 span{color:#2563EB}
.subtitulo{font-size:12px;color:#94A3B8;margin-top:4px}
.search-box{position:relative;margin-top:12px}.search-box input{width:100%;padding:11px 14px 11px 38px;border:1px solid #CBD5E1;border-radius:10px;font-family:'DM Sans',sans-serif;font-size:14px;outline:none;transition:border-color .2s}
.search-box input:focus{border-color:#2563EB;box-shadow:0 0 0 3px rgba(37,99,235,.1)}.search-icon{position:absolute;left:12px;top:50%;transform:translateY(-50%);color:#94A3B8}
.dropdown{position:absolute;top:100%;left:0;right:0;background:#fff;border:1px solid #E2E8F0;border-radius:10px;margin-top:4px;max-height:240px;overflow-y:auto;box-shadow:0 8px 24px rgba(0,0,0,.1);z-index:100;display:none}
.dropdown.visible{display:block}.dropdown-item{padding:10px 14px;cursor:pointer;border-bottom:1px solid #F1F5F9;font-size:13px;color:#334155}.dropdown-item:hover{background:#EFF6FF}.dropdown-item small{color:#94A3B8;display:block;margin-top:2px;font-size:11px}
.btn-gps{flex:1;padding:8px;border-radius:8px;border:1px solid #BAE6FD;background:#F0F9FF;color:#0284C7;font-size:12px;font-weight:600;cursor:pointer}.btn-gps:hover{background:#E0F2FE}
.btn-primary{width:100%;padding:12px;border:none;border-radius:10px;background:#2563EB;color:#fff;font-size:14px;font-weight:600;cursor:pointer;font-family:'DM Sans',sans-serif;transition:all .2s}.btn-primary:hover{background:#1D4ED8;box-shadow:0 4px 12px rgba(37,99,235,.3)}.btn-primary:disabled{opacity:.5;cursor:not-allowed}
.route-card{background:linear-gradient(135deg,rgba(37,99,235,.06),rgba(14,165,233,.04));border:1px solid rgba(37,99,235,.2);border-radius:12px;padding:14px;margin-top:12px}
.route-card h3{font-size:14px;color:#1E293B;font-weight:600;margin-top:4px}.route-card .tipo{font-size:11px;color:#64748B;text-transform:uppercase;margin-top:6px;display:inline-block;background:#F1F5F9;padding:2px 8px;border-radius:4px}.route-card .dir{font-size:11px;color:#94A3B8;margin-top:6px}
.metricas{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:12px}.metrica{background:#F8FAFC;border:1px solid #E2E8F0;border-radius:10px;padding:12px}
.metrica-label{font-family:'JetBrains Mono',monospace;font-size:9px;text-transform:uppercase;letter-spacing:.15em;color:#94A3B8}.metrica-valor{font-family:'JetBrains Mono',monospace;font-size:20px;font-weight:600;color:#1E293B;margin-top:4px}
.toggle-btn{width:100%;padding:8px;background:none;border:none;color:#64748B;font-size:13px;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:6px}.toggle-btn:hover{color:#2563EB}.toggle-btn.emergencia{color:#DC2626}.toggle-btn.emergencia:hover{color:#B91C1C}
.seccion{display:none;margin-top:8px}.seccion.visible{display:block}
.paso{display:flex;gap:10px;padding:8px 0}.paso-num{width:22px;height:22px;border-radius:50%;flex-shrink:0;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;font-family:'JetBrains Mono',monospace;background:#F1F5F9;color:#64748B}.paso-num.final{background:#16A34A;color:#fff}.paso-texto{font-size:13px;color:#475569;line-height:1.4}.paso-dist{font-size:11px;color:#94A3B8;font-family:'JetBrains Mono',monospace}
.kit-box{background:#FEF2F2;border:1px solid #FECACA;border-radius:10px;padding:14px;max-height:200px;overflow-y:auto}.kit-item{font-size:13px;color:#64748B;padding:3px 0;display:flex;gap:6px}.kit-dot{color:#EF4444;flex-shrink:0}
.ref-item{display:flex;justify-content:space-between;align-items:center;padding:8px 10px;background:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px;margin-top:6px;font-size:12px}.ref-item .nombre{color:#334155;font-weight:500;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.ref-item .dist{color:#2563EB;font-family:'JetBrains Mono',monospace;font-weight:600;margin-left:8px}
.leyenda{position:absolute;bottom:20px;right:20px;z-index:1000;background:rgba(255,255,255,.92);backdrop-filter:blur(20px);border:1px solid rgba(0,0,0,.1);border-radius:12px;padding:12px;box-shadow:0 2px 8px rgba(0,0,0,.08)}
.leyenda-titulo{font-size:9px;text-transform:uppercase;letter-spacing:.15em;color:#94A3B8;margin-bottom:8px;font-family:'JetBrains Mono',monospace}.leyenda-item{display:flex;align-items:center;gap:8px;margin-top:4px;font-size:12px;color:#64748B}.leyenda-dot{width:10px;height:10px;border-radius:50%;border:1.5px solid #fff;box-shadow:0 1px 3px rgba(0,0,0,.2)}.leyenda-line{width:24px;height:3px;border-radius:2px}
.school-tooltip{background:#fff!important;border:1px solid rgba(220,38,38,.3)!important;border-radius:6px!important;padding:3px 8px!important;box-shadow:0 2px 8px rgba(0,0,0,.1)!important}.school-tooltip-text{color:#DC2626;font-size:10px;font-weight:600;font-family:'DM Sans',sans-serif}
.info-vacia{text-align:center;padding:20px 0;color:#94A3B8;font-size:13px}.nodo-sel{font-size:12px;color:#0284C7;margin-top:6px}.error-msg{background:#FEF2F2;border:1px solid #FECACA;border-radius:8px;padding:10px;color:#DC2626;font-size:13px;margin-top:12px;display:none}
</style>
</head>
<body>
<div id="mapa"></div>
<button class="btn-toggle" id="btnToggle" onclick="togglePanel()">&#9664;</button>
<div class="panel" id="panel">
<div class="panel-body">
<h1><span>&#9654;</span> Refugios A*</h1>
<p class="subtitulo">Ciudad Renacimiento, Acapulco &mdash; Java Edition</p>
<div class="search-box"><span class="search-icon">&#128269;</span><input type="text" id="inputBuscar" placeholder="Escribe tu calle (ej: Escudero, Costa Azul...)" oninput="buscar(this.value)" onfocus="mostrarDD()"><div class="dropdown" id="dd"></div></div>
<div style="display:flex;gap:8px;align-items:center;margin-top:8px"><button class="btn-gps" onclick="usarGPS()">&#128205; Usar mi GPS</button><span style="font-size:11px;color:#94A3B8">o click en mapa</span></div>
<div class="nodo-sel" id="nodoInfo" style="display:none"></div>
<button class="btn-primary" id="btnCalc" onclick="calcular()" disabled style="margin-top:12px">Encontrar refugio m&aacute;s cercano</button>
<div class="error-msg" id="error"></div>
<div id="resultado"></div>
<div class="info-vacia" id="infoVacia">Escribe tu calle, usa GPS o haz click en el mapa</div>
</div>
<div class="panel-footer"><span id="sN">0 puntos</span><span id="sE">0 refugios</span><span>A* Algorithm</span></div>
</div>
<div class="leyenda"><div class="leyenda-titulo">Leyenda</div><div class="leyenda-item"><div class="leyenda-dot" style="background:#0EA5E9"></div> Tu ubicaci&oacute;n</div><div class="leyenda-item"><div class="leyenda-dot" style="background:#DC2626"></div> Refugio</div><div class="leyenda-item"><div class="leyenda-dot" style="background:#16A34A"></div> M&aacute;s cercano</div><div class="leyenda-item"><div class="leyenda-line" style="background:#2563EB"></div> Ruta</div></div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
let mapa,nodoSel=null,mkUser=null,lineaRuta=null,mkEsc=[];
mapa=L.map('mapa').setView([16.8971,-99.8199],15);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{attribution:'&copy; OSM'}).addTo(mapa);
mapa.on('click',e=>{fetch('/api/nodo-cercano',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({lat:e.latlng.lat,lon:e.latlng.lng})}).then(r=>r.json()).then(n=>selNodo(n))});
fetch('/api/escuelas').then(r=>r.json()).then(es=>{es.forEach(e=>{let m=L.circleMarker([e.lat,e.lon],{radius:7,fillColor:'#DC2626',color:'#FFF',weight:2,fillOpacity:.9}).addTo(mapa);m.bindTooltip(e.nombre.length>30?e.nombre.slice(0,28)+'...':e.nombre,{permanent:true,direction:'top',offset:[0,-10],className:'school-tooltip'});m.bindPopup('<b style="color:#2563EB">'+e.nombre+'</b>'+(e.direccion?'<br><small style="color:#94A3B8">'+e.direccion+'</small>':'')+'<br><span style="font-size:11px;color:#DC2626;text-transform:uppercase">'+e.tipo+'</span>');m.eid=e.id;mkEsc.push(m)})});
fetch('/api/grafo/stats').then(r=>r.json()).then(s=>{document.getElementById('sN').textContent=s.total_nodos+' puntos';document.getElementById('sE').textContent=s.total_escuelas+' refugios'});
let timer;function buscar(t){clearTimeout(timer);if(t.length<2){document.getElementById('dd').className='dropdown';return}timer=setTimeout(()=>{fetch('/api/buscar-nodos?q='+encodeURIComponent(t)).then(r=>r.json()).then(r=>{let d=document.getElementById('dd');if(!r.length){d.className='dropdown';return}d.innerHTML=r.map((n,i)=>'<div class="dropdown-item" onclick="selDD('+i+')">'+n.nombre+'<small>'+(n.tipo==='escuela'?'Refugio':'Intersección')+'</small></div>').join('');d.className='dropdown visible';window._res=r})},300)}
function mostrarDD(){let d=document.getElementById('dd');if(d.innerHTML)d.className='dropdown visible'}
function selDD(i){let n=window._res[i];document.getElementById('inputBuscar').value=n.nombre;document.getElementById('dd').className='dropdown';selNodo(n)}
function selNodo(n){nodoSel=n;if(mkUser)mapa.removeLayer(mkUser);mkUser=L.circleMarker([n.lat,n.lon],{radius:10,fillColor:'#0EA5E9',color:'#FFF',weight:3,fillOpacity:1}).addTo(mapa).bindTooltip('Tu ubicación',{permanent:true,direction:'bottom',offset:[0,10]});mapa.setView([n.lat,n.lon],15);document.getElementById('nodoInfo').style.display='block';document.getElementById('nodoInfo').textContent='📍 '+n.nombre;document.getElementById('inputBuscar').value=n.nombre;document.getElementById('btnCalc').disabled=false;document.getElementById('error').style.display='none';document.getElementById('resultado').innerHTML='';document.getElementById('infoVacia').style.display='block'}
function usarGPS(){if(!navigator.geolocation){showErr('GPS no soportado');return}navigator.geolocation.getCurrentPosition(p=>{fetch('/api/nodo-cercano',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({lat:p.coords.latitude,lon:p.coords.longitude})}).then(r=>r.json()).then(n=>selNodo(n))},e=>{showErr(e.code===1?'Permiso GPS denegado':'Error GPS')},{enableHighAccuracy:true,timeout:10000})}
function showErr(m){document.getElementById('error').textContent=m;document.getElementById('error').style.display='block'}
function calcular(){if(!nodoSel)return;document.getElementById('btnCalc').disabled=true;document.getElementById('btnCalc').textContent='Calculando...';document.getElementById('error').style.display='none';
fetch('/api/calcular-ruta',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({nodo_origen:nodoSel.id})}).then(r=>r.json()).then(data=>{document.getElementById('btnCalc').disabled=false;document.getElementById('btnCalc').textContent='Encontrar refugio más cercano';if(!data.exito){showErr(data.mensaje);return}
let m=data.mejor_ruta;if(lineaRuta)mapa.removeLayer(lineaRuta);lineaRuta=L.polyline(m.ruta_coordenadas.map(c=>[c.lat,c.lon]),{color:'#2563EB',weight:5,opacity:.85}).addTo(mapa);mkEsc.forEach(mk=>{mk.setStyle(mk.eid===m.escuela.id?{fillColor:'#16A34A',radius:10}:{fillColor:'#DC2626',radius:7})});
let coords=m.ruta_coordenadas,mid=coords[Math.floor(coords.length/2)];mapa.setView([mid.lat,mid.lon],15);
let ds=m.distancia_total>=1000?(m.distancia_total/1000).toFixed(1)+' km':Math.round(m.distancia_total)+' m';
let ts=m.tiempo_minutos>=60?Math.floor(m.tiempo_minutos/60)+'h '+Math.round(m.tiempo_minutos%60)+'m':Math.round(m.tiempo_minutos)+' min';
let h='<div class="route-card"><div style="font-size:9px;color:#94A3B8;text-transform:uppercase;letter-spacing:.1em">Refugio más cercano</div><h3>'+m.escuela.nombre+'</h3>';
if(m.escuela.direccion)h+='<div class="dir">'+m.escuela.direccion+'</div>';h+='<span class="tipo">'+m.escuela.tipo+'</span></div>';
h+='<div class="metricas"><div class="metrica"><div class="metrica-label">Distancia</div><div class="metrica-valor">'+ds+'</div></div><div class="metrica"><div class="metrica-label">Caminando</div><div class="metrica-valor">'+ts+'</div></div></div>';
h+='<button class="toggle-btn" onclick="tog(\'inst\')">📋 Ver instrucciones ('+m.instrucciones.length+' pasos) ▼</button><div class="seccion" id="inst">';
m.instrucciones.forEach(p=>{let f=p.distancia_m===0;h+='<div class="paso"><div class="paso-num '+(f?'final':'')+'">'+(f?'✓':p.paso)+'</div><div><div class="paso-texto">'+p.instruccion+'</div>';if(!f)h+='<div class="paso-dist">'+Math.round(p.distancia_m)+'m · total: '+Math.round(p.acumulado_m)+'m</div>';h+='</div></div>'});h+='</div>';
h+='<button class="toggle-btn emergencia" onclick="tog(\'kit\')">🎒 Qué llevar al refugio ▼</button><div class="seccion" id="kit"><div class="kit-box">';data.sugerencias_emergencia.forEach(s=>{h+='<div class="kit-item"><span class="kit-dot">●</span>'+s+'</div>'});h+='</div></div>';
h+='<button class="toggle-btn" onclick="tog(\'todos\')">📋 Ver todos ('+data.todas_rutas.length+' refugios) ▼</button><div class="seccion" id="todos" style="max-height:200px;overflow-y:auto">';
data.todas_rutas.forEach((r,i)=>{let d=r.distancia_total>=1000?(r.distancia_total/1000).toFixed(1)+'km':Math.round(r.distancia_total)+'m';h+='<div class="ref-item"><span class="nombre">'+(i+1)+'. '+r.escuela.nombre+'</span><span class="dist">'+d+'</span></div>'});h+='</div>';
document.getElementById('resultado').innerHTML=h;document.getElementById('infoVacia').style.display='none'}).catch(()=>{document.getElementById('btnCalc').disabled=false;document.getElementById('btnCalc').textContent='Encontrar refugio más cercano';showErr('Error al calcular')})}
function tog(id){let e=document.getElementById(id);e.className=e.className.includes('visible')?'seccion':'seccion visible'}
function togglePanel(){let p=document.getElementById('panel'),b=document.getElementById('btnToggle');if(p.className.includes('oculto')){p.className='panel';b.innerHTML='&#9664;';b.style.left='400px'}else{p.className='panel oculto';b.innerHTML='&#9654;';b.style.left='20px'}}
document.getElementById('btnToggle').style.left='400px';
document.addEventListener('click',e=>{if(!e.target.closest('.search-box'))document.getElementById('dd').className='dropdown'});
</script>
</body>
</html>
""";
}
