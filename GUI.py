"""
ecommerce_app.py

A simple e-commerce GUI using Tkinter:
 - Product catalog with search and category filter
 - Product detail popup
 - Add-to-cart, edit quantities, remove items
 - Checkout form saving orders to a local SQLite DB
 - Clean, modular code suitable for extension

Author: ChatGPT (example)
"""
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from decimal import Decimal, ROUND_HALF_UP

# ---------- Sample product data ----------
SAMPLE_PRODUCTS = [
    {"id": 1, "name": "Classic White T-Shirt", "category": "Clothing", "price": 19.99, "stock": 25, "desc": "100% cotton, comfortable everyday tee."},
    {"id": 2, "name": "Wireless Headphones", "category": "Electronics", "price": 89.50, "stock": 10, "desc": "Over-ear, 20hr battery life, noise cancellation."},
    {"id": 3, "name": "Stainless Water Bottle 1L", "category": "Home", "price": 24.00, "stock": 40, "desc": "Keeps drinks hot or cold for hours."},
    {"id": 4, "name": "Running Shoes", "category": "Footwear", "price": 120.00, "stock": 8, "desc": "Lightweight, breathable, great for daily runs."},
    {"id": 5, "name": "Bluetooth Speaker", "category": "Electronics", "price": 45.25, "stock": 15, "desc": "Portable, splash resistant, rich bass."},
    {"id": 6, "name": "Canvas Tote Bag", "category": "Accessories", "price": 12.75, "stock": 50, "desc": "Durable bag for shopping and everyday use."},
]

# ---------- Utilities ----------
def fmt_price(p):
    """Format price as 2-decimal string (rounding half up)."""
    return f"${Decimal(p).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)}"

# ---------- Simple persistence (SQLite) ----------
DB_FILE = "orders.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT NOT NULL,
        email TEXT NOT NULL,
        address TEXT NOT NULL,
        total REAL NOT NULL,
        details TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

def save_order(customer_name, email, address, total, details):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO orders (customer_name, email, address, total, details) VALUES (?, ?, ?, ?, ?)",
              (customer_name, email, address, float(total), details))
    conn.commit()
    conn.close()

# ---------- Core App ----------
class Product:
    def __init__(self, pid, name, category, price, stock, desc=""):
        self.id = pid
        self.name = name
        self.category = category
        self.price = Decimal(price)
        self.stock = stock
        self.desc = desc

class CartItem:
    def __init__(self, product: Product, qty=1):
        self.product = product
        self.qty = qty

    @property
    def line_total(self):
        return (self.product.price * self.qty).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

