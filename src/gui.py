"""Interfaz grafica sencilla con tkinter.

La app usa pestañas para separar tareas:
1. Productos
2. Ventas diarias
3. Inventario
4. Optimizacion con Busqueda Tabu
"""

from __future__ import annotations

from datetime import date
import tkinter as tk
from tkinter import messagebox, ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd

from analytics import product_metrics, summarize_order
from data_manager import DataManager
from reporting import create_optimization_figure, save_optimization_plots
from tabu_search import TabuSearchOptimizer


class InventoryApp(tk.Tk):
    """Ventana principal de la aplicacion."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Pedidos optimizados con Busqueda Tabu")
        self.geometry("1180x760")
        self.minsize(1000, 680)

        self.data_manager = DataManager()
        self.selected_product_id: str | None = None
        self.optimization_canvas: FigureCanvasTkAgg | None = None

        self._configure_style()
        self._build_layout()
        self.refresh_all()

    def _configure_style(self) -> None:
        self.configure(bg="#f8f5ff")
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#f8f5ff")
        style.configure("Card.TFrame", background="#ffffff", relief="flat")
        style.configure("TLabel", background="#f8f5ff", foreground="#22223b", font=("Segoe UI", 10))
        style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"), foreground="#4a148c")
        style.configure("Subtitle.TLabel", font=("Segoe UI", 11), foreground="#5f5f75")
        style.configure("Accent.TButton", background="#7b2cbf", foreground="#ffffff", font=("Segoe UI", 10, "bold"))
        style.map("Accent.TButton", background=[("active", "#5a189a")])
        style.configure("Treeview", rowheight=26, font=("Segoe UI", 9))
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))

    def _build_layout(self) -> None:
        header = ttk.Frame(self, padding=(18, 14, 18, 8))
        header.pack(fill="x")
        ttk.Label(header, text="Optimizacion mensual de pedidos", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text="Inventario de productos de belleza usando la metaheuristica Busqueda Tabu",
            style="Subtitle.TLabel",
        ).pack(anchor="w")

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=16, pady=10)

        self.products_tab = ttk.Frame(self.notebook, padding=12)
        self.sales_tab = ttk.Frame(self.notebook, padding=12)
        self.inventory_tab = ttk.Frame(self.notebook, padding=12)
        self.optimization_tab = ttk.Frame(self.notebook, padding=12)

        self.notebook.add(self.products_tab, text="Productos")
        self.notebook.add(self.sales_tab, text="Ventas diarias")
        self.notebook.add(self.inventory_tab, text="Inventario")
        self.notebook.add(self.optimization_tab, text="Optimizacion")

        self._build_products_tab()
        self._build_sales_tab()
        self._build_inventory_tab()
        self._build_optimization_tab()

    def _build_products_tab(self) -> None:
        self.products_tab.columnconfigure(0, weight=3)
        self.products_tab.columnconfigure(1, weight=2)
        self.products_tab.rowconfigure(0, weight=1)

        table_frame = ttk.Frame(self.products_tab)
        table_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

        columns = (
            "producto_id",
            "nombre",
            "categoria",
            "piezas_por_caja",
            "costo_pieza",
            "precio_venta_pieza",
            "inventario_actual",
            "stock_objetivo",
            "cajas_maximas",
        )
        self.products_tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        headings = {
            "producto_id": "ID",
            "nombre": "Producto",
            "categoria": "Categoria",
            "piezas_por_caja": "Pzas/caja",
            "costo_pieza": "Costo",
            "precio_venta_pieza": "Precio",
            "inventario_actual": "Stock",
            "stock_objetivo": "Objetivo",
            "cajas_maximas": "Max cajas",
        }
        widths = {
            "producto_id": 70,
            "nombre": 180,
            "categoria": 110,
            "piezas_por_caja": 75,
            "costo_pieza": 75,
            "precio_venta_pieza": 75,
            "inventario_actual": 70,
            "stock_objetivo": 70,
            "cajas_maximas": 75,
        }
        for column in columns:
            self.products_tree.heading(column, text=headings[column])
            self.products_tree.column(column, width=widths[column], anchor="center")
        self.products_tree.pack(fill="both", expand=True)
        self.products_tree.bind("<<TreeviewSelect>>", self._on_product_selected)

        form_frame = ttk.LabelFrame(self.products_tab, text="Agregar o modificar producto", padding=12)
        form_frame.grid(row=0, column=1, sticky="nsew")

        self.product_entries: dict[str, ttk.Entry] = {}
        fields = [
            ("nombre", "Nombre"),
            ("categoria", "Categoria"),
            ("piezas_por_caja", "Piezas por caja"),
            ("costo_pieza", "Costo por pieza"),
            ("precio_venta_pieza", "Precio de venta"),
            ("inventario_actual", "Inventario actual"),
            ("inventario_minimo", "Inventario minimo"),
            ("stock_objetivo", "Stock objetivo"),
            ("cajas_maximas", "Cajas maximas a pedir"),
        ]
        for row, (key, label) in enumerate(fields):
            ttk.Label(form_frame, text=label).grid(row=row, column=0, sticky="w", pady=4)
            entry = ttk.Entry(form_frame)
            entry.grid(row=row, column=1, sticky="ew", pady=4, padx=(8, 0))
            self.product_entries[key] = entry
        form_frame.columnconfigure(1, weight=1)

        buttons = ttk.Frame(form_frame)
        buttons.grid(row=len(fields), column=0, columnspan=2, sticky="ew", pady=(12, 0))
        ttk.Button(buttons, text="Agregar producto", style="Accent.TButton", command=self.add_product).pack(
            side="left", padx=(0, 8)
        )
        ttk.Button(buttons, text="Guardar cambios", command=self.update_product).pack(side="left", padx=(0, 8))
        ttk.Button(buttons, text="Limpiar", command=self.clear_product_form).pack(side="left")

    def _build_sales_tab(self) -> None:
        self.sales_tab.columnconfigure(0, weight=1)
        self.sales_tab.columnconfigure(1, weight=2)
        self.sales_tab.rowconfigure(0, weight=1)

        form = ttk.LabelFrame(self.sales_tab, text="Registrar venta diaria", padding=12)
        form.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

        self.sale_product_var = tk.StringVar()
        self.sale_date_var = tk.StringVar(value=date.today().isoformat())
        self.sale_quantity_var = tk.StringVar()
        self.sale_price_var = tk.StringVar()

        ttk.Label(form, text="Producto").grid(row=0, column=0, sticky="w", pady=5)
        self.sale_product_combo = ttk.Combobox(form, textvariable=self.sale_product_var, state="readonly")
        self.sale_product_combo.grid(row=0, column=1, sticky="ew", pady=5)

        ttk.Label(form, text="Fecha (YYYY-MM-DD)").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(form, textvariable=self.sale_date_var).grid(row=1, column=1, sticky="ew", pady=5)

        ttk.Label(form, text="Cantidad vendida").grid(row=2, column=0, sticky="w", pady=5)
        ttk.Entry(form, textvariable=self.sale_quantity_var).grid(row=2, column=1, sticky="ew", pady=5)

        ttk.Label(form, text="Precio unitario opcional").grid(row=3, column=0, sticky="w", pady=5)
        ttk.Entry(form, textvariable=self.sale_price_var).grid(row=3, column=1, sticky="ew", pady=5)

        ttk.Button(form, text="Registrar venta", style="Accent.TButton", command=self.register_sale).grid(
            row=4, column=0, columnspan=2, sticky="ew", pady=(12, 0)
        )
        form.columnconfigure(1, weight=1)

        table_frame = ttk.LabelFrame(self.sales_tab, text="Ventas registradas", padding=8)
        table_frame.grid(row=0, column=1, sticky="nsew")
        self.sales_tree = ttk.Treeview(
            table_frame,
            columns=("venta_id", "fecha", "producto_id", "cantidad", "precio_unitario"),
            show="headings",
        )
        for column, text in [
            ("venta_id", "ID"),
            ("fecha", "Fecha"),
            ("producto_id", "Producto"),
            ("cantidad", "Cantidad"),
            ("precio_unitario", "Precio"),
        ]:
            self.sales_tree.heading(column, text=text)
            self.sales_tree.column(column, width=120, anchor="center")
        self.sales_tree.pack(fill="both", expand=True)

    def _build_inventory_tab(self) -> None:
        self.inventory_tab.columnconfigure(0, weight=1)
        self.inventory_tab.columnconfigure(1, weight=2)
        self.inventory_tab.rowconfigure(0, weight=1)

        form = ttk.LabelFrame(self.inventory_tab, text="Actualizar inventario", padding=12)
        form.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

        self.inventory_product_var = tk.StringVar()
        self.inventory_new_stock_var = tk.StringVar()
        self.inventory_note_var = tk.StringVar(value="Conteo fisico")
        self.inventory_current_label = ttk.Label(form, text="Inventario actual: -")

        ttk.Label(form, text="Producto").grid(row=0, column=0, sticky="w", pady=5)
        self.inventory_product_combo = ttk.Combobox(
            form,
            textvariable=self.inventory_product_var,
            state="readonly",
        )
        self.inventory_product_combo.grid(row=0, column=1, sticky="ew", pady=5)
        self.inventory_product_combo.bind("<<ComboboxSelected>>", lambda _: self.update_inventory_label())

        self.inventory_current_label.grid(row=1, column=0, columnspan=2, sticky="w", pady=5)

        ttk.Label(form, text="Nuevo inventario").grid(row=2, column=0, sticky="w", pady=5)
        ttk.Entry(form, textvariable=self.inventory_new_stock_var).grid(row=2, column=1, sticky="ew", pady=5)

        ttk.Label(form, text="Nota").grid(row=3, column=0, sticky="w", pady=5)
        ttk.Entry(form, textvariable=self.inventory_note_var).grid(row=3, column=1, sticky="ew", pady=5)

        ttk.Button(form, text="Actualizar inventario", style="Accent.TButton", command=self.set_inventory).grid(
            row=4, column=0, columnspan=2, sticky="ew", pady=(12, 0)
        )
        form.columnconfigure(1, weight=1)

        table_frame = ttk.LabelFrame(self.inventory_tab, text="Movimientos de inventario", padding=8)
        table_frame.grid(row=0, column=1, sticky="nsew")
        self.movements_tree = ttk.Treeview(
            table_frame,
            columns=("movimiento_id", "fecha", "producto_id", "tipo", "cantidad", "existencia_final", "nota"),
            show="headings",
        )
        for column, text in [
            ("movimiento_id", "ID"),
            ("fecha", "Fecha"),
            ("producto_id", "Producto"),
            ("tipo", "Tipo"),
            ("cantidad", "Cambio"),
            ("existencia_final", "Final"),
            ("nota", "Nota"),
        ]:
            self.movements_tree.heading(column, text=text)
            self.movements_tree.column(column, width=105, anchor="center")
        self.movements_tree.pack(fill="both", expand=True)

    def _build_optimization_tab(self) -> None:
        self.optimization_tab.columnconfigure(0, weight=1)
        self.optimization_tab.columnconfigure(1, weight=2)
        self.optimization_tab.rowconfigure(1, weight=1)

        controls = ttk.LabelFrame(self.optimization_tab, text="Parametros", padding=12)
        controls.grid(row=0, column=0, sticky="ew", padx=(0, 12))

        self.budget_var = tk.StringVar(value="5000")
        self.iterations_var = tk.StringVar(value="250")
        self.no_improve_var = tk.StringVar(value="60")
        self.tenure_var = tk.StringVar(value="8")

        fields = [
            ("Presupuesto disponible", self.budget_var),
            ("Iteraciones maximas", self.iterations_var),
            ("Max. sin mejora", self.no_improve_var),
            ("Tamano lista tabu", self.tenure_var),
        ]
        for row, (label, variable) in enumerate(fields):
            ttk.Label(controls, text=label).grid(row=row, column=0, sticky="w", pady=4)
            ttk.Entry(controls, textvariable=variable).grid(row=row, column=1, sticky="ew", pady=4, padx=(8, 0))
        controls.columnconfigure(1, weight=1)

        ttk.Button(
            controls,
            text="Ejecutar optimizacion",
            style="Accent.TButton",
            command=self.run_optimization,
        ).grid(row=len(fields), column=0, columnspan=2, sticky="ew", pady=(10, 0))

        self.optimization_summary = ttk.Label(
            self.optimization_tab,
            text="Ejecuta la optimizacion para ver el pedido sugerido.",
            style="Subtitle.TLabel",
        )
        self.optimization_summary.grid(row=0, column=1, sticky="w")

        result_frame = ttk.LabelFrame(self.optimization_tab, text="Pedido sugerido", padding=8)
        result_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 12), pady=(12, 0))
        self.result_tree = ttk.Treeview(
            result_frame,
            columns=("producto_id", "nombre", "rotacion", "necesidad_piezas", "cajas", "costo_total", "utilidad_esperada"),
            show="headings",
        )
        for column, text, width in [
            ("producto_id", "ID", 70),
            ("nombre", "Producto", 170),
            ("rotacion", "Rotacion", 80),
            ("necesidad_piezas", "Necesidad", 80),
            ("cajas", "Cajas", 70),
            ("costo_total", "Costo", 90),
            ("utilidad_esperada", "Utilidad", 90),
        ]:
            self.result_tree.heading(column, text=text)
            self.result_tree.column(column, width=width, anchor="center")
        self.result_tree.pack(fill="both", expand=True)

        self.graph_frame = ttk.LabelFrame(self.optimization_tab, text="Graficos", padding=8)
        self.graph_frame.grid(row=1, column=1, sticky="nsew", pady=(12, 0))

    def refresh_all(self) -> None:
        self.refresh_products()
        self.refresh_sales()
        self.refresh_movements()
        self.refresh_product_combos()

    def refresh_products(self) -> None:
        self.products_tree.delete(*self.products_tree.get_children())
        products = self.data_manager.load_products(include_inactive=True)
        for _, row in products.iterrows():
            self.products_tree.insert(
                "",
                "end",
                values=(
                    row["producto_id"],
                    row["nombre"],
                    row["categoria"],
                    int(row["piezas_por_caja"]),
                    f"{float(row['costo_pieza']):.2f}",
                    f"{float(row['precio_venta_pieza']):.2f}",
                    int(row["inventario_actual"]),
                    int(row["stock_objetivo"]),
                    int(row["cajas_maximas"]),
                ),
            )

    def refresh_sales(self) -> None:
        self.sales_tree.delete(*self.sales_tree.get_children())
        sales = self.data_manager.load_sales().sort_values("fecha", ascending=False)
        for _, row in sales.head(100).iterrows():
            self.sales_tree.insert(
                "",
                "end",
                values=(
                    row["venta_id"],
                    pd.to_datetime(row["fecha"]).strftime("%Y-%m-%d"),
                    row["producto_id"],
                    int(row["cantidad"]),
                    f"{float(row['precio_unitario']):.2f}",
                ),
            )

    def refresh_movements(self) -> None:
        self.movements_tree.delete(*self.movements_tree.get_children())
        movements = self.data_manager.load_movements().sort_values("fecha", ascending=False)
        for _, row in movements.head(100).iterrows():
            self.movements_tree.insert(
                "",
                "end",
                values=(
                    row["movimiento_id"],
                    pd.to_datetime(row["fecha"]).strftime("%Y-%m-%d"),
                    row["producto_id"],
                    row["tipo"],
                    int(row["cantidad"]),
                    int(row["existencia_final"]),
                    row["nota"],
                ),
            )

    def refresh_product_combos(self) -> None:
        options = self._product_options()
        self.sale_product_combo["values"] = options
        self.inventory_product_combo["values"] = options
        if options:
            if not self.sale_product_var.get():
                self.sale_product_var.set(options[0])
            if not self.inventory_product_var.get():
                self.inventory_product_var.set(options[0])
        self.update_inventory_label()

    def add_product(self) -> None:
        try:
            product_id = self.data_manager.add_product(self._product_form_data())
            messagebox.showinfo("Producto agregado", f"Se agrego el producto {product_id}.")
            self.clear_product_form()
            self.refresh_all()
        except Exception as exc:  # noqa: BLE001 - mensaje amigable para la interfaz
            messagebox.showerror("Error", str(exc))

    def update_product(self) -> None:
        if not self.selected_product_id:
            messagebox.showwarning("Seleccion requerida", "Selecciona un producto de la tabla.")
            return
        try:
            self.data_manager.update_product(self.selected_product_id, self._product_form_data())
            messagebox.showinfo("Cambios guardados", "El producto fue actualizado.")
            self.refresh_all()
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Error", str(exc))

    def clear_product_form(self) -> None:
        self.selected_product_id = None
        for entry in self.product_entries.values():
            entry.delete(0, tk.END)

    def register_sale(self) -> None:
        try:
            product_id = self._product_id_from_option(self.sale_product_var.get())
            quantity = int(self.sale_quantity_var.get())
            price = self.sale_price_var.get().strip()
            price_value = float(price) if price else None
            sale_id = self.data_manager.register_sale(
                product_id=product_id,
                quantity=quantity,
                sale_date=self.sale_date_var.get(),
                price_unit=price_value,
            )
            messagebox.showinfo("Venta registrada", f"Se registro la venta {sale_id}.")
            self.sale_quantity_var.set("")
            self.sale_price_var.set("")
            self.refresh_all()
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Error", str(exc))

    def set_inventory(self) -> None:
        try:
            product_id = self._product_id_from_option(self.inventory_product_var.get())
            new_stock = int(self.inventory_new_stock_var.get())
            self.data_manager.set_inventory(
                product_id=product_id,
                new_stock=new_stock,
                note=self.inventory_note_var.get(),
            )
            messagebox.showinfo("Inventario actualizado", "El inventario fue actualizado.")
            self.inventory_new_stock_var.set("")
            self.refresh_all()
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Error", str(exc))

    def run_optimization(self) -> None:
        try:
            budget = float(self.budget_var.get())
            products = self.data_manager.load_products()
            sales = self.data_manager.load_sales()
            metrics = product_metrics(products, sales)
            if metrics.empty or not metrics["comprar"].any():
                messagebox.showinfo("Sin compra sugerida", "No hay productos con necesidad de reabastecimiento.")
                return

            optimizer = TabuSearchOptimizer(
                metrics=metrics,
                budget=budget,
                tabu_tenure=int(self.tenure_var.get()),
                max_iterations=int(self.iterations_var.get()),
                max_no_improve=int(self.no_improve_var.get()),
            )
            result = optimizer.run()
            order_id = self.data_manager.save_order_suggestion(result.result_table)
            plot_path = save_optimization_plots(result.history, result.result_table, budget)

            self._fill_result_table(result.result_table)
            summary = summarize_order(result.result_table)
            self.optimization_summary.configure(
                text=(
                    f"Pedido {order_id} | Costo: ${summary['costo_total']:.2f} | "
                    f"Utilidad esperada: ${summary['utilidad_esperada']:.2f} | "
                    f"Productos: {summary['productos_pedidos']} | Grafica: {plot_path.name}"
                )
            )
            self._draw_optimization_figure(result.history, result.result_table, budget)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Error", str(exc))

    def update_inventory_label(self) -> None:
        try:
            product_id = self._product_id_from_option(self.inventory_product_var.get())
            products = self.data_manager.load_products(include_inactive=True)
            row = products[products["producto_id"] == product_id].iloc[0]
            self.inventory_current_label.configure(
                text=f"Inventario actual: {int(row['inventario_actual'])} piezas"
            )
        except Exception:
            self.inventory_current_label.configure(text="Inventario actual: -")

    def _on_product_selected(self, _event) -> None:
        selected = self.products_tree.selection()
        if not selected:
            return
        values = self.products_tree.item(selected[0], "values")
        product_id = values[0]
        products = self.data_manager.load_products(include_inactive=True)
        product = products[products["producto_id"] == product_id].iloc[0]
        self.selected_product_id = product_id
        for key, entry in self.product_entries.items():
            entry.delete(0, tk.END)
            entry.insert(0, str(product[key]))

    def _product_form_data(self) -> dict[str, str]:
        return {key: entry.get() for key, entry in self.product_entries.items()}

    def _product_options(self) -> list[str]:
        products = self.data_manager.load_products()
        return [f"{row['producto_id']} - {row['nombre']}" for _, row in products.iterrows()]

    @staticmethod
    def _product_id_from_option(option: str) -> str:
        if not option:
            raise ValueError("Selecciona un producto.")
        return option.split(" - ", 1)[0]

    def _fill_result_table(self, result_df: pd.DataFrame) -> None:
        self.result_tree.delete(*self.result_tree.get_children())
        for _, row in result_df.iterrows():
            if int(row["cajas"]) <= 0:
                continue
            self.result_tree.insert(
                "",
                "end",
                values=(
                    row["producto_id"],
                    row["nombre"],
                    row["rotacion"],
                    int(row["necesidad_piezas"]),
                    int(row["cajas"]),
                    f"{float(row['costo_total']):.2f}",
                    f"{float(row['utilidad_esperada']):.2f}",
                ),
            )

    def _draw_optimization_figure(self, history: pd.DataFrame, result_df: pd.DataFrame, budget: float) -> None:
        for child in self.graph_frame.winfo_children():
            child.destroy()
        figure = create_optimization_figure(history, result_df, budget)
        self.optimization_canvas = FigureCanvasTkAgg(figure, master=self.graph_frame)
        self.optimization_canvas.draw()
        self.optimization_canvas.get_tk_widget().pack(fill="both", expand=True)


def run_app() -> None:
    app = InventoryApp()
    app.mainloop()

