package refugios;

import java.util.*;

/**
 * ============================================================
 *  CLASE GRAFO: Red de calles + Algoritmo A*
 * ============================================================
 * 
 * Modela la red de calles como un GRAFO donde:
 *   - Nodos = intersecciones de calles
 *   - Aristas = calles que conectan intersecciones
 *   - Peso de arista = distancia en metros
 * 
 * Implementa el algoritmo A* para encontrar la ruta más corta.
 */
public class Grafo {

    /** Cada vecino almacena: nodo destino, distancia, nombre de calle */
    public record Vecino(String nodoId, double distancia, String nombreCalle) {}

    /** Resultado de una instrucción paso a paso */
    public record Instruccion(int paso, String texto, String calle, double distanciaM, double acumuladoM) {}

    /** Resultado completo de una búsqueda A* */
    public record ResultadoRuta(
        Datos.Escuela escuela,
        double distanciaTotal,
        double tiempoMinutos,
        List<String> rutaNodos,
        List<double[]> rutaCoordenadas,
        List<Instruccion> instrucciones
    ) {}

    // ===== ESTRUCTURA DEL GRAFO =====
    // Lista de adyacencia: para cada nodo, guarda la lista de vecinos
    private final Map<String, List<Vecino>> adyacencia = new HashMap<>();
    private final Datos datos;

    /**
     * Constructor: construye el grafo a partir de los datos cargados.
     */
    public Grafo(Datos datos) {
        this.datos = datos;

        // Inicializar lista de adyacencia para cada nodo
        for (Datos.Nodo nodo : datos.nodos) {
            adyacencia.put(nodo.id, new ArrayList<>());
        }

        // Agregar aristas (bidireccionales: se puede caminar en ambos sentidos)
        for (Datos.Arista arista : datos.aristas) {
            // Dirección origen → destino
            adyacencia.computeIfAbsent(arista.origen, k -> new ArrayList<>())
                .add(new Vecino(arista.destino, arista.distancia_m, arista.nombre_calle));
            // Dirección destino → origen (grafo no dirigido)
            adyacencia.computeIfAbsent(arista.destino, k -> new ArrayList<>())
                .add(new Vecino(arista.origen, arista.distancia_m, arista.nombre_calle));
        }

        System.out.printf("Grafo construido: %d nodos, %d aristas%n",
                adyacencia.size(), datos.aristas.size());
    }

    // ============================================================
    // ALGORITMO A* (A-ESTRELLA)
    // ============================================================
    /**
     * Encuentra la ruta más corta desde 'origen' hasta 'destino'.
     * 
     * A* combina:
     *   g(n) = distancia real acumulada desde el origen
     *   h(n) = estimación (línea recta) hasta el destino
     *   f(n) = g(n) + h(n) → prioridad en la cola
     * 
     * @return [lista de nodos de la ruta, distancia total] o null si no hay ruta
     */
    public Object[] astar(String origen, String destino) {
        // Verificar que existan los nodos
        if (!adyacencia.containsKey(origen) || !adyacencia.containsKey(destino)) {
            return null;
        }
        if (origen.equals(destino)) {
            return new Object[]{List.of(origen), 0.0};
        }

        // Cola de prioridad: ordena por f_score (menor primero)
        // Cada elemento: [f_score, contador, nodo_id]
        PriorityQueue<double[]> cola = new PriorityQueue<>(Comparator.comparingDouble(a -> a[0]));
        Map<String, String> colaIds = new HashMap<>(); // Para mapear índice → nodo
        int contador = 0;

        // Estructura alternativa más clara:
        record NodoA(double f, int orden, String id) implements Comparable<NodoA> {
            public int compareTo(NodoA o) {
                int c = Double.compare(f, o.f);
                return c != 0 ? c : Integer.compare(orden, o.orden);
            }
        }

        PriorityQueue<NodoA> pq = new PriorityQueue<>();

        // padre[B] = A significa "para llegar a B, vinimos desde A"
        Map<String, String> padre = new HashMap<>();

        // g_score[n] = distancia real acumulada desde origen hasta n
        Map<String, Double> gScore = new HashMap<>();
        gScore.put(origen, 0.0);

        // Nodos ya en la cola
        Set<String> enCola = new HashSet<>();
        enCola.add(origen);

        pq.add(new NodoA(0.0, contador++, origen));

        // ---- BUCLE PRINCIPAL ----
        while (!pq.isEmpty()) {
            NodoA actual = pq.poll();
            String nodoActual = actual.id;

            // ¿Llegamos al destino?
            if (nodoActual.equals(destino)) {
                // Reconstruir la ruta
                List<String> ruta = new ArrayList<>();
                String n = destino;
                while (n != null) {
                    ruta.add(n);
                    n = padre.get(n);
                }
                Collections.reverse(ruta);
                return new Object[]{ruta, gScore.get(destino)};
            }

            enCola.remove(nodoActual);

            // Explorar vecinos
            List<Vecino> vecinos = adyacencia.getOrDefault(nodoActual, Collections.emptyList());
            for (Vecino vecino : vecinos) {
                // g tentativo = distancia acumulada si vamos por este camino
                double gTentativo = gScore.getOrDefault(nodoActual, Double.MAX_VALUE) + vecino.distancia;

                // ¿Es mejor que lo que ya teníamos?
                if (gTentativo < gScore.getOrDefault(vecino.nodoId, Double.MAX_VALUE)) {
                    padre.put(vecino.nodoId, nodoActual);
                    gScore.put(vecino.nodoId, gTentativo);

                    // f = g + h
                    double f = gTentativo + heuristica(vecino.nodoId, destino);

                    if (!enCola.contains(vecino.nodoId)) {
                        pq.add(new NodoA(f, contador++, vecino.nodoId));
                        enCola.add(vecino.nodoId);
                    }
                }
            }
        }

        // No se encontró ruta
        return null;
    }

