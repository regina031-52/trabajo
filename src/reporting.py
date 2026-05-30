"""Graficas de la optimizacion."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from config import REPORTS_DIR


def create_optimization_figure(history: pd.DataFrame, result_df: pd.DataFrame, budget: float):
    """Crea una figura con los tres graficos solicitados."""

    fig, axes = plt.subplots(3, 1, figsize=(8, 9), constrained_layout=True)

    if history.empty:
        axes[0].text(0.5, 0.5, "Sin iteraciones", ha="center", va="center")
        axes[1].text(0.5, 0.5, "Sin datos", ha="center", va="center")
    else:
        axes[0].plot(history["iteracion"], history["mejor_utilidad"], color="#7b2cbf", linewidth=2)
        axes[0].set_title("Evolucion de la mejor solucion")
        axes[0].set_xlabel("Iteracion")
        axes[0].set_ylabel("Utilidad esperada")
        axes[0].grid(alpha=0.25)

        axes[1].plot(history["iteracion"], history["mejor_presupuesto_usado"], color="#2a9d8f", linewidth=2)
        axes[1].axhline(budget, color="#e76f51", linestyle="--", label="Presupuesto")
        axes[1].set_title("Presupuesto utilizado")
        axes[1].set_xlabel("Iteracion")
        axes[1].set_ylabel("Monto")
        axes[1].legend()
        axes[1].grid(alpha=0.25)

    selected = result_df[result_df["cajas"] > 0].copy()
    if selected.empty:
        axes[2].text(0.5, 0.5, "No se sugirio compra", ha="center", va="center")
    else:
        selected = selected.sort_values("utilidad_esperada", ascending=True)
        axes[2].barh(selected["nombre"], selected["utilidad_esperada"], color="#f4a261")
        axes[2].set_title("Utilidad esperada por producto sugerido")
        axes[2].set_xlabel("Utilidad esperada")
        axes[2].grid(axis="x", alpha=0.25)

    return fig


def save_optimization_plots(history: pd.DataFrame, result_df: pd.DataFrame, budget: float) -> Path:
    """Guarda los graficos en la carpeta reports."""

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORTS_DIR / "optimizacion_busqueda_tabu.png"
    fig = create_optimization_figure(history, result_df, budget)
    fig.savefig(path, dpi=140)
    plt.close(fig)
    return path

