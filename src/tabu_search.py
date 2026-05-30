"""Implementacion completa y legible de Busqueda Tabu.

El problema se modela como una mochila entera acotada:

    x_i = numero de cajas a pedir del producto i
    0 <= x_i <= cajas_utiles_maximas_i, x_i entero
    sum(costo_caja_i * x_i) <= presupuesto

La funcion objetivo maximiza la utilidad esperada del pedido.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import random

import pandas as pd

from analytics import expected_profit_for_boxes, order_result_from_solution


@dataclass
class TabuResult:
    best_solution: list[int]
    best_profit: float
    best_budget_used: float
    result_table: pd.DataFrame
    history: pd.DataFrame
    iterations: int


class TabuSearchOptimizer:
    """Optimizador de pedidos mensuales con Busqueda Tabu."""

    def __init__(
        self,
        metrics: pd.DataFrame,
        budget: float,
        tabu_tenure: int = 8,
        max_iterations: int = 250,
        max_no_improve: int = 60,
        random_seed: int = 42,
        max_neighbors: int = 120,
    ) -> None:
        if budget <= 0:
            raise ValueError("El presupuesto debe ser mayor que cero.")

        self.metrics = metrics.reset_index(drop=True).copy()
        self.budget = float(budget)
        self.tabu_tenure = int(tabu_tenure)
        self.max_iterations = int(max_iterations)
        self.max_no_improve = int(max_no_improve)
        self.max_neighbors = int(max_neighbors)
        self.random = random.Random(random_seed)

        self.costs = self.metrics["costo_caja"].astype(float).tolist()
        self.upper_bounds = self.metrics["cajas_utiles_maximas"].astype(int).tolist()
        self.value_cache = self._build_value_cache()

    def run(self) -> TabuResult:
        """Ejecuta la busqueda y devuelve la mejor solucion encontrada."""

        current = self._initial_solution()
        current_profit = self._profit(current)
        best = current.copy()
        best_profit = current_profit

        tabu_list: deque[tuple[int, int]] = deque(maxlen=self.tabu_tenure)
        history_rows = []
        no_improve = 0

        for iteration in range(1, self.max_iterations + 1):
            candidates = self._neighbors(current)
            if not candidates:
                break

            chosen_solution = None
            chosen_profit = float("-inf")
            chosen_move: tuple[int, int] | None = None

            for candidate, move in candidates:
                profit = self._profit(candidate)
                is_tabu = move in tabu_list
                aspiration = profit > best_profit
                if (not is_tabu or aspiration) and profit > chosen_profit:
                    chosen_solution = candidate
                    chosen_profit = profit
                    chosen_move = move

            if chosen_solution is None:
                break

            # Guardamos el valor anterior como tabu para evitar regresar de inmediato.
            changed_index = chosen_move[0] if chosen_move else 0
            tabu_list.append((changed_index, current[changed_index]))
            current = chosen_solution
            current_profit = chosen_profit

            if current_profit > best_profit:
                best = current.copy()
                best_profit = current_profit
                no_improve = 0
            else:
                no_improve += 1

            history_rows.append(
                {
                    "iteracion": iteration,
                    "utilidad_actual": round(current_profit, 2),
                    "mejor_utilidad": round(best_profit, 2),
                    "presupuesto_usado": round(self._budget_used(current), 2),
                    "mejor_presupuesto_usado": round(self._budget_used(best), 2),
                }
            )

            if no_improve >= self.max_no_improve:
                break

        result_table = order_result_from_solution(self.metrics, best)
        history = pd.DataFrame(history_rows)
        return TabuResult(
            best_solution=best,
            best_profit=round(best_profit, 2),
            best_budget_used=round(self._budget_used(best), 2),
            result_table=result_table,
            history=history,
            iterations=len(history_rows),
        )

    def _build_value_cache(self) -> list[list[float]]:
        value_cache: list[list[float]] = []
        for _, row in self.metrics.iterrows():
            values = [expected_profit_for_boxes(row, boxes) for boxes in range(int(row["cajas_utiles_maximas"]) + 1)]
            value_cache.append(values)
        return value_cache

    def _initial_solution(self) -> list[int]:
        """Construye una solucion inicial golosa y factible."""

        solution = [0] * len(self.metrics)
        remaining_budget = self.budget

        items = []
        for i, row in self.metrics.iterrows():
            if self.upper_bounds[i] <= 0 or self.costs[i] <= 0:
                continue
            value_first_box = self.value_cache[i][1] if len(self.value_cache[i]) > 1 else 0
            rotation_bonus = {"Alta": 1.15, "Media": 1.0, "Baja": 0.85, "Sin ventas": 0.6}.get(
                row["rotacion"], 1.0
            )
            score = (value_first_box / self.costs[i]) * rotation_bonus
            items.append((score, i))

        for _, i in sorted(items, reverse=True):
            while solution[i] < self.upper_bounds[i] and remaining_budget >= self.costs[i]:
                next_solution = solution.copy()
                next_solution[i] += 1
                if self._profit(next_solution) < self._profit(solution):
                    break
                solution = next_solution
                remaining_budget -= self.costs[i]
        return solution

    def _neighbors(self, solution: list[int]) -> list[tuple[list[int], tuple[int, int]]]:
        """Genera vecinos cambiando una caja de un producto.

        Cada vecino suma una caja o quita una caja. La lista se mezcla para que
        la exploracion no dependa del orden de los productos en el CSV.
        """

        neighbors: list[tuple[list[int], tuple[int, int]]] = []
        for i in range(len(solution)):
            for delta in (-1, 1):
                new_value = solution[i] + delta
                if new_value < 0 or new_value > self.upper_bounds[i]:
                    continue
                candidate = solution.copy()
                candidate[i] = new_value
                if self._is_feasible(candidate):
                    neighbors.append((candidate, (i, new_value)))

        # Vecinos tipo intercambio: quitar una caja de i y agregar una a j.
        for i in range(len(solution)):
            if solution[i] <= 0:
                continue
            for j in range(len(solution)):
                if i == j or solution[j] >= self.upper_bounds[j]:
                    continue
                candidate = solution.copy()
                candidate[i] -= 1
                candidate[j] += 1
                if self._is_feasible(candidate):
                    neighbors.append((candidate, (j, candidate[j])))

        self.random.shuffle(neighbors)
        return neighbors[: self.max_neighbors]

    def _profit(self, solution: list[int]) -> float:
        return sum(self.value_cache[i][boxes] for i, boxes in enumerate(solution))

    def _budget_used(self, solution: list[int]) -> float:
        return sum(self.costs[i] * boxes for i, boxes in enumerate(solution))

    def _is_feasible(self, solution: list[int]) -> bool:
        if any(value < 0 or value > upper for value, upper in zip(solution, self.upper_bounds)):
            return False
        return self._budget_used(solution) <= self.budget + 1e-9

