# Proyecto final: optimizacion de pedidos con Busqueda Tabu

Aplicacion educativa en Python para decidir que productos de belleza comprar
cada mes y cuantas cajas pedir al proveedor. El objetivo es maximizar la
utilidad esperada respetando un presupuesto y evitando comprar productos que ya
tienen suficiente inventario.

La implementacion esta pensada para una estudiante de matematicas con
conocimientos basicos de programacion: usa archivos CSV, pandas, tkinter y una
Busqueda Tabu escrita de forma directa y comentada.

## 1. Como ejecutar

```bash
pip install -r requirements.txt
python src/main.py
# En Linux tambien puede ser:
python3 src/main.py
```

Si la computadora no tiene entorno grafico, se puede probar solo la
optimizacion:

```bash
python src/run_optimization_cli.py
# En Linux tambien puede ser:
python3 src/run_optimization_cli.py
```

## 2. Arquitectura general

```text
data/
  productos.csv                 Catalogo e inventario actual
  ventas.csv                    Ventas diarias historicas
  movimientos_inventario.csv    Ajustes y salidas de inventario
  pedidos_sugeridos.csv         Resultados guardados de optimizacion

reports/
  optimizacion_busqueda_tabu.png  Grafica generada al optimizar

src/
  config.py          Rutas del proyecto
  data_manager.py    Lectura y escritura de CSV con pandas
  analytics.py       Ventas mensuales, rotacion, utilidad y necesidad
  tabu_search.py     Metaheuristica Busqueda Tabu
  reporting.py       Graficos de evolucion, presupuesto y utilidad
  gui.py             Interfaz grafica con tkinter
  main.py            Punto de entrada
```

Flujo principal:

1. El usuario registra productos y ventas diarias.
2. El sistema calcula ventas mensuales historicas por producto.
3. Se estima la demanda mensual esperada.
4. Se clasifica la rotacion: alta, media, baja o sin ventas.
5. Se calcula cuanto falta para llegar al nivel deseado de inventario.
6. La Busqueda Tabu busca un vector de cajas a pedir.
7. Se guardan el pedido sugerido y las graficas.

## 3. Archivos CSV

### `productos.csv`

| Columna | Significado |
| --- | --- |
| `producto_id` | Identificador unico, por ejemplo `P001`. |
| `nombre` | Nombre comercial del producto. |
| `categoria` | Tintes, tratamientos, shampoos, sprays, geles, etc. |
| `piezas_por_caja` | Numero de piezas que trae una caja de mayoreo. |
| `costo_pieza` | Costo de compra de una pieza. |
| `precio_venta_pieza` | Precio de venta de una pieza. |
| `inventario_actual` | Existencias actuales en piezas. |
| `inventario_minimo` | Nivel minimo deseado como seguridad. |
| `stock_objetivo` | Nivel deseado para cubrir el mes o exhibicion. |
| `cajas_maximas` | Limite superior de cajas que se permiten pedir. |
| `activo` | 1 si el producto se usa, 0 si se desactiva. |

### `ventas.csv`

| Columna | Significado |
| --- | --- |
| `venta_id` | Identificador de la venta. |
| `fecha` | Fecha en formato `YYYY-MM-DD`. |
| `producto_id` | Producto vendido. |
| `cantidad` | Piezas vendidas. |
| `precio_unitario` | Precio unitario usado en esa venta. |

### `movimientos_inventario.csv`

Registra altas, ventas y ajustes manuales para explicar por que cambio el
inventario.

### `pedidos_sugeridos.csv`

Guarda cada resultado de optimizacion: producto, cajas sugeridas, piezas,
costo total, utilidad esperada y rotacion.

## 4. Formulacion matematica

Sea:

