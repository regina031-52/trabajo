package refugios;

import com.google.gson.*;
import com.google.gson.reflect.TypeToken;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;

/**
 * ============================================================
 *  CLASE DATOS: Carga los archivos JSON y almacena la información
 * ============================================================
 * 
 * Esta clase lee los 3 archivos JSON:
 *   - escuelas.json: los 19 refugios con coordenadas verificadas
 *   - nodos_calles.json: 8,558 intersecciones de calles (de OpenStreetMap)
 *   - aristas_calles.json: 23,332 conexiones entre calles con distancias
 */
public class Datos {

    // ===== CLASES INTERNAS (modelos de datos) =====

    /** Representa un nodo (intersección de calles) */
    public static class Nodo {
        public String id;
        public double lat;      // Latitud (coordenada Y)
        public double lon;      // Longitud (coordenada X)
        public String tipo;     // "interseccion" o "escuela"
        public String nombre;   // Nombre de la calle/intersección
    }

    /** Representa una arista (calle que conecta dos nodos) */
    public static class Arista {
        public String origen;       // ID del nodo de inicio
        public String destino;      // ID del nodo de fin
        public double distancia_m;  // Distancia en metros
        public String nombre_calle; // Nombre de la calle
    }

    /** Representa un refugio (escuela) */
    public static class Escuela {
        public String id;
        public String nombre;
        public String alias;
        public String tipo;
        public boolean unificada;
        public String nodo_id;      // ID del nodo más cercano en la red
        public double lat;
        public double lon;
        public String direccion;
        public String estatus;
    }

    // ===== DATOS CARGADOS =====
    public List<Nodo> nodos;
    public List<Arista> aristas;
    public List<Escuela> escuelas;
    public Map<String, Nodo> nodosPorId;  // Diccionario para acceso rápido

    /**
     * Constructor: carga los datos desde la carpeta especificada.
     */
    public Datos(String carpetaData) throws IOException {
        Gson gson = new Gson();

        // Leer nodos
        String jsonNodos = Files.readString(Path.of(carpetaData, "nodos_calles.json"), StandardCharsets.UTF_8);
        nodos = gson.fromJson(jsonNodos, new TypeToken<List<Nodo>>(){}.getType());

        // Leer aristas
        String jsonAristas = Files.readString(Path.of(carpetaData, "aristas_calles.json"), StandardCharsets.UTF_8);
        aristas = gson.fromJson(jsonAristas, new TypeToken<List<Arista>>(){}.getType());

        // Leer escuelas
        String jsonEscuelas = Files.readString(Path.of(carpetaData, "escuelas.json"), StandardCharsets.UTF_8);
        escuelas = gson.fromJson(jsonEscuelas, new TypeToken<List<Escuela>>(){}.getType());

        // Crear diccionario de nodos para acceso rápido por ID
        nodosPorId = new HashMap<>();
        for (Nodo n : nodos) {
            nodosPorId.put(n.id, n);
        }

        System.out.printf("Datos cargados: %d nodos, %d aristas, %d refugios%n",
                nodos.size(), aristas.size(), escuelas.size());
    }

    /**
     * Busca nodos por nombre de calle (tolerante a acentos).
     * No necesitas escribir "Calle" ni "Avenida".
     */
    public List<Nodo> buscarPorNombre(String consulta) {
        if (consulta == null || consulta.length() < 2) return Collections.emptyList();

        String qNorm = normalizar(consulta);
        List<Nodo> resultados = new ArrayList<>();
        Set<String> vistos = new HashSet<>();

        // Búsqueda directa
        for (Nodo n : nodos) {
            if (n.nombre != null && normalizar(n.nombre).contains(qNorm) && !vistos.contains(n.id)) {
                vistos.add(n.id);
                resultados.add(n);
                if (resultados.size() >= 25) break;
            }
        }

        // Búsqueda sin prefijos
        if (resultados.size() < 10) {
            String[] prefijos = {"calle ", "avenida ", "andador ", "privada ", "cerrada ", "cerca de "};
            for (Nodo n : nodos) {
                if (vistos.contains(n.id) || n.nombre == null) continue;
                String nn = normalizar(n.nombre);
                for (String pref : prefijos) {
                    if (nn.startsWith(pref) && nn.substring(pref.length()).contains(qNorm)) {
                        vistos.add(n.id);
                        resultados.add(n);
                        break;
                    }
                }
                if (resultados.size() >= 25) break;
            }
        }

        return resultados;
    }

    /**
     * Encuentra el nodo más cercano a unas coordenadas dadas.
     * Se usa cuando el usuario hace click en el mapa.
     */
    public Nodo nodoCercano(double lat, double lon) {
        Nodo mejor = null;
        double mejorDist = Double.MAX_VALUE;

        for (Nodo n : nodos) {
            double dlat = (n.lat - lat) * 111000;
            double dlon = (n.lon - lon) * 99900;
            double d = Math.sqrt(dlat * dlat + dlon * dlon);
            if (d < mejorDist) {
                mejorDist = d;
                mejor = n;
            }
        }
        return mejor;
    }

    /**
     * Quita acentos y convierte a minúsculas.
     * "Cuauhtémoc" → "cuauhtemoc"
     */
    private static String normalizar(String texto) {
        String norm = java.text.Normalizer.normalize(texto, java.text.Normalizer.Form.NFD);
        return norm.replaceAll("[\\p{InCombiningDiacriticalMarks}]", "").toLowerCase();
    }
}
