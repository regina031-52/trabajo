"""Ejecuta la optimizacion desde terminal sin abrir la interfaz grafica."""

from analytics import product_metrics, summarize_order
from data_manager import DataManager
from reporting import save_optimization_plots
from tabu_search import TabuSearchOptimizer


def main() -> None:
    data_manager = DataManager()
    products = data_manager.load_products()
    sales = data_manager.load_sales()
    metrics = product_metrics(products, sales)

    budget = 5000.0
    optimizer = TabuSearchOptimizer(metrics=metrics, budget=budget)
    result = optimizer.run()
    order_id = data_manager.save_order_suggestion(result.result_table)
    plot_path = save_optimization_plots(result.history, result.result_table, budget)

    print(result.result_table[result.result_table["cajas"] > 0].to_string(index=False))
    print("\nResumen:", summarize_order(result.result_table))
    print(f"Pedido guardado: {order_id}")
    print(f"Grafica guardada en: {plot_path}")


if __name__ == "__main__":
    main()

