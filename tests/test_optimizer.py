import sys
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from analytics import product_metrics, summarize_order  # noqa: E402
from tabu_search import TabuSearchOptimizer  # noqa: E402


class OptimizerTest(unittest.TestCase):
    def test_tabu_search_returns_feasible_order(self):
        products = pd.read_csv(ROOT / "data" / "productos.csv")
        sales = pd.read_csv(ROOT / "data" / "ventas.csv")
        metrics = product_metrics(products, sales)

        budget = 5000.0
        result = TabuSearchOptimizer(metrics, budget=budget, max_iterations=80).run()
        summary = summarize_order(result.result_table)

        self.assertLessEqual(summary["costo_total"], budget)
        self.assertGreaterEqual(summary["utilidad_esperada"], 0)
        self.assertEqual(len(result.best_solution), len(metrics))

    def test_products_with_enough_inventory_get_zero_upper_bound(self):
        products = pd.DataFrame(
            [
                {
                    "producto_id": "P999",
                    "nombre": "Producto con inventario suficiente",
                    "categoria": "Prueba",
                    "piezas_por_caja": 12,
                    "costo_pieza": 10,
                    "precio_venta_pieza": 20,
                    "inventario_actual": 100,
                    "inventario_minimo": 5,
                    "stock_objetivo": 30,
                    "cajas_maximas": 10,
                    "activo": 1,
                }
            ]
        )
        sales = pd.DataFrame(
            [
                {
                    "venta_id": "V999",
                    "fecha": "2026-05-01",
                    "producto_id": "P999",
                    "cantidad": 4,
                    "precio_unitario": 20,
                }
            ]
        )

        metrics = product_metrics(products, sales)
        self.assertEqual(int(metrics.loc[0, "cajas_utiles_maximas"]), 0)
        self.assertFalse(bool(metrics.loc[0, "comprar"]))


if __name__ == "__main__":
    unittest.main()

