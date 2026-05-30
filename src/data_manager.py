"""Lectura, escritura y validacion basica de los archivos CSV.

La clase DataManager concentra todas las operaciones sobre archivos. Asi la
interfaz grafica no necesita saber detalles de pandas ni de las rutas.
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from config import (
    DATA_DIR,
    INVENTORY_MOVEMENTS_CSV,
    ORDERS_CSV,
    PRODUCTS_CSV,
    SALES_CSV,
)


PRODUCT_COLUMNS = [
    "producto_id",
    "nombre",
    "categoria",
    "piezas_por_caja",
    "costo_pieza",
    "precio_venta_pieza",
    "inventario_actual",
    "inventario_minimo",
    "stock_objetivo",
    "cajas_maximas",
    "activo",
]

SALE_COLUMNS = ["venta_id", "fecha", "producto_id", "cantidad", "precio_unitario"]

MOVEMENT_COLUMNS = [
    "movimiento_id",
    "fecha",
    "producto_id",
    "tipo",
    "cantidad",
    "existencia_final",
    "nota",
]

ORDER_COLUMNS = [
    "pedido_id",
    "fecha_ejecucion",
    "producto_id",
    "nombre",
    "cajas",
    "piezas",
    "costo_total",
    "utilidad_esperada",
    "rotacion",
]


class DataManager:
    """Administra productos, ventas, inventario y pedidos sugeridos."""

    def __init__(
        self,
        data_dir: Path = DATA_DIR,
        products_path: Path = PRODUCTS_CSV,
        sales_path: Path = SALES_CSV,
        movements_path: Path = INVENTORY_MOVEMENTS_CSV,
        orders_path: Path = ORDERS_CSV,
    ) -> None:
        self.data_dir = Path(data_dir)
        self.products_path = Path(products_path)
        self.sales_path = Path(sales_path)
        self.movements_path = Path(movements_path)
        self.orders_path = Path(orders_path)
        self.ensure_files()

    def ensure_files(self) -> None:
        """Crea archivos vacios si no existen."""

        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_csv(self.products_path, PRODUCT_COLUMNS)
        self._ensure_csv(self.sales_path, SALE_COLUMNS)
        self._ensure_csv(self.movements_path, MOVEMENT_COLUMNS)
        self._ensure_csv(self.orders_path, ORDER_COLUMNS)

    @staticmethod
    def _ensure_csv(path: Path, columns: list[str]) -> None:
        if not path.exists():
            pd.DataFrame(columns=columns).to_csv(path, index=False)

    def load_products(self, include_inactive: bool = False) -> pd.DataFrame:
        products = pd.read_csv(self.products_path)
        products = self._coerce_products(products)
        if not include_inactive:
            products = products[products["activo"].astype(int) == 1]
        return products.reset_index(drop=True)

    def save_products(self, products: pd.DataFrame) -> None:
        products = self._coerce_products(products)
        products[PRODUCT_COLUMNS].to_csv(self.products_path, index=False)

    def load_sales(self) -> pd.DataFrame:
        sales = pd.read_csv(self.sales_path)
        if sales.empty:
            return pd.DataFrame(columns=SALE_COLUMNS)
        sales["fecha"] = pd.to_datetime(sales["fecha"], errors="coerce")
        sales["cantidad"] = pd.to_numeric(sales["cantidad"], errors="coerce").fillna(0).astype(int)
        sales["precio_unitario"] = pd.to_numeric(
            sales["precio_unitario"], errors="coerce"
        ).fillna(0.0)
        return sales[SALE_COLUMNS].dropna(subset=["fecha"]).reset_index(drop=True)

    def save_sales(self, sales: pd.DataFrame) -> None:
        sales = sales.copy()
        if not sales.empty:
            sales["fecha"] = pd.to_datetime(sales["fecha"]).dt.strftime("%Y-%m-%d")
        sales[SALE_COLUMNS].to_csv(self.sales_path, index=False)

    def load_movements(self) -> pd.DataFrame:
        movements = pd.read_csv(self.movements_path)
        if movements.empty:
            return pd.DataFrame(columns=MOVEMENT_COLUMNS)
        movements["fecha"] = pd.to_datetime(movements["fecha"], errors="coerce")
        movements["cantidad"] = pd.to_numeric(movements["cantidad"], errors="coerce").fillna(0).astype(int)
        movements["existencia_final"] = pd.to_numeric(
            movements["existencia_final"], errors="coerce"
        ).fillna(0).astype(int)
        return movements[MOVEMENT_COLUMNS].reset_index(drop=True)

    def load_orders(self) -> pd.DataFrame:
        return pd.read_csv(self.orders_path)

    def add_product(self, data: dict[str, Any]) -> str:
        products = self.load_products(include_inactive=True)
        product_id = self._next_id(products, "producto_id", "P")
        row = self._product_row(product_id, data)
        products = pd.concat([products, pd.DataFrame([row])], ignore_index=True)
        self.save_products(products)
        self._append_movement(
            product_id=product_id,
            movement_type="alta_producto",
            quantity=row["inventario_actual"],
            final_stock=row["inventario_actual"],
            note="Producto agregado desde la aplicacion",
            movement_date=date.today(),
        )
        return product_id

    def update_product(self, product_id: str, data: dict[str, Any]) -> None:
        products = self.load_products(include_inactive=True)
        mask = products["producto_id"] == product_id
        if not mask.any():
            raise ValueError(f"No existe el producto {product_id}.")

        current = products.loc[mask].iloc[0].to_dict()
        updated = self._product_row(product_id, {**current, **data})
        for column, value in updated.items():
            products.loc[mask, column] = value
        self.save_products(products)

    def register_sale(
        self,
        product_id: str,
        quantity: int,
        sale_date: date | datetime | str | None = None,
        price_unit: float | None = None,
    ) -> str:
        if quantity <= 0:
            raise ValueError("La cantidad vendida debe ser mayor que cero.")

        products = self.load_products(include_inactive=True)
        mask = products["producto_id"] == product_id
        if not mask.any():
            raise ValueError(f"No existe el producto {product_id}.")

        idx = products.index[mask][0]
        current_stock = int(products.loc[idx, "inventario_actual"])
        if quantity > current_stock:
            raise ValueError(
                "No hay inventario suficiente para registrar la venta. "
                f"Disponible: {current_stock} piezas."
            )

        sale_date = self._parse_date(sale_date)
        if price_unit is None:
            price_unit = float(products.loc[idx, "precio_venta_pieza"])

        sales = self.load_sales()
        sale_id = self._next_id(sales, "venta_id", "V")
        sale = {
            "venta_id": sale_id,
            "fecha": sale_date,
            "producto_id": product_id,
            "cantidad": int(quantity),
            "precio_unitario": float(price_unit),
        }
        sales = pd.concat([sales, pd.DataFrame([sale])], ignore_index=True)
        self.save_sales(sales)

        final_stock = current_stock - quantity
        products.loc[idx, "inventario_actual"] = final_stock
        self.save_products(products)
        self._append_movement(
            product_id=product_id,
            movement_type="salida_venta",
            quantity=-quantity,
            final_stock=final_stock,
            note=f"Venta {sale_id}",
            movement_date=sale_date,
        )
        return sale_id

    def set_inventory(
        self,
        product_id: str,
        new_stock: int,
        note: str = "Ajuste manual de inventario",
        movement_date: date | datetime | str | None = None,
    ) -> None:
        if new_stock < 0:
            raise ValueError("El inventario no puede ser negativo.")

        products = self.load_products(include_inactive=True)
        mask = products["producto_id"] == product_id
        if not mask.any():
            raise ValueError(f"No existe el producto {product_id}.")

        idx = products.index[mask][0]
        previous_stock = int(products.loc[idx, "inventario_actual"])
        products.loc[idx, "inventario_actual"] = int(new_stock)
        self.save_products(products)
        self._append_movement(
            product_id=product_id,
            movement_type="ajuste_manual",
            quantity=int(new_stock) - previous_stock,
            final_stock=int(new_stock),
            note=note,
            movement_date=self._parse_date(movement_date),
        )

    def save_order_suggestion(self, result_df: pd.DataFrame) -> str:
        """Guarda un resultado de optimizacion en pedidos_sugeridos.csv."""

        orders = self.load_orders()
        order_id = self._next_id(orders, "pedido_id", "O")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        rows = []
        for _, row in result_df[result_df["cajas"] > 0].iterrows():
            rows.append(
                {
                    "pedido_id": order_id,
                    "fecha_ejecucion": now,
                    "producto_id": row["producto_id"],
                    "nombre": row["nombre"],
                    "cajas": int(row["cajas"]),
                    "piezas": int(row["piezas"]),
                    "costo_total": round(float(row["costo_total"]), 2),
                    "utilidad_esperada": round(float(row["utilidad_esperada"]), 2),
                    "rotacion": row["rotacion"],
                }
            )

        if rows:
            orders = pd.concat([orders, pd.DataFrame(rows)], ignore_index=True)
            orders[ORDER_COLUMNS].to_csv(self.orders_path, index=False)
        return order_id

    def _append_movement(
        self,
        product_id: str,
        movement_type: str,
        quantity: int,
        final_stock: int,
        note: str,
        movement_date: date | datetime | str | None,
    ) -> None:
        movements = self.load_movements()
        movement_id = self._next_id(movements, "movimiento_id", "M")
        row = {
            "movimiento_id": movement_id,
            "fecha": self._parse_date(movement_date),
            "producto_id": product_id,
            "tipo": movement_type,
            "cantidad": int(quantity),
            "existencia_final": int(final_stock),
            "nota": note,
        }
        movements = pd.concat([movements, pd.DataFrame([row])], ignore_index=True)
        movements["fecha"] = pd.to_datetime(movements["fecha"]).dt.strftime("%Y-%m-%d")
        movements[MOVEMENT_COLUMNS].to_csv(self.movements_path, index=False)

    @staticmethod
    def _coerce_products(products: pd.DataFrame) -> pd.DataFrame:
        if products.empty:
            return pd.DataFrame(columns=PRODUCT_COLUMNS)

        products = products.copy()
        for column in PRODUCT_COLUMNS:
            if column not in products.columns:
                products[column] = 0 if column != "nombre" and column != "categoria" else ""

        integer_columns = [
            "piezas_por_caja",
            "inventario_actual",
            "inventario_minimo",
            "stock_objetivo",
            "cajas_maximas",
            "activo",
        ]
        float_columns = ["costo_pieza", "precio_venta_pieza"]
        for column in integer_columns:
            products[column] = pd.to_numeric(products[column], errors="coerce").fillna(0).astype(int)
        for column in float_columns:
            products[column] = pd.to_numeric(products[column], errors="coerce").fillna(0.0).astype(float)
        return products[PRODUCT_COLUMNS]

    @staticmethod
    def _product_row(product_id: str, data: dict[str, Any]) -> dict[str, Any]:
        row = {
            "producto_id": product_id,
            "nombre": str(data.get("nombre", "")).strip(),
            "categoria": str(data.get("categoria", "")).strip() or "Sin categoria",
            "piezas_por_caja": int(float(data.get("piezas_por_caja", 1))),
            "costo_pieza": float(data.get("costo_pieza", 0)),
            "precio_venta_pieza": float(data.get("precio_venta_pieza", 0)),
            "inventario_actual": int(float(data.get("inventario_actual", 0))),
            "inventario_minimo": int(float(data.get("inventario_minimo", 0))),
            "stock_objetivo": int(float(data.get("stock_objetivo", 0))),
            "cajas_maximas": int(float(data.get("cajas_maximas", 1))),
            "activo": int(float(data.get("activo", 1))),
        }

        if not row["nombre"]:
            raise ValueError("El nombre del producto es obligatorio.")
        if row["piezas_por_caja"] <= 0:
            raise ValueError("Las piezas por caja deben ser mayores que cero.")
        if row["costo_pieza"] < 0 or row["precio_venta_pieza"] < 0:
            raise ValueError("Los precios y costos no pueden ser negativos.")
        if row["precio_venta_pieza"] < row["costo_pieza"]:
            raise ValueError("El precio de venta debe ser mayor o igual al costo.")
        if row["inventario_actual"] < 0 or row["inventario_minimo"] < 0 or row["stock_objetivo"] < 0:
            raise ValueError("Los inventarios no pueden ser negativos.")
        if row["cajas_maximas"] < 0:
            raise ValueError("Las cajas maximas no pueden ser negativas.")
        return row

    @staticmethod
    def _next_id(df: pd.DataFrame, column: str, prefix: str) -> str:
        if df.empty or column not in df.columns:
            return f"{prefix}0001"
        values = df[column].dropna().astype(str)
        numbers = []
        for value in values:
            if value.startswith(prefix):
                suffix = value.replace(prefix, "", 1)
                if suffix.isdigit():
                    numbers.append(int(suffix))
        return f"{prefix}{max(numbers, default=0) + 1:04d}"

    @staticmethod
    def _parse_date(value: date | datetime | str | None) -> date:
        if value is None or value == "":
            return date.today()
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        return pd.to_datetime(value).date()