- \(i = 1, 2, ..., n\): indice de producto.
- \(x_i\): cajas del producto \(i\) que se van a pedir.
- \(p_i\): piezas por caja del producto \(i\).
- \(c_i\): costo de compra por pieza.
- \(v_i\): precio de venta por pieza.
- \(m_i = v_i - c_i\): margen de utilidad por pieza.
- \(I_i\): inventario actual.
- \(D_i\): demanda mensual esperada calculada con ventas historicas.
- \(S_i\): stock objetivo definido por el negocio.
- \(B\): presupuesto disponible.

Primero se calcula la necesidad en piezas:

\[
N_i = \max(0, \max(D_i, S_i) - I_i)
\]

Si \(N_i = 0\), el producto ya tiene inventario suficiente y el modelo no
recomienda comprarlo.

El costo de pedir \(x_i\) cajas es:

\[
C_i(x_i) = c_i p_i x_i
\]

La utilidad esperada considera solo las piezas que probablemente se venderan o
que cubren la necesidad:

\[
U_i(x_i) = m_i \min(p_i x_i, N_i)
\]

En el codigo se agrega una penalizacion pequena si se excede la necesidad para
desalentar sobreinventario.

## 5. Modelo como mochila entera

El problema es una mochila entera acotada porque:

- Cada caja es indivisible.
- Cada producto puede tener varias cajas, pero con limite superior.
- El presupuesto es la capacidad de la mochila.
- La utilidad esperada es el valor de los objetos.

Modelo:

\[
\max \sum_{i=1}^{n} U_i(x_i)
\]

sujeto a:

\[
\sum_{i=1}^{n} c_i p_i x_i \le B
\]

\[
0 \le x_i \le L_i
\]

\[
x_i \in \mathbb{Z}
\]

donde:

\[
L_i = \min\left(\text{cajas\_maximas}_i,
\left\lceil \frac{N_i}{p_i} \right\rceil\right)
\]

## 6. Diseno de la Busqueda Tabu

### Representacion de soluciones

Una solucion es un vector entero:

```text
x = [2, 0, 1, 3, 0, ...]
```

Cada posicion representa un producto y el valor indica cuantas cajas se piden.

### Solucion inicial

Se construye una solucion inicial golosa:

1. Calcula utilidad por peso presupuestal.
2. Da un pequeno bono a productos de alta rotacion.
3. Agrega cajas mientras haya presupuesto y necesidad.

### Vecindad

Desde una solucion actual se generan vecinos:

- Aumentar una caja de un producto si no rompe el presupuesto.
- Quitar una caja de un producto.
- Intercambiar una caja: quitar de un producto y agregar a otro.

### Lista tabu

La lista tabu guarda movimientos recientes del tipo:

```text
(indice_producto, valor_anterior)
```

Esto evita volver inmediatamente a una solucion ya explorada. Se usa una cola
con longitud fija (`tabu_tenure`).

### Criterio de aspiracion

Un movimiento tabu se permite si produce una solucion mejor que la mejor
solucion global encontrada hasta el momento.

### Criterios de parada

La busqueda termina si ocurre alguno de estos casos:

1. Se alcanza el numero maximo de iteraciones.
2. Pasa cierto numero de iteraciones sin mejorar.
3. No hay vecinos factibles.

## 7. Interfaz grafica

La ventana tiene cuatro pestañas:

1. **Productos**: agregar y modificar productos.
2. **Ventas diarias**: registrar ventas; al vender se descuenta inventario.
3. **Inventario**: ajustar existencias con nota de movimiento.
4. **Optimizacion**: escribir presupuesto, ejecutar Busqueda Tabu y ver:
   - Pedido sugerido.
   - Evolucion de la mejor solucion.
   - Presupuesto utilizado.
   - Utilidad esperada por producto.

## 8. Ideas para ampliar el proyecto

- Agregar estacionalidad por mes.
- Usar pronosticos mas avanzados para demanda.
- Considerar caducidad o espacio de almacen.
- Exportar pedido final a Excel.
- Comparar Busqueda Tabu contra algoritmo goloso o programacion dinamica.

