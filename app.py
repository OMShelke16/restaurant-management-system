"""
app.py
Restaurant Management System — Flask web application.

Run with:
    python3 app.py
Then open http://127.0.0.1:5000 in your browser.
"""

import datetime
from flask import Flask, render_template, request, redirect, url_for, flash

from database import get_db, init_db, seed_demo_data, TAX_RATE

app = Flask(__name__)
app.secret_key = "dev-secret-key-change-in-production"


def now_str():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# --------------------------------------------------------------------------
# Dashboard
# --------------------------------------------------------------------------
@app.route("/")
def dashboard():
    db = get_db()
    today = datetime.date.today().isoformat()

    open_orders = db.execute(
        "SELECT COUNT(*) FROM orders WHERE status='open'"
    ).fetchone()[0]
    free_tables = db.execute(
        "SELECT COUNT(*) FROM tables WHERE status='free'"
    ).fetchone()[0]
    total_tables = db.execute("SELECT COUNT(*) FROM tables").fetchone()[0]
    today_revenue = db.execute(
        "SELECT COALESCE(SUM(total), 0) FROM bills WHERE created_at LIKE ?",
        (today + "%",),
    ).fetchone()[0]
    today_bills = db.execute(
        "SELECT COUNT(*) FROM bills WHERE created_at LIKE ?", (today + "%",)
    ).fetchone()[0]
    menu_items = db.execute("SELECT COUNT(*) FROM menu").fetchone()[0]

    top_items = db.execute("""
        SELECT m.name, SUM(oi.quantity) as qty
        FROM order_items oi JOIN menu m ON oi.item_id = m.item_id
        GROUP BY m.name ORDER BY qty DESC LIMIT 5
    """).fetchall()

    recent_orders = db.execute("""
        SELECT o.order_id, t.label, o.status, o.created_at
        FROM orders o JOIN tables t ON o.table_id = t.table_id
        ORDER BY o.order_id DESC LIMIT 6
    """).fetchall()

    db.close()
    return render_template(
        "dashboard.html",
        open_orders=open_orders,
        free_tables=free_tables,
        total_tables=total_tables,
        today_revenue=today_revenue,
        today_bills=today_bills,
        menu_items=menu_items,
        top_items=top_items,
        recent_orders=recent_orders,
    )


# --------------------------------------------------------------------------
# Menu Management
# --------------------------------------------------------------------------
@app.route("/menu")
def menu():
    db = get_db()
    items = db.execute("SELECT * FROM menu ORDER BY category, name").fetchall()
    db.close()
    return render_template("menu.html", items=items)


@app.route("/menu/add", methods=["POST"])
def menu_add():
    name = request.form["name"].strip()
    category = request.form["category"].strip()
    price = float(request.form["price"])
    db = get_db()
    db.execute(
        "INSERT INTO menu (name, category, price, available) VALUES (?, ?, ?, 1)",
        (name, category, price),
    )
    db.commit()
    db.close()
    flash(f"'{name}' added to the menu.", "success")
    return redirect(url_for("menu"))


@app.route("/menu/edit/<int:item_id>", methods=["POST"])
def menu_edit(item_id):
    name = request.form["name"].strip()
    category = request.form["category"].strip()
    price = float(request.form["price"])
    db = get_db()
    db.execute(
        "UPDATE menu SET name=?, category=?, price=? WHERE item_id=?",
        (name, category, price, item_id),
    )
    db.commit()
    db.close()
    flash(f"'{name}' updated.", "success")
    return redirect(url_for("menu"))


@app.route("/menu/toggle/<int:item_id>", methods=["POST"])
def menu_toggle(item_id):
    db = get_db()
    row = db.execute("SELECT available, name FROM menu WHERE item_id=?", (item_id,)).fetchone()
    new_status = 0 if row["available"] else 1
    db.execute("UPDATE menu SET available=? WHERE item_id=?", (new_status, item_id))
    db.commit()
    db.close()
    state = "available" if new_status else "86'd (unavailable)"
    flash(f"'{row['name']}' is now {state}.", "info")
    return redirect(url_for("menu"))


@app.route("/menu/delete/<int:item_id>", methods=["POST"])
def menu_delete(item_id):
    db = get_db()
    row = db.execute("SELECT name FROM menu WHERE item_id=?", (item_id,)).fetchone()
    db.execute("DELETE FROM menu WHERE item_id=?", (item_id,))
    db.commit()
    db.close()
    if row:
        flash(f"'{row['name']}' removed from menu.", "warning")
    return redirect(url_for("menu"))


# --------------------------------------------------------------------------
# Table Management
# --------------------------------------------------------------------------
@app.route("/tables")
def tables():
    db = get_db()
    all_tables = db.execute("SELECT * FROM tables ORDER BY table_id").fetchall()
    db.close()
    return render_template("tables.html", tables=all_tables)