    /**
     * HEURÍSTICA: distancia en línea recta entre dos nodos (en metros).
     * Es ADMISIBLE porque la línea recta siempre es ≤ distancia por calles.
     */
    private double heuristica(String nodoA, String nodoB) {
        Datos.Nodo a = datos.nodosPorId.get(nodoA);
        Datos.Nodo b = datos.nodosPorId.get(nodoB);
        if (a == null || b == null) return 0;

        double dlat = (b.lat - a.lat) * 111000;   // grados → metros (latitud)
        double dlon = (b.lon - a.lon) * 99900;    // grados → metros (longitud en Acapulco)
        return Math.sqrt(dlat * dlat + dlon * dlon);
    }

    /**
     * Calcula la ruta A* a TODAS las escuelas y retorna todas ordenadas por distancia.
     */
    @SuppressWarnings("unchecked")
    public List<ResultadoRuta> calcularRutasATodas(String nodoOrigen) {
        List<ResultadoRuta> rutas = new ArrayList<>();

        for (Datos.Escuela esc : datos.escuelas) {
            Object[] resultado = astar(nodoOrigen, esc.nodo_id);
            if (resultado != null) {
                List<String> rutaNodos = (List<String>) resultado[0];
                double distancia = (Double) resultado[1];
                double tiempo = distancia / 83.33; // 5 km/h

                // Obtener coordenadas de la ruta
                List<double[]> coords = new ArrayList<>();
                for (String nid : rutaNodos) {
                    Datos.Nodo n = datos.nodosPorId.get(nid);
                    if (n != null) coords.add(new double[]{n.lat, n.lon});
                }

                // Generar instrucciones
                List<Instruccion> instrucciones = generarInstrucciones(rutaNodos);

                rutas.add(new ResultadoRuta(esc, Math.round(distancia * 100.0) / 100.0,
                        Math.round(tiempo * 10.0) / 10.0, rutaNodos, coords, instrucciones));
            }
        }

        // Ordenar por distancia
        rutas.sort(Comparator.comparingDouble(ResultadoRuta::distanciaTotal));
        return rutas;
    }

    // ============================================================
    // INSTRUCCIONES PASO A PASO
    // ============================================================

    /**
     * Genera instrucciones agrupando tramos de la misma calle.
     */
    public List<Instruccion> generarInstrucciones(List<String> ruta) {
        if (ruta.size() < 2) return Collections.emptyList();

        List<Instruccion> pasos = new ArrayList<>();
        String calleActual = null;
        double distCalle = 0;
        int numPaso = 0;
        double acumulado = 0;

        for (int i = 0; i < ruta.size() - 1; i++) {
            String n1 = ruta.get(i), n2 = ruta.get(i + 1);
            String nombreCalle = "Sin nombre";
            double dist = 0;

            // Buscar la arista entre n1 y n2
            for (Vecino v : adyacencia.getOrDefault(n1, Collections.emptyList())) {
                if (v.nodoId.equals(n2)) {
                    nombreCalle = v.nombreCalle;
                    dist = v.distancia;
                    break;
                }
            }

            if (calleActual == null) {
                calleActual = nombreCalle;
                distCalle = dist;
            } else if (nombreCalle.equals(calleActual)) {
                distCalle += dist;
            } else {
                numPaso++;
                acumulado += distCalle;
                String giro = (i >= 2) ? calcularGiro(ruta.get(i-2), ruta.get(i-1), ruta.get(i)) : "Camina por";
                String texto = (numPaso == 1)
                    ? String.format("Sal caminando por %s (%d m)", calleActual, Math.round(distCalle))
                    : String.format("%s hacia %s (%d m por %s)", giro, nombreCalle, Math.round(distCalle), calleActual);

                pasos.add(new Instruccion(numPaso, texto, calleActual, Math.round(distCalle * 10.0) / 10.0, Math.round(acumulado * 10.0) / 10.0));
                calleActual = nombreCalle;
                distCalle = dist;
            }
        }

        if (calleActual != null && distCalle > 0) {
            numPaso++;
            acumulado += distCalle;
            pasos.add(new Instruccion(numPaso,
                String.format("Continúa por %s hasta el refugio (%d m)", calleActual, Math.round(distCalle)),
                calleActual, Math.round(distCalle * 10.0) / 10.0, Math.round(acumulado * 10.0) / 10.0));
        }

        numPaso++;
        pasos.add(new Instruccion(numPaso, "¡Llegaste al refugio!", "Destino", 0, Math.round(acumulado * 10.0) / 10.0));
        return pasos;
    }

    /** Calcula el ángulo de dirección entre dos nodos */
    private double bearing(String a, String b) {
        Datos.Nodo n1 = datos.nodosPorId.get(a), n2 = datos.nodosPorId.get(b);
        if (n1 == null || n2 == null) return 0;
        return (Math.toDegrees(Math.atan2(n2.lon - n1.lon, n2.lat - n1.lat)) + 360) % 360;
    }

    /** Determina la dirección del giro */
    private String calcularGiro(String a, String b, String c) {
        double diff = (bearing(b, c) - bearing(a, b) + 360) % 360;
        if (diff < 30 || diff > 330) return "Continúa recto";
        if (diff < 150) return "Gira a la derecha";
        if (diff <= 210) return "Da vuelta";
        return "Gira a la izquierda";
    }
}
