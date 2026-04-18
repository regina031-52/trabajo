package refugios;

import java.util.*;

/**
 * ============================================================
 *  VERSIÓN DE CONSOLA (Terminal)
 * ============================================================
 * 
 * Ejecutar: mvn compile exec:java -Dexec.mainClass="refugios.ConsoleApp"
 * O después de compilar: java -cp target/classes:target/dependency/* refugios.ConsoleApp
 */
public class ConsoleApp {

    // Kit de emergencia
    static final String[] SUGERENCIAS = {
        "Agua embotellada (al menos 3 litros por persona)",
        "Documentos importantes en bolsa impermeable (INE, CURP, actas)",
        "Botiquín de primeros auxilios",
        "Linterna con pilas extra",
        "Radio portátil de pilas",
        "Alimentos no perecederos (enlatados, barras, galletas)",
        "Medicamentos personales (si aplica)",
        "Ropa extra y cobija ligera",
        "Cargador portátil para celular",
        "Silbato de emergencia",
        "Dinero en efectivo (billetes y monedas)",
        "Copia de llaves de casa",
        "Artículos de higiene (papel, jabón, gel antibacterial)",
        "Mascarilla o cubrebocas",
        "Bolsas de plástico (proteger documentos)"
    };

    public static void main(String[] args) throws Exception {
        Scanner scanner = new Scanner(System.in);

        System.out.println("=".repeat(65));
        System.out.println("  REFUGIOS A* — Ciudad Renacimiento, Acapulco (CP 39715)");
        System.out.println("  Encuentra el refugio más cercano a tu ubicación");
        System.out.println("=".repeat(65));
        System.out.println();

        // 1. Cargar datos
        Datos datos = new Datos("data");
        Grafo grafo = new Grafo(datos);
        System.out.println();

        // 2. Buscar ubicación del usuario
        System.out.println("PASO 1: Escribe el nombre de tu calle");
        System.out.println("  (Solo el nombre: Escudero, Costa Azul, Zaragoza, Río Yolotla...)");
        System.out.println();

        Datos.Nodo nodoOrigen = null;
        while (nodoOrigen == null) {
            System.out.print("  Buscar: ");
            String texto = scanner.nextLine().trim();
            if (texto.isEmpty()) continue;

            List<Datos.Nodo> resultados = datos.buscarPorNombre(texto);
            if (resultados.isEmpty()) {
                System.out.printf("  '%s' no encontrado. Intenta otro.%n%n", texto);
                continue;
            }

            System.out.printf("%n  %d resultados:%n", resultados.size());
            for (int i = 0; i < resultados.size(); i++) {
                System.out.printf("    [%d] %s%n", i + 1, resultados.get(i).nombre);
            }

            System.out.print("\n  Número: ");
            try {
                int opcion = Integer.parseInt(scanner.nextLine().trim()) - 1;
                if (opcion >= 0 && opcion < resultados.size()) {
                    nodoOrigen = resultados.get(opcion);
                } else {
                    System.out.println("  Fuera de rango.");
                }
            } catch (NumberFormatException e) {
                System.out.println("  Escribe un número.");
            }
        }

        System.out.printf("%n  Ubicación: %s%n%n", nodoOrigen.nombre);

        // 3. Calcular rutas A*
        System.out.printf("PASO 2: Calculando A* a %d refugios...%n%n", datos.escuelas.size());
        List<Grafo.ResultadoRuta> rutas = grafo.calcularRutasATodas(nodoOrigen.id);

        if (rutas.isEmpty()) {
            System.out.println("ERROR: No se encontró ruta a ningún refugio.");
            return;
        }

        Grafo.ResultadoRuta mejor = rutas.get(0);

        // 4. Mostrar resultado
        System.out.println("=".repeat(65));
        System.out.println("  REFUGIO MÁS CERCANO");
        System.out.println("=".repeat(65));
        System.out.printf("%n  %s%n", mejor.escuela().nombre);
        if (mejor.escuela().alias != null && !mejor.escuela().alias.isEmpty())
            System.out.printf("  (%s)%n", mejor.escuela().alias);
        if (mejor.escuela().direccion != null && !mejor.escuela().direccion.isEmpty())
            System.out.printf("  Dir: %s%n", mejor.escuela().direccion);
        System.out.printf("  Tipo: %s  |  Estatus: %s%n", mejor.escuela().tipo,
                mejor.escuela().estatus != null ? mejor.escuela().estatus : "");
        String distStr = mejor.distanciaTotal() >= 1000
                ? String.format("%.1f km", mejor.distanciaTotal() / 1000)
                : String.format("%d m", Math.round(mejor.distanciaTotal()));
        System.out.printf("  Distancia: %s  |  Tiempo: %.1f min%n%n", distStr, mejor.tiempoMinutos());

        // 5. Instrucciones
        System.out.println("-".repeat(65));
        System.out.println("  INSTRUCCIONES PASO A PASO");
        System.out.println("-".repeat(65));
        for (Grafo.Instruccion inst : mejor.instrucciones()) {
            String marca = inst.distanciaM() == 0 ? ">>>" : "   ";
            System.out.printf("  %s Paso %d: %s%n", marca, inst.paso(), inst.texto());
        }

        // 6. Todos los refugios
        System.out.println();
        System.out.println("-".repeat(65));
        System.out.println("  TODOS LOS REFUGIOS (por distancia)");
        System.out.println("-".repeat(65));
        for (int i = 0; i < rutas.size(); i++) {
            Grafo.ResultadoRuta r = rutas.get(i);
            String d = r.distanciaTotal() >= 1000
                    ? String.format("%.1fkm", r.distanciaTotal() / 1000)
                    : String.format("%dm", Math.round(r.distanciaTotal()));
            System.out.printf("  %2d. %-42s | %7s | %5.1fmin%s%n",
                    i + 1, r.escuela().nombre.length() > 42
                            ? r.escuela().nombre.substring(0, 42)
                            : r.escuela().nombre,
                    d, r.tiempoMinutos(), i == 0 ? "  <<<" : "");
        }

        // 7. Kit de emergencia
        System.out.println();
        System.out.println("=".repeat(65));
        System.out.println("  QUÉ LLEVAR AL REFUGIO");
        System.out.println("=".repeat(65));
        for (int i = 0; i < SUGERENCIAS.length; i++) {
            System.out.printf("  %2d. %s%n", i + 1, SUGERENCIAS[i]);
        }

        System.out.println();
        System.out.println("=".repeat(65));
        System.out.println("  ¡Camina con precaución hacia tu refugio!");
        System.out.println("=".repeat(65));
    }
}
