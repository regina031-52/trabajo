"""Configuracion central del proyecto.

Mantener las rutas en un solo archivo evita repetir cadenas de texto en los
modulos. La aplicacion puede ejecutarse desde la raiz del repositorio con:

    python src/main.py
"""

from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
REPORTS_DIR = ROOT_DIR / "reports"

PRODUCTS_CSV = DATA_DIR / "productos.csv"
SALES_CSV = DATA_DIR / "ventas.csv"
INVENTORY_MOVEMENTS_CSV = DATA_DIR / "movimientos_inventario.csv"
ORDERS_CSV = DATA_DIR / "pedidos_sugeridos.csv"

