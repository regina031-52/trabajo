"""Interfaz facil y visual para la aplicacion.

Esta pantalla usa la misma logica del proyecto, pero organiza las acciones en
un menu lateral con textos claros. La idea es que una persona que no programa
pueda usar la app sin tener que entender todos los archivos internos.
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


BG = "#f6f1ff"
PANEL = "#ffffff"
PURPLE = "#7b2cbf"
DARK = "#2f2440"
MUTED = "#6f6580"
GREEN = "#2a9d8f"
ORANGE = "#f4a261"


class EasyInventoryApp(tk.Tk):
    """Aplicacion con flujo simplificado para inventario y pedidos."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Pedidos de belleza con Busqueda Tabu")
        self.geometry("1180x740")
        self.minsize(1020, 650)
        self.configure(bg=BG)

        self.data_manager = DataManager()
        self.selected_product_id: str | None = None
        self.current_chart: FigureCanvasTkAgg | None = None

        self._build_style()
        self._build_shell()
        self.show_home()

    def _build_style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background=BG)
        style.configure("Panel.TFrame", background=PANEL)
        style.configure("Sidebar.TFrame", background=PURPLE)
        style.configure("TLabel", background=BG, foreground=DARK, font=("Segoe UI", 10))
        style.configure("Panel.TLabel", background=PANEL, foreground=DARK, font=("Segoe UI", 10))
        style.configure("Title.TLabel", background=BG, foreground=DARK, font=("Segoe UI", 22, "bold"))
        style.configure("Section.TLabel", background=PANEL, foreground=DARK, font=("Segoe UI", 15, "bold"))
        style.configure("Muted.TLabel", background=PANEL, foreground=MUTED, font=("Segoe UI", 10))
        style.configure("CardTitle.TLabel", background=PANEL, foreground=PURPLE, font=("Segoe UI", 13, "bold"))
        style.configure("CardValue.TLabel", background=PANEL, foreground=DARK, font=("Segoe UI", 22, "bold"))
        style.configure("TButton", padding=8, font=("Segoe UI", 10))
        style.configure("Accent.TButton", background=PURPLE, foreground="#ffffff", font=("Segoe UI", 10, "bold"))
        style.map("Accent.TButton", background=[("active", "#5a189a")])
        style.configure("Treeview", rowheight=28, font=("Segoe UI", 9), background="#ffffff")
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))

    def _build_shell(self) -> None:
        self.sidebar = ttk.Frame(self, style="Sidebar.TFrame", padding=(14, 18))
        self.sidebar.pack(side="left", fill="y")

        tk.Label(
            self.sidebar,
            text="Beauty\nTabu",
            bg=PURPLE,
            fg="white",
            font=("Segoe UI", 20, "bold"),
            justify="left",
        ).pack(anchor="w", pady=(0, 24))

        self._nav_button("Inicio", self.show_home)
        self._nav_button("Productos", self.show_products)
        self._nav_button("Ventas", self.show_sales)
        self._nav_button("Inventario", self.show_inventory)
        self._nav_button("Optimizar pedido", self.show_optimization)

        tk.Label(
            self.sidebar,
            text="Los datos se guardan\nautomaticamente en CSV.",
            bg=PURPLE,
            fg="#e9d8fd",
            font=("Segoe UI", 9),
            justify="left",
        ).pack(side="bottom", anchor="w", pady=(20, 0))

        self.main = ttk.Frame(self, padding=22)
        self.main.pack(side="left", fill="both", expand=True)

    def _nav_button(self, text: str, command) -> None:
        button = tk.Button(
            self.sidebar,
            text=text,
            command=command,
            bg="#9d4edd",
            fg="white",
            activebackground="#c77dff",
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=14,
            pady=10,
            anchor="w",
            font=("Segoe UI", 10, "bold"),
            cursor="hand2",
            width=18,
        )
        button.pack(fill="x", pady=5)

    def _clear_main(self) -> None:
        if self.current_chart is not None:
            self.current_chart.get_tk_widget().destroy()
            self.current_chart = None
        for child in self.main.winfo_children():
            child.destroy()

    def show_home(self) -> None:
        self._clear_main()
        ttk.Label(self.main, text="Panel principal", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            self.main,
            text="Usa el menu de la izquierda para registrar datos y ejecutar la optimizacion.",
            foreground=MUTED,
        ).pack(anchor="w", pady=(0, 18))

        cards = ttk.Frame(self.main)
        cards.pack(fill="x")
        summary = self._business_summary()
        self._summary_card(cards, "Productos", str(summary["productos"]), "Catalogo registrado", 0)
        self._summary_card(cards, "Inventario", str(summary["inventario"]), "Piezas disponibles", 1)
        self._summary_card(cards, "Ventas", str(summary["ventas"]), "Ventas historicas", 2)
        self._summary_card(cards, "Utilidad media", f"${summary['margen_promedio']:.2f}", "Por pieza", 3)

        guide = ttk.Frame(self.main, style="Panel.TFrame", padding=18)
        guide.pack(fill="both", expand=True, pady=18)
        ttk.Label(guide, text="Flujo recomendado", style="Section.TLabel").pack(anchor="w")
        steps = [
            "1. Agrega productos con costo, precio, inventario y piezas por caja.",
            "2. Registra ventas diarias para que el sistema estime la demanda mensual.",
            "3. Ajusta inventario cuando hagas conteo fisico.",
            "4. Escribe tu presupuesto y ejecuta la Busqueda Tabu.",
        ]
        for step in steps:
            ttk.Label(guide, text=step, style="Panel.TLabel").pack(anchor="w", pady=5)

        ttk.Button(
            guide,
            text="Empezar optimizacion",
            style="Accent.TButton",
            command=self.show_optimization,
        ).pack(anchor="w", pady=(18, 0))

    def _summary_card(self, parent: ttk.Frame, title: str, value: str, subtitle: str, column: int) -> None:
        parent.columnconfigure(column, weight=1)
        card = ttk.Frame(parent, style="Panel.TFrame", padding=16)
        card.grid(row=0, column=column, sticky="nsew", padx=6)
        ttk.Label(card, text=title, style="CardTitle.TLabel").pack(anchor="w")
        ttk.Label(card, text=value, style="CardValue.TLabel").pack(anchor="w", pady=(6, 0))
        ttk.Label(card, text=subtitle, style="Muted.TLabel").pack(anchor="w")

    def show_products(self) -> None:
        self._clear_main()
        self.selected_product_id = None
        ttk.Label(self.main, text="Productos", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            self.main,
            text="Registra los productos que compras por caja.",
            foreground=MUTED,
        ).pack(anchor="w", pady=(0, 14))

        body = ttk.Frame(self.main)
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)

        form = ttk.Frame(body, style="Panel.TFrame", padding=16)
        form.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        ttk.Label(form, text="Datos del producto", style="Section.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 8)
        )

        self.product_vars = {
            "nombre": tk.StringVar(),
            "categoria": tk.StringVar(value="Tintes"),
            "piezas_por_caja": tk.StringVar(value="12"),
            "costo_pieza": tk.StringVar(value="0"),
            "precio_venta_pieza": tk.StringVar(value="0"),
            "inventario_actual": tk.StringVar(value="0"),
            "inventario_minimo": tk.StringVar(value="0"),
            "stock_objetivo": tk.StringVar(value="0"),
            "cajas_maximas": tk.StringVar(value="5"),
        }
        labels = {
            "nombre": "Nombre",
            "categoria": "Categoria",
            "piezas_por_caja": "Piezas por caja",
            "costo_pieza": "Costo por pieza",
            "precio_venta_pieza": "Precio venta",
            "inventario_actual": "Inventario actual",
            "inventario_minimo": "Inventario minimo",
            "stock_objetivo": "Stock objetivo",
            "cajas_maximas": "Maximo de cajas",
        }
        for row, (key, var) in enumerate(self.product_vars.items(), start=1):
            ttk.Label(form, text=labels[key], style="Panel.TLabel").grid(row=row, column=0, sticky="w", pady=4)
            ttk.Entry(form, textvariable=var).grid(row=row, column=1, sticky="ew", pady=4, padx=(8, 0))
        form.columnconfigure(1, weight=1)

        ttk.Button(form, text="Guardar producto", style="Accent.TButton", command=self.save_product).grid(
            row=11, column=0, columnspan=2, sticky="ew", pady=(14, 4)
        )
        ttk.Button(form, text="Limpiar formulario", command=self.clear_product_form).grid(
            row=12, column=0, columnspan=2, sticky="ew"
        )

        table_panel = ttk.Frame(body, style="Panel.TFrame", padding=10)
        table_panel.grid(row=0, column=1, sticky="nsew")
        columns = (
            "producto_id",
            "nombre",
            "categoria",
            "piezas_por_caja",
            "costo_pieza",
            "precio_venta_pieza",
            "inventario_actual",
        )
        self.products_tree = self._tree(table_panel, columns)
        headings = {
            "producto_id": "ID",
            "nombre": "Producto",
            "categoria": "Categoria",
            "piezas_por_caja": "Caja",
            "costo_pieza": "Costo",
            "precio_venta_pieza": "Precio",
            "inventario_actual": "Stock",
        }
        for column in columns:
            self.products_tree.heading(column, text=headings[column])
            self.products_tree.column(column, width=110, anchor="center")
        self.products_tree.column("nombre", width=190, anchor="w")
        self.products_tree.bind("<<TreeviewSelect>>", self.on_product_selected)
        self.refresh_products_table()

    def show_sales(self) -> None:
        self._clear_main()
        ttk.Label(self.main, text="Ventas diarias", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            self.main,
            text="Cada venta descuenta inventario y alimenta el historial de demanda.",
            foreground=MUTED,
        ).pack(anchor="w", pady=(0, 14))

        body = ttk.Frame(self.main)
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)

        form = ttk.Frame(body, style="Panel.TFrame", padding=16)
        form.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        ttk.Label(form, text="Registrar venta", style="Section.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 8)
        )

        self.sale_product = tk.StringVar()
        self.sale_date = tk.StringVar(value=date.today().isoformat())
        self.sale_quantity = tk.StringVar(value="1")
        self.sale_price = tk.StringVar()

        self.sale_combo = ttk.Combobox(form, textvariable=self.sale_product, state="readonly")
        sale_options = self._product_options()
        self.sale_combo["values"] = sale_options
        if sale_options:
            self.sale_product.set(sale_options[0])
        self.sale_combo.bind("<<ComboboxSelected>>", lambda _event: self.fill_sale_price())
        self._form_row(form, 1, "Producto", self.sale_combo)
        self._entry_row(form, 2, "Fecha", self.sale_date)
        self._entry_row(form, 3, "Cantidad", self.sale_quantity)
        self._entry_row(form, 4, "Precio unitario", self.sale_price)
        ttk.Button(form, text="Usar precio del producto", command=self.fill_sale_price).grid(
            row=5, column=0, columnspan=2, sticky="ew", pady=(12, 4)
        )
        ttk.Button(form, text="Guardar venta", style="Accent.TButton", command=self.save_sale).grid(
            row=6, column=0, columnspan=2, sticky="ew"
        )
        form.columnconfigure(1, weight=1)
        self.fill_sale_price()

        table_panel = ttk.Frame(body, style="Panel.TFrame", padding=10)
        table_panel.grid(row=0, column=1, sticky="nsew")
        columns = ("venta_id", "fecha", "producto_id", "cantidad", "precio_unitario")
        self.sales_tree = self._tree(table_panel, columns)
        for column, title in zip(columns, ["ID", "Fecha", "Producto", "Cantidad", "Precio"]):
            self.sales_tree.heading(column, text=title)
            self.sales_tree.column(column, width=120, anchor="center")
        self.refresh_sales_table()

    def show_inventory(self) -> None:
        self._clear_main()
        ttk.Label(self.main, text="Inventario", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            self.main,
            text="Actualiza existencias despues de conteos fisicos o ajustes.",
            foreground=MUTED,
        ).pack(anchor="w", pady=(0, 14))

        body = ttk.Frame(self.main)
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)

        form = ttk.Frame(body, style="Panel.TFrame", padding=16)
        form.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        ttk.Label(form, text="Ajuste de inventario", style="Section.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 8)
        )

        self.inventory_product = tk.StringVar()
        self.inventory_stock = tk.StringVar()
        self.inventory_note = tk.StringVar(value="Conteo fisico")
        self.inventory_combo = ttk.Combobox(form, textvariable=self.inventory_product, state="readonly")
        inventory_options = self._product_options()
        self.inventory_combo["values"] = inventory_options
        if inventory_options:
            self.inventory_product.set(inventory_options[0])
        self.inventory_combo.bind("<<ComboboxSelected>>", lambda _event: self.refresh_inventory_hint())
        self.inventory_hint = ttk.Label(form, text="Inventario actual: -", style="Muted.TLabel")

        self._form_row(form, 1, "Producto", self.inventory_combo)
        self.inventory_hint.grid(row=2, column=0, columnspan=2, sticky="w", pady=(2, 10))
        self._entry_row(form, 3, "Nuevo inventario", self.inventory_stock)
        self._entry_row(form, 4, "Nota", self.inventory_note)
        ttk.Button(form, text="Actualizar inventario", style="Accent.TButton", command=self.save_inventory).grid(
            row=5, column=0, columnspan=2, sticky="ew", pady=(12, 0)
        )
        form.columnconfigure(1, weight=1)
        self.refresh_inventory_hint()

        table_panel = ttk.Frame(body, style="Panel.TFrame", padding=10)
        table_panel.grid(row=0, column=1, sticky="nsew")
        columns = ("movimiento_id", "fecha", "producto_id", "tipo", "cantidad", "existencia_final")
        self.movements_tree = self._tree(table_panel, columns)
        for column, title in zip(columns, ["ID", "Fecha", "Producto", "Tipo", "Cambio", "Final"]):
            self.movements_tree.heading(column, text=title)
            self.movements_tree.column(column, width=110, anchor="center")
        self.refresh_movements_table()

    def show_optimization(self) -> None:
        self._clear_main()
        ttk.Label(self.main, text="Optimizar pedido", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            self.main,
            text="El sistema decide cuantas cajas pedir sin pasar el presupuesto.",
            foreground=MUTED,
        ).pack(anchor="w", pady=(0, 14))

        top = ttk.Frame(self.main, style="Panel.TFrame", padding=14)
        top.pack(fill="x")
        self.budget_var = tk.StringVar(value="5000")
        self.iter_var = tk.StringVar(value="250")
        ttk.Label(top, text="Presupuesto disponible", style="Panel.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Entry(top, textvariable=self.budget_var, width=14).grid(row=0, column=1, padx=8)
        ttk.Label(top, text="Iteraciones", style="Panel.TLabel").grid(row=0, column=2, sticky="w", padx=(18, 0))
        ttk.Entry(top, textvariable=self.iter_var, width=10).grid(row=0, column=3, padx=8)
        ttk.Button(top, text="Ejecutar Busqueda Tabu", style="Accent.TButton", command=self.run_optimization).grid(
            row=0, column=4, padx=(18, 0)
        )

        self.optimization_summary = ttk.Label(
            self.main,
            text="Aun no se ha ejecutado la optimizacion.",
            foreground=MUTED,
        )
        self.optimization_summary.pack(anchor="w", pady=10)

        bottom = ttk.Frame(self.main)
        bottom.pack(fill="both", expand=True)
        bottom.columnconfigure(0, weight=1)
        bottom.columnconfigure(1, weight=1)
        bottom.rowconfigure(0, weight=1)

        table_panel = ttk.Frame(bottom, style="Panel.TFrame", padding=10)
        table_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        columns = ("producto_id", "nombre", "rotacion", "cajas", "costo_total", "utilidad_esperada")
        self.result_tree = self._tree(table_panel, columns)
        for column, title in zip(columns, ["ID", "Producto", "Rotacion", "Cajas", "Costo", "Utilidad"]):
            self.result_tree.heading(column, text=title)
            self.result_tree.column(column, width=105, anchor="center")
        self.result_tree.column("nombre", width=180, anchor="w")

        self.chart_panel = ttk.Frame(bottom, style="Panel.TFrame", padding=10)
        self.chart_panel.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        ttk.Label(self.chart_panel, text="Aqui apareceran las graficas.", style="Muted.TLabel").pack(expand=True)

    def _form_row(self, parent: ttk.Frame, row: int, label: str, widget) -> None:
        ttk.Label(parent, text=label, style="Panel.TLabel").grid(row=row, column=0, sticky="w", pady=5)
        widget.grid(row=row, column=1, sticky="ew", pady=5, padx=(8, 0))

    def _entry_row(self, parent: ttk.Frame, row: int, label: str, variable: tk.StringVar) -> None:
        self._form_row(parent, row, label, ttk.Entry(parent, textvariable=variable))

    def _tree(self, parent: ttk.Frame, columns: tuple[str, ...]) -> ttk.Treeview:
        frame = ttk.Frame(parent, style="Panel.TFrame")
        frame.pack(fill="both", expand=True)
        tree = ttk.Treeview(frame, columns=columns, show="headings")
        yscroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        xscroll = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        return tree

    def save_product(self) -> None:
        try:
            data = {key: var.get() for key, var in self.product_vars.items()}
            data["activo"] = 1
            if self.selected_product_id:
                self.data_manager.update_product(self.selected_product_id, data)
                messagebox.showinfo("Producto guardado", "El producto fue actualizado.")
            else:
                product_id = self.data_manager.add_product(data)
                messagebox.showinfo("Producto guardado", f"Se agrego el producto {product_id}.")
            self.clear_product_form()
            self.refresh_products_table()
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Error", str(exc))

    def clear_product_form(self) -> None:
        self.selected_product_id = None
        defaults = {
            "nombre": "",
            "categoria": "Tintes",
            "piezas_por_caja": "12",
            "costo_pieza": "0",
            "precio_venta_pieza": "0",
            "inventario_actual": "0",
            "inventario_minimo": "0",
            "stock_objetivo": "0",
            "cajas_maximas": "5",
        }
        for key, value in defaults.items():
            self.product_vars[key].set(value)

    def on_product_selected(self, _event=None) -> None:
        selected = self.products_tree.selection()
        if not selected:
            return
        product_id = self.products_tree.item(selected[0], "values")[0]
        products = self.data_manager.load_products(include_inactive=True)
        product = products[products["producto_id"] == product_id].iloc[0]
        self.selected_product_id = product_id
        for key in self.product_vars:
            self.product_vars[key].set(str(product[key]))

    def save_sale(self) -> None:
        try:
            product_id = self._selected_product_id(self.sale_product.get())
            price = self.sale_price.get().strip()
            self.data_manager.register_sale(
                product_id=product_id,
                quantity=int(self.sale_quantity.get()),
                sale_date=self.sale_date.get(),
                price_unit=float(price) if price else None,
            )
            messagebox.showinfo("Venta guardada", "La venta fue registrada.")
            self.sale_quantity.set("1")
            self.fill_sale_price()
            self.refresh_sales_table()
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Error", str(exc))

    def fill_sale_price(self) -> None:
        try:
            product_id = self._selected_product_id(self.sale_product.get())
            products = self.data_manager.load_products()
            product = products[products["producto_id"] == product_id].iloc[0]
            self.sale_price.set(f"{float(product['precio_venta_pieza']):.2f}")
        except Exception:
            self.sale_price.set("")

    def save_inventory(self) -> None:
        try:
            product_id = self._selected_product_id(self.inventory_product.get())
            self.data_manager.set_inventory(
                product_id=product_id,
                new_stock=int(self.inventory_stock.get()),
                note=self.inventory_note.get(),
            )
            messagebox.showinfo("Inventario actualizado", "El inventario fue actualizado.")
            self.inventory_stock.set("")
            self.refresh_inventory_hint()
            self.refresh_movements_table()
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Error", str(exc))

    def refresh_inventory_hint(self) -> None:
        try:
            product_id = self._selected_product_id(self.inventory_product.get())
            products = self.data_manager.load_products(include_inactive=True)
            product = products[products["producto_id"] == product_id].iloc[0]
            self.inventory_hint.configure(text=f"Inventario actual: {int(product['inventario_actual'])} piezas")
        except Exception:
            self.inventory_hint.configure(text="Inventario actual: -")

    def run_optimization(self) -> None:
        try:
            budget = float(self.budget_var.get())
            products = self.data_manager.load_products()
            sales = self.data_manager.load_sales()
            metrics = product_metrics(products, sales)
            optimizer = TabuSearchOptimizer(
                metrics=metrics,
                budget=budget,
                max_iterations=int(self.iter_var.get()),
            )
            result = optimizer.run()
            order_id = self.data_manager.save_order_suggestion(result.result_table)
            plot_path = save_optimization_plots(result.history, result.result_table, budget)
            summary = summarize_order(result.result_table)

            self.result_tree.delete(*self.result_tree.get_children())
            for _, row in result.result_table[result.result_table["cajas"] > 0].iterrows():
                self.result_tree.insert(
                    "",
                    "end",
                    values=(
                        row["producto_id"],
                        row["nombre"],
                        row["rotacion"],
                        int(row["cajas"]),
                        f"${float(row['costo_total']):.2f}",
                        f"${float(row['utilidad_esperada']):.2f}",
                    ),
                )

            self.optimization_summary.configure(
                text=(
                    f"Pedido {order_id}: costo ${summary['costo_total']:.2f}, "
                    f"utilidad esperada ${summary['utilidad_esperada']:.2f}. "
                    f"Grafica guardada en {plot_path.name}."
                )
            )
            self._draw_chart(result.history, result.result_table, budget)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Error", str(exc))

    def _draw_chart(self, history: pd.DataFrame, result_df: pd.DataFrame, budget: float) -> None:
        for child in self.chart_panel.winfo_children():
            child.destroy()
        figure = create_optimization_figure(history, result_df, budget)
        self.current_chart = FigureCanvasTkAgg(figure, master=self.chart_panel)
        self.current_chart.draw()
        self.current_chart.get_tk_widget().pack(fill="both", expand=True)

    def refresh_products_table(self) -> None:
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
                ),
            )

    def refresh_sales_table(self) -> None:
        self.sales_tree.delete(*self.sales_tree.get_children())
        sales = self.data_manager.load_sales().sort_values("fecha", ascending=False)
        for _, row in sales.head(150).iterrows():
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

    def refresh_movements_table(self) -> None:
        self.movements_tree.delete(*self.movements_tree.get_children())
        movements = self.data_manager.load_movements().sort_values("fecha", ascending=False)
        for _, row in movements.head(150).iterrows():
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
                ),
            )

    def _business_summary(self) -> dict[str, float]:
        products = self.data_manager.load_products()
        sales = self.data_manager.load_sales()
        if products.empty:
            margin = 0.0
            stock = 0
        else:
            margin = float((products["precio_venta_pieza"] - products["costo_pieza"]).mean())
            stock = int(products["inventario_actual"].sum())
        return {
            "productos": int(len(products)),
            "inventario": stock,
            "ventas": int(len(sales)),
            "margen_promedio": margin,
        }

    def _product_options(self) -> list[str]:
        products = self.data_manager.load_products()
        return [f"{row['producto_id']} - {row['nombre']}" for _, row in products.iterrows()]

    @staticmethod
    def _selected_product_id(option: str) -> str:
        if not option:
            raise ValueError("Selecciona un producto.")
        return option.split(" - ", 1)[0]


def run_easy_app() -> None:
    app = EasyInventoryApp()
    app.mainloop()


if __name__ == "__main__":
    run_easy_app()