class StoreApp(tk.Tk):
    def __init__(self, products_data):
        super().__init__()
        self.title("Simple E-Commerce GUI")
        self.geometry("980x620")
        self.minsize(860, 520)
        self.products = [Product(**p) for p in products_data]
        self.cart = {}  # product.id -> CartItem
        self._build_ui()

    def _build_ui(self):
        # Top frame: search + categories + cart button
        top = ttk.Frame(self, padding=(10, 8))
        top.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(top, text="Search:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(top, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=(6, 12))
        search_entry.bind("<Return>", lambda e: self.refresh_products())

        ttk.Button(top, text="Search", command=self.refresh_products).pack(side=tk.LEFT)

        ttk.Label(top, text="   Category:").pack(side=tk.LEFT, padx=(12,0))
        categories = ["All"] + sorted({p.category for p in self.products})
        self.category_var = tk.StringVar(value="All")
        cat_menu = ttk.OptionMenu(top, self.category_var, "All", *categories, command=lambda _: self.refresh_products())
        cat_menu.pack(side=tk.LEFT, padx=(6, 6))

        # Spacer
        spacer = ttk.Frame(top)
        spacer.pack(side=tk.LEFT, expand=True)

        # Cart summary / button
        self.cart_btn = ttk.Button(top, text="Cart (0) - View", command=self.open_cart_window)
        self.cart_btn.pack(side=tk.RIGHT)

        # Main content: left product list, right product detail placeholder
        content = ttk.Frame(self, padding=(10,6))
        content.pack(fill=tk.BOTH, expand=True)

        # Left: product listing with a scrollable canvas
        left = ttk.Frame(content)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._create_product_list(left)

        # Right: quick cart summary + featured/selected product detail
        right = ttk.Frame(content, width=300)
        right.pack(side=tk.RIGHT, fill=tk.Y, padx=(10,0))
        right.pack_propagate(False)

        ttk.Label(right, text="Quick Cart Summary", font=("Segoe UI", 11, "bold")).pack(pady=(6,4))
        self.quick_cart_frame = ttk.Frame(right)
        self.quick_cart_frame.pack(fill=tk.X, padx=6)
        self._refresh_quick_cart()

        ttk.Separator(right).pack(fill=tk.X, pady=(10,10))
        ttk.Label(right, text="Selected Product", font=("Segoe UI", 11, "bold")).pack(pady=(4,4))
        self.selected_frame = ttk.Frame(right)
        self.selected_frame.pack(fill=tk.BOTH, expand=True, padx=6)
        self._render_selected_empty()

        # Initialize product view
        self.refresh_products()

    # ---------- product list with scrollbar ----------
    def _create_product_list(self, parent):
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        self.product_list_frame = ttk.Frame(canvas)

        self.product_list_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0,0), window=self.product_list_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # ---------- helpers to display products ----------
    def refresh_products(self):
        # Clear current list
        for w in self.product_list_frame.winfo_children():
            w.destroy()

        q = self.search_var.get().strip().lower()
        cat = self.category_var.get()

        matches = []
        for p in self.products:
            if cat != "All" and p.category != cat:
                continue
            if q and (q not in p.name.lower() and q not in p.desc.lower()):
                continue
            matches.append(p)

        if not matches:
            ttk.Label(self.product_list_frame, text="No products found.", padding=12).pack()
            return

        for p in matches:
            self._render_product_card(self.product_list_frame, p)

    def _render_product_card(self, frame, product: Product):
        card = ttk.Frame(frame, padding=10, relief="ridge")
        card.pack(fill=tk.X, pady=6, padx=6)

        # Header: name + price
        header = ttk.Frame(card)
        header.pack(fill=tk.X)
        ttk.Label(header, text=product.name, font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        ttk.Label(header, text=fmt_price(product.price), font=("Segoe UI", 10)).pack(side=tk.RIGHT)

        # Sub info: category, stock
        sub = ttk.Frame(card)
        sub.pack(fill=tk.X, pady=(6,0))
        ttk.Label(sub, text=f"Category: {product.category}").pack(side=tk.LEFT)
        ttk.Label(sub, text=f"Stock: {product.stock}").pack(side=tk.RIGHT)

        # Description
        ttk.Label(card, text=product.desc, wraplength=640, foreground="#444").pack(pady=(6,8))

        # Actions
        actions = ttk.Frame(card)
        actions.pack(fill=tk.X)
        ttk.Button(actions, text="View", command=lambda p=product: self.open_product_detail(p)).pack(side=tk.LEFT)
        ttk.Button(actions, text="Add to Cart", command=lambda p=product: self.add_to_cart(p, 1)).pack(side=tk.LEFT, padx=(6,0))

    # ---------- selected area ----------
    def _render_selected_empty(self):
        for w in self.selected_frame.winfo_children():
            w.destroy()
        ttk.Label(self.selected_frame, text="No product selected.\nClick 'View' on any product.", justify=tk.CENTER).pack(expand=True)

    def open_product_detail(self, product: Product):
        # Update selected panel
        for w in self.selected_frame.winfo_children():
            w.destroy()

        ttk.Label(self.selected_frame, text=product.name, font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(6,4))
        ttk.Label(self.selected_frame, text=f"Category: {product.category}").pack(anchor="w")
        ttk.Label(self.selected_frame, text=f"Price: {fmt_price(product.price)}").pack(anchor="w", pady=(4,0))
        ttk.Label(self.selected_frame, text=f"Stock: {product.stock}").pack(anchor="w", pady=(2,8))
        ttk.Label(self.selected_frame, text=product.desc, wraplength=260, foreground="#333").pack(anchor="w", pady=(6,8))

        qty_frame = ttk.Frame(self.selected_frame)
        qty_frame.pack(anchor="w", pady=(6,6))
        ttk.Label(qty_frame, text="Qty:").pack(side=tk.LEFT)
        qty_var = tk.IntVar(value=1)
        qty_spin = ttk.Spinbox(qty_frame, from_=1, to=max(1, product.stock), textvariable=qty_var, width=5)
        qty_spin.pack(side=tk.LEFT, padx=(6,10))

        btns = ttk.Frame(self.selected_frame)
        btns.pack(anchor="w", pady=(6,6))
        ttk.Button(btns, text="Add to Cart", command=lambda: (self.add_to_cart(product, qty_var.get()), messagebox.showinfo("Added", f"Added {qty_var.get()} × {product.name} to cart"))).pack(side=tk.LEFT)
        ttk.Button(btns, text="Open Detail Window", command=lambda p=product: self.open_product_popup(p)).pack(side=tk.LEFT, padx=(6,0))

    def open_product_popup(self, product: Product):
        popup = tk.Toplevel(self)
        popup.title(product.name)
        popup.geometry("420x300")
        ttk.Label(popup, text=product.name, font=("Segoe UI", 12, "bold")).pack(pady=(8,6))
        ttk.Label(popup, text=f"Category: {product.category}").pack()
        ttk.Label(popup, text=f"Price: {fmt_price(product.price)}").pack()
        ttk.Label(popup, text=f"Stock: {product.stock}").pack(pady=(4,6))
        ttk.Label(popup, text=product.desc, wraplength=380).pack(pady=(6,12))
        qty_var = tk.IntVar(value=1)
        ttk.Label(popup, text="Quantity:").pack()
        ttk.Spinbox(popup, from_=1, to=max(1, product.stock), textvariable=qty_var, width=6).pack()
        ttk.Button(popup, text="Add to cart", command=lambda: (self.add_to_cart(product, qty_var.get()), popup.destroy(), messagebox.showinfo("Added", "Added to cart"))).pack(pady=(12,0))

    # ---------- cart management ----------
    def add_to_cart(self, product: Product, qty:int=1):
        qty = int(qty)
        if qty <= 0:
            return
        if product.stock < qty:
            messagebox.showwarning("Stock", "Not enough stock for that quantity.")
            return
        if product.id in self.cart:
            new_qty = self.cart[product.id].qty + qty
            if new_qty > product.stock:
                messagebox.showwarning("Stock", "Not enough stock to increase quantity.")
                return
            self.cart[product.id].qty = new_qty
        else:
            self.cart[product.id] = CartItem(product, qty)
        self._update_cart_button()
        self._refresh_quick_cart()

    def _update_cart_button(self):
        total_items = sum(item.qty for item in self.cart.values())
        self.cart_btn.config(text=f"Cart ({total_items}) - View")

    def _refresh_quick_cart(self):
        # Clear quick cart
        for w in self.quick_cart_frame.winfo_children():
            w.destroy()

        if not self.cart:
            ttk.Label(self.quick_cart_frame, text="Cart empty").pack()
            return

        for item in list(self.cart.values())[:5]:  # show up to 5 items
            row = ttk.Frame(self.quick_cart_frame)
            row.pack(fill=tk.X, pady=3)
            ttk.Label(row, text=f"{item.qty} × {item.product.name}", wraplength=170).pack(side=tk.LEFT)
            ttk.Label(row, text=fmt_price(item.line_total)).pack(side=tk.RIGHT)

        ttk.Button(self.quick_cart_frame, text="Open Cart", command=self.open_cart_window).pack(pady=(6,0))

    def open_cart_window(self):
        cart_win = tk.Toplevel(self)
        cart_win.title("Shopping Cart")
        cart_win.geometry("640x420")

        # Header
        header = ttk.Frame(cart_win, padding=8)
        header.pack(fill=tk.X)
        ttk.Label(header, text="Your Cart", font=("Segoe UI", 12, "bold")).pack(side=tk.LEFT)

        # Cart list
        body = ttk.Frame(cart_win, padding=(8,4))
        body.pack(fill=tk.BOTH, expand=True)

        if not self.cart:
            ttk.Label(body, text="Your cart is empty.").pack()
            return

        # Treeview for cart
        columns = ("name", "price", "qty", "total")
        tree = ttk.Treeview(body, columns=columns, show="headings", selectmode="browse")
        tree.heading("name", text="Product")
        tree.heading("price", text="Unit Price")
        tree.heading("qty", text="Qty")
        tree.heading("total", text="Line Total")
        tree.column("name", width=280)
        tree.column("price", width=100, anchor=tk.E)
        tree.column("qty", width=60, anchor=tk.CENTER)
        tree.column("total", width=100, anchor=tk.E)
        tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        # Insert items
        for item in self.cart.values():
            tree.insert("", "end", iid=str(item.product.id),
                        values=(item.product.name, fmt_price(item.product.price), item.qty, fmt_price(item.line_total)))

        # Controls to change quantity / remove
        ctrl = ttk.Frame(body, padding=8)
        ctrl.pack(side=tk.RIGHT, fill=tk.Y)
        ttk.Label(ctrl, text="Selected item actions").pack(pady=(0,6))
        qty_var = tk.IntVar(value=1)
        ttk.Label(ctrl, text="Qty:").pack()
        qty_spin = ttk.Spinbox(ctrl, from_=1, to=99, textvariable=qty_var, width=6)
        qty_spin.pack(pady=(0,6))

        def on_select_update(event=None):
            sel = tree.selection()
            if not sel:
                return
            pid = int(sel[0])
            qty_var.set(self.cart[pid].qty)

        def update_qty():
            sel = tree.selection()
            if not sel:
                messagebox.showinfo("Select", "Select an item in the cart to update quantity.")
                return
            pid = int(sel[0])
            newq = int(qty_var.get())
            prod = self.cart[pid].product
            if newq > prod.stock:
                messagebox.showwarning("Stock", "Not enough stock for that quantity.")
                return
            self.cart[pid].qty = newq
            tree.item(str(pid), values=(prod.name, fmt_price(prod.price), newq, fmt_price(self.cart[pid].line_total)))
            self._update_cart_button()
            self._refresh_quick_cart()

        def remove_item():
            sel = tree.selection()
            if not sel:
                messagebox.showinfo("Select", "Select an item to remove.")
                return
            pid = int(sel[0])
            del self.cart[pid]
            tree.delete(str(pid))
            self._update_cart_button()
            self._refresh_quick_cart()
            if not self.cart:
                cart_win.destroy()

        tree.bind("<<TreeviewSelect>>", on_select_update(None))
        ttk.Button(ctrl, text="Update Qty", command=update_qty).pack(pady=(6,0))
        ttk.Button(ctrl, text="Remove Item", command=remove_item).pack(pady=(6,0))

        # Bottom: totals and checkout
        bottom = ttk.Frame(cart_win, padding=8)
        bottom.pack(fill=tk.X)
        subtotal = sum(item.line_total for item in self.cart.values())
        ttk.Label(bottom, text=f"Subtotal: {fmt_price(subtotal)}", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)

        ttk.Button(bottom, text="Checkout", command=lambda: (cart_win.destroy(), self.open_checkout_window())).pack(side=tk.RIGHT)

    # ---------- checkout ----------
    def open_checkout_window(self):
        if not self.cart:
            messagebox.showinfo("Empty", "Your cart is empty.")
            return
        win = tk.Toplevel(self)
        win.title("Checkout")
        win.geometry("520x420")

        ttk.Label(win, text="Checkout", font=("Segoe UI", 12, "bold")).pack(pady=(8,6))
        form = ttk.Frame(win, padding=12)
        form.pack(fill=tk.BOTH, expand=True)

        ttk.Label(form, text="Full Name:").grid(row=0, column=0, sticky="w", pady=4)
        name_var = tk.StringVar()
        ttk.Entry(form, textvariable=name_var).grid(row=0, column=1, sticky="ew", pady=4)

        ttk.Label(form, text="Email:").grid(row=1, column=0, sticky="w", pady=4)
        email_var = tk.StringVar()
        ttk.Entry(form, textvariable=email_var).grid(row=1, column=1, sticky="ew", pady=4)

        ttk.Label(form, text="Shipping Address:").grid(row=2, column=0, sticky="nw", pady=4)
        address_txt = tk.Text(form, height=5, width=40)
        address_txt.grid(row=2, column=1, sticky="ew", pady=4)

        form.columnconfigure(1, weight=1)

        subtotal = sum(item.line_total for item in self.cart.values())
        ttk.Label(form, text=f"Order total: {fmt_price(subtotal)}", font=("Segoe UI", 10, "bold")).grid(row=3, column=1, sticky="e", pady=(8,12))

        def place_order():
            name = name_var.get().strip()
            email = email_var.get().strip()
            address = address_txt.get("1.0", tk.END).strip()
            if not name or not email or not address:
                messagebox.showwarning("Missing", "Please complete all fields.")
                return
            # Save order (mock)
            details_lines = []
            for item in self.cart.values():
                details_lines.append(f"{item.qty}x {item.product.name} @ {fmt_price(item.product.price)} = {fmt_price(item.line_total)}")
            details = "\n".join(details_lines)
            save_order(name, email, address, float(subtotal), details)
            messagebox.showinfo("Order placed", f"Thanks {name}! Your order has been placed.")
            # reduce stock locally
            for item in list(self.cart.values()):
                item.product.stock -= item.qty
            self.cart.clear()
            self._update_cart_button()
            self._refresh_quick_cart()
            self.refresh_products()
            win.destroy()

        ttk.Button(form, text="Place Order", command=place_order).grid(row=4, column=1, sticky="e", pady=(8,0))

# ---------- Boot ----------
def main():
    init_db()
    app = StoreApp(SAMPLE_PRODUCTS)
    app.mainloop()

if __name__ == "__main__":
    main()
