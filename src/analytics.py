"""Calculos de ventas historicas, rotacion y utilidad esperada."""

from __future__ import annotations

import math

import pandas as pd


def monthly_sales(sales: pd.DataFrame) -> pd.DataFrame:
    """Agrupa las ventas por producto y mes.

    Devuelve columnas: producto_id, mes y cantidad.
    """

    if sales.empty:
        return pd.DataFrame(columns=["producto_id", "mes", "cantidad"])

    sales = sales.copy()
    sales["fecha"] = pd.to_datetime(sales["fecha"])
    sales["mes"] = sales["fecha"].dt.to_period("M").astype(str)
    return (
        sales.groupby(["producto_id", "mes"], as_index=False)["cantidad"]
        .sum()
        .sort_values(["producto_id", "mes"])
        .reset_index(drop=True)
    )


def product_metrics(products: pd.DataFrame, sales: pd.DataFrame, months_window: int = 6) -> pd.DataFrame:
    """Combina productos con indicadores para tomar decisiones de compra.

    La demanda esperada usa las ventas mensuales promedio. Si hay pocos datos,
    se aprovechan todos los meses disponibles. El stock objetivo permite pedir
    productos aunque el promedio historico sea bajo, por ejemplo para mantener
    una exhibicion minima.
    """

    products = products.copy()
    if products.empty:
        return _empty_metrics()

    month_table = monthly_sales(sales)
    if month_table.empty:
        products["ventas_mensuales_promedio"] = 0.0
        products["ventas_totales"] = 0
    else:
        months = sorted(month_table["mes"].unique())[-months_window:]
        relevant_sales = month_table[month_table["mes"].isin(months)]
        sales_by_product = relevant_sales.groupby("producto_id")["cantidad"].agg(["sum", "mean"])
        products = products.merge(
            sales_by_product.rename(columns={"sum": "ventas_totales", "mean": "ventas_mensuales_promedio"}),
            left_on="producto_id",
            right_index=True,
            how="left",
        )
        products["ventas_totales"] = products["ventas_totales"].fillna(0).astype(int)
        products["ventas_mensuales_promedio"] = products["ventas_mensuales_promedio"].fillna(0.0)

    products["margen_pieza"] = products["precio_venta_pieza"] - products["costo_pieza"]
    products["costo_caja"] = products["costo_pieza"] * products["piezas_por_caja"]
    products["utilidad_caja"] = products["margen_pieza"] * products["piezas_por_caja"]

    products["demanda_esperada"] = products["ventas_mensuales_promedio"].round(2)
    products["nivel_deseado"] = products[["demanda_esperada", "stock_objetivo"]].max(axis=1)
    products["necesidad_piezas"] = (
        products["nivel_deseado"] - products["inventario_actual"]
    ).clip(lower=0).round().astype(int)
    products["cajas_utiles_maximas"] = products.apply(_useful_boxes, axis=1)
    products["cobertura_meses"] = products.apply(_coverage_months, axis=1)
    products["rotacion"] = _classify_rotation(products)
    products["utilidad_maxima_esperada"] = products["necesidad_piezas"] * products["margen_pieza"]
    products["comprar"] = products["cajas_utiles_maximas"] > 0

    metric_columns = [
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
        "ventas_totales",
        "ventas_mensuales_promedio",
        "demanda_esperada",
        "nivel_deseado",
        "necesidad_piezas",
        "cajas_utiles_maximas",
        "costo_caja",
        "margen_pieza",
        "utilidad_caja",
        "utilidad_maxima_esperada",
        "cobertura_meses",
        "rotacion",
        "comprar",
    ]
    return products[metric_columns].reset_index(drop=True)


def expected_profit_for_boxes(row: pd.Series, boxes: int) -> float:
    """Utilidad esperada de pedir cierto numero de cajas de un producto."""

    pieces = int(boxes) * int(row["piezas_por_caja"])
    useful_pieces = min(pieces, int(row["necesidad_piezas"]))
    excess_pieces = max(0, pieces - int(row["necesidad_piezas"]))

    # Penaliza suavemente el exceso para favorecer compras que no inmovilicen capital.
    overstock_penalty = 0.05 * excess_pieces * float(row["costo_pieza"])
    return float(useful_pieces * row["margen_pieza"] - overstock_penalty)


def order_result_from_solution(metrics: pd.DataFrame, solution: list[int]) -> pd.DataFrame:
    """Convierte el vector de cajas en una tabla legible."""

    rows = []
    for idx, row in metrics.reset_index(drop=True).iterrows():
        boxes = int(solution[idx])
        pieces = boxes * int(row["piezas_por_caja"])
        rows.append(
            {
                "producto_id": row["producto_id"],
                "nombre": row["nombre"],
                "categoria": row["categoria"],
                "rotacion": row["rotacion"],
                "inventario_actual": int(row["inventario_actual"]),
                "demanda_esperada": round(float(row["demanda_esperada"]), 2),
                "necesidad_piezas": int(row["necesidad_piezas"]),
                "cajas": boxes,
                "piezas": pieces,
                "costo_total": round(pieces * float(row["costo_pieza"]), 2),
                "utilidad_esperada": round(expected_profit_for_boxes(row, boxes), 2),
            }
        )
    result = pd.DataFrame(rows)
    return result.sort_values(["cajas", "utilidad_esperada"], ascending=[False, False]).reset_index(drop=True)


def summarize_order(result_df: pd.DataFrame) -> dict[str, float]:
    """Resume costo y utilidad de un pedido sugerido."""

    if result_df.empty:
        return {"costo_total": 0.0, "utilidad_esperada": 0.0, "productos_pedidos": 0}
    selected = result_df[result_df["cajas"] > 0]
    return {
        "costo_total": round(float(selected["costo_total"].sum()), 2),
        "utilidad_esperada": round(float(selected["utilidad_esperada"].sum()), 2),
        "productos_pedidos": int((selected["cajas"] > 0).sum()),
    }


def _useful_boxes(row: pd.Series) -> int:
    need = int(row["necesidad_piezas"])
    if need <= 0:
        return 0
    boxes = math.ceil(need / int(row["piezas_por_caja"]))
    return min(int(row["cajas_maximas"]), boxes)


def _coverage_months(row: pd.Series) -> float:
    average = float(row["ventas_mensuales_promedio"])
    if average <= 0:
        return 999.0
    return round(float(row["inventario_actual"]) / average, 2)


def _classify_rotation(products: pd.DataFrame) -> list[str]:
    averages = products["ventas_mensuales_promedio"].astype(float)
    positive = averages[averages > 0]
    if positive.empty:
        return ["Sin ventas"] * len(products)

    q_low = positive.quantile(0.33)
    q_high = positive.quantile(0.66)
    classes = []
    for average, coverage in zip(averages, products["cobertura_meses"]):
        if average <= 0:
            classes.append("Sin ventas")
        elif average >= q_high or coverage < 1:
            classes.append("Alta")
        elif average <= q_low and coverage > 2:
            classes.append("Baja")
        else:
            classes.append("Media")
    return classes


def _empty_metrics() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
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
            "ventas_totales",
            "ventas_mensuales_promedio",
            "demanda_esperada",
            "nivel_deseado",
            "necesidad_piezas",
            "cajas_utiles_maximas",
            "costo_caja",
            "margen_pieza",
            "utilidad_caja",
            "utilidad_maxima_esperada",
            "cobertura_meses",
            "rotacion",
            "comprar",
        ]
    )