@app.route("/tables/add", methods=["POST"])
def tables_add():
    label = request.form["label"].strip()
    capacity = int(request.form["capacity"])
    db = get_db()
    db.execute("INSERT INTO tables (label, capacity) VALUES (?, ?)", (label, capacity))
    db.commit()
    db.close()
    flash(f"Table '{label}' added.", "success")
    return redirect(url_for("tables"))


@app.route("/tables/free/<int:table_id>", methods=["POST"])
def tables_free(table_id):
    db = get_db()
    db.execute("UPDATE tables SET status='free' WHERE table_id=?", (table_id,))
    db.commit()
    db.close()
    flash("Table marked free.", "info")
    return redirect(url_for("tables"))


# --------------------------------------------------------------------------
# Order Management
# --------------------------------------------------------------------------
@app.route("/orders")
def orders():
    db = get_db()
    open_orders = db.execute("""
        SELECT o.order_id, t.label, t.table_id, o.created_at,
               COALESCE(SUM(oi.quantity * oi.price_each), 0) as running_total
        FROM orders o
        JOIN tables t ON o.table_id = t.table_id
        LEFT JOIN order_items oi ON oi.order_id = o.order_id
        WHERE o.status = 'open'
        GROUP BY o.order_id
        ORDER BY o.order_id DESC
    """).fetchall()
    free_tables = db.execute("SELECT * FROM tables WHERE status='free' ORDER BY table_id").fetchall()
    db.close()
    return render_template("orders.html", open_orders=open_orders, free_tables=free_tables)


@app.route("/orders/create", methods=["POST"])
def orders_create():
    table_id = int(request.form["table_id"])
    db = get_db()
    table = db.execute("SELECT * FROM tables WHERE table_id=?", (table_id,)).fetchone()
    if not table or table["status"] != "free":
        flash("That table is not available.", "error")
        db.close()
        return redirect(url_for("orders"))

    cur = db.cursor()
    cur.execute(
        "INSERT INTO orders (table_id, status, created_at) VALUES (?, 'open', ?)",
        (table_id, now_str()),
    )
    order_id = cur.lastrowid
    db.execute("UPDATE tables SET status='occupied' WHERE table_id=?", (table_id,))
    db.commit()
    db.close()
    flash(f"Order #{order_id} opened for table {table['label']}.", "success")
    return redirect(url_for("order_detail", order_id=order_id))


@app.route("/orders/<int:order_id>")
def order_detail(order_id):
    db = get_db()
    order = db.execute("""
        SELECT o.*, t.label, t.table_id FROM orders o
        JOIN tables t ON o.table_id = t.table_id
        WHERE o.order_id=?
    """, (order_id,)).fetchone()

    if not order:
        db.close()
        flash("Order not found.", "error")
        return redirect(url_for("orders"))

    line_items = db.execute("""
        SELECT oi.id, m.name, oi.quantity, oi.price_each,
               (oi.quantity * oi.price_each) as line_total
        FROM order_items oi JOIN menu m ON oi.item_id = m.item_id
        WHERE oi.order_id=?
    """, (order_id,)).fetchall()

    subtotal = sum(row["line_total"] for row in line_items)
    available_items = db.execute(
        "SELECT * FROM menu WHERE available=1 ORDER BY category, name"
    ).fetchall()
    bill = db.execute("SELECT * FROM bills WHERE order_id=?", (order_id,)).fetchone()
    db.close()

    return render_template(
        "order_detail.html",
        order=order,
        line_items=line_items,
        subtotal=subtotal,
        available_items=available_items,
        bill=bill,
    )


@app.route("/orders/<int:order_id>/add_item", methods=["POST"])
def order_add_item(order_id):
    item_id = int(request.form["item_id"])
    quantity = int(request.form["quantity"])
    db = get_db()
    order = db.execute("SELECT status FROM orders WHERE order_id=?", (order_id,)).fetchone()
    if not order or order["status"] != "open":
        flash("This order is closed and cannot be modified.", "error")
        db.close()
        return redirect(url_for("order_detail", order_id=order_id))

    item = db.execute("SELECT * FROM menu WHERE item_id=?", (item_id,)).fetchone()
    if item and quantity > 0:
        db.execute(
            "INSERT INTO order_items (order_id, item_id, quantity, price_each) VALUES (?, ?, ?, ?)",
            (order_id, item_id, quantity, item["price"]),
        )
        db.commit()
        flash(f"Added {quantity} x {item['name']}.", "success")
    db.close()
    return redirect(url_for("order_detail", order_id=order_id))


