"""
database.py
Handles SQLite connection, schema creation, and demo data seeding
for the Restaurant Management System.
"""

import sqlite3
import os

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "restaurant.db")
TAX_RATE = 0.05  # 5%


def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS menu (
            item_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            category    TEXT NOT NULL,
            price       REAL NOT NULL,
            available   INTEGER NOT NULL DEFAULT 1
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS tables (
            table_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            label       TEXT NOT NULL,
            capacity    INTEGER NOT NULL,
            status      TEXT NOT NULL DEFAULT 'free'
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            table_id    INTEGER NOT NULL,
            status      TEXT NOT NULL DEFAULT 'open',
            created_at  TEXT NOT NULL,
            closed_at   TEXT,
            FOREIGN KEY (table_id) REFERENCES tables (table_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id    INTEGER NOT NULL,
            item_id     INTEGER NOT NULL,
            quantity    INTEGER NOT NULL,
            price_each  REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders (order_id),
            FOREIGN KEY (item_id) REFERENCES menu (item_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS bills (
            bill_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id    INTEGER NOT NULL UNIQUE,
            subtotal    REAL NOT NULL,
            discount    REAL NOT NULL,
            tax         REAL NOT NULL,
            total       REAL NOT NULL,
            created_at  TEXT NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders (order_id)
        )
    """)

    conn.commit()
    conn.close()


def seed_demo_data():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM menu")
    if cur.fetchone()[0] == 0:
        demo_items = [
            ("Paneer Butter Masala", "Main Course", 220.0),
            ("Veg Biryani", "Main Course", 180.0),
            ("Chicken Tikka Masala", "Main Course", 260.0),
            ("Butter Naan", "Bread", 40.0),
            ("Tandoori Roti", "Bread", 25.0),
            ("Masala Dosa", "South Indian", 90.0),
            ("Gulab Jamun", "Dessert", 60.0),
            ("Cold Coffee", "Beverage", 80.0),
            ("Masala Chai", "Beverage", 30.0),
            ("Green Salad", "Starter", 70.0),
        ]
        cur.executemany(
            "INSERT INTO menu (name, category, price) VALUES (?, ?, ?)", demo_items
        )

    cur.execute("SELECT COUNT(*) FROM tables")
    if cur.fetchone()[0] == 0:
        demo_tables = [
            ("T1", 2), ("T2", 2), ("T3", 4),
            ("T4", 4), ("T5", 6), ("T6", 8),
        ]
        cur.executemany(
            "INSERT INTO tables (label, capacity) VALUES (?, ?)", demo_tables
        )

    conn.commit()
    conn.close()