@app.route("/orders/<int:order_id>/remove_item/<int:line_id>", methods=["POST"])
def order_remove_item(order_id, line_id):
    db = get_db()
    db.execute("DELETE FROM order_items WHERE id=? AND order_id=?", (line_id, order_id))
    db.commit()
    db.close()
    flash("Item removed from order.", "info")
    return redirect(url_for("order_detail", order_id=order_id))


# --------------------------------------------------------------------------
# Billing
# --------------------------------------------------------------------------
@app.route("/orders/<int:order_id>/bill", methods=["POST"])
def generate_bill(order_id):
    discount_pct = float(request.form.get("discount_pct", 0) or 0)

    db = get_db()
    order = db.execute("SELECT * FROM orders WHERE order_id=?", (order_id,)).fetchone()
    if not order:
        db.close()
        flash("Order not found.", "error")
        return redirect(url_for("orders"))

    line_items = db.execute(
        "SELECT quantity, price_each FROM order_items WHERE order_id=?", (order_id,)
    ).fetchall()
    subtotal = sum(row["quantity"] * row["price_each"] for row in line_items)

    if subtotal <= 0:
        db.close()
        flash("Cannot bill an order with no items.", "error")
        return redirect(url_for("order_detail", order_id=order_id))

    discount_amount = subtotal * (discount_pct / 100.0)
    taxable = subtotal - discount_amount
    tax = taxable * TAX_RATE
    total = taxable + tax

    db.execute("""
        INSERT INTO bills (order_id, subtotal, discount, tax, total, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (order_id, subtotal, discount_amount, tax, total, now_str()))

    db.execute("UPDATE orders SET status='closed', closed_at=? WHERE order_id=?", (now_str(), order_id))
    db.execute("UPDATE tables SET status='free' WHERE table_id=?", (order["table_id"],))
    db.commit()
    db.close()

    flash("Bill generated. Table is now free.", "success")
    return redirect(url_for("bill_detail", order_id=order_id))


@app.route("/bills")
def bills():
    db = get_db()
    all_bills = db.execute("""
        SELECT b.*, t.label FROM bills b
        JOIN orders o ON b.order_id = o.order_id
        JOIN tables t ON o.table_id = t.table_id
        ORDER BY b.bill_id DESC
    """).fetchall()
    db.close()
    return render_template("bills.html", bills=all_bills)


@app.route("/bills/<int:order_id>")
def bill_detail(order_id):
    db = get_db()
    bill = db.execute("SELECT * FROM bills WHERE order_id=?", (order_id,)).fetchone()
    order = db.execute("""
        SELECT o.*, t.label FROM orders o JOIN tables t ON o.table_id = t.table_id
        WHERE o.order_id=?
    """, (order_id,)).fetchone()
    line_items = db.execute("""
        SELECT m.name, oi.quantity, oi.price_each, (oi.quantity * oi.price_each) as line_total
        FROM order_items oi JOIN menu m ON oi.item_id = m.item_id
        WHERE oi.order_id=?
    """, (order_id,)).fetchall()
    db.close()

    if not bill:
        flash("No bill found for this order.", "error")
        return redirect(url_for("orders"))

    return render_template("bill_detail.html", bill=bill, order=order, line_items=line_items)


# --------------------------------------------------------------------------
# Reports
# --------------------------------------------------------------------------
@app.route("/reports")
def reports():
    db = get_db()
    total_bills, total_revenue = db.execute(
        "SELECT COUNT(*), COALESCE(SUM(total), 0) FROM bills"
    ).fetchone()

    today = datetime.date.today().isoformat()
    today_bills, today_revenue = db.execute(
        "SELECT COUNT(*), COALESCE(SUM(total), 0) FROM bills WHERE created_at LIKE ?",
        (today + "%",),
    ).fetchone()

    top_items = db.execute("""
        SELECT m.name, m.category, SUM(oi.quantity) as qty,
               SUM(oi.quantity * oi.price_each) as revenue
        FROM order_items oi JOIN menu m ON oi.item_id = m.item_id
        GROUP BY m.name ORDER BY qty DESC LIMIT 10
    """).fetchall()

    daily_sales = db.execute("""
        SELECT substr(created_at, 1, 10) as day, COUNT(*) as bill_count, SUM(total) as revenue
        FROM bills GROUP BY day ORDER BY day DESC LIMIT 14
    """).fetchall()

    db.close()
    return render_template(
        "reports.html",
        total_bills=total_bills,
        total_revenue=total_revenue,
        today_bills=today_bills,
        today_revenue=today_revenue,
        top_items=top_items,
        daily_sales=daily_sales,
    )


if __name__ == "__main__":
    init_db()
    seed_demo_data()
    app.run(debug=True, host="127.0.0.1", port=5000)
