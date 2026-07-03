# The Pass — Restaurant Management System

A full-stack restaurant management web app: **Flask** backend, **SQLite**
database, server-rendered HTML/CSS/JS frontend. No frameworks or build step
required — clone it and run it.

## Features

| Module | What it does |
|---|---|
| **Dashboard** | Live counts of open orders, free tables, today's revenue, top sellers, recent orders |
| **Menu Management** | Add, edit, delete dishes; toggle "86" (unavailable) status |
| **Table Management** | Add tables, view floor plan, see free/occupied status at a glance |
| **Orders** | Seat a table (opens an order), fire items to the kitchen, remove items, running total |
| **Billing** | Generate a bill from an open order with optional discount %, auto tax calculation, closes the order and frees the table |
| **Reports** | All-time & today's revenue, top-selling items, daily sales breakdown |

## Tech stack

- **Backend:** Python 3 + Flask (routes in `app.py`)
- **Database:** SQLite (`restaurant.db`, created automatically — see `database.py` for schema)
- **Frontend:** Jinja2 templates + plain CSS + a little vanilla JS (no React/build tools, so there's nothing to compile — just run and go)

## Project structure

```
restaurant-webapp/
├── app.py                 # Flask routes / application logic
├── database.py             # SQLite schema + demo data seeding
├── requirements.txt
├── templates/               # Jinja2 HTML templates
│   ├── base.html            # Shared layout (sidebar nav, flash messages)
│   ├── dashboard.html
│   ├── menu.html
│   ├── tables.html
│   ├── orders.html
│   ├── order_detail.html    # Kitchen-ticket-style order view
│   ├── bills.html
│   ├── bill_detail.html     # Final receipt view
│   └── reports.html
└── static/
    ├── css/style.css        # Design system (CSS variables, components)
    └── js/app.js             # Drawer toggling, flash auto-dismiss
```

## Setup & run

Requires Python 3.9+.

```bash
# 1. Move into the project folder
cd restaurant-webapp

# 2. (Recommended) create a virtual environment
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
python3 app.py
```

Then open **http://127.0.0.1:5000** in your browser.

The database (`restaurant.db`) is created automatically on first run and
pre-seeded with a sample menu (10 dishes) and 6 tables, so the app is ready
to demo immediately — no manual setup needed.

To reset all data, just stop the server and delete `restaurant.db`; it will
be recreated and reseeded next time you run `python3 app.py`.

## Suggested demo flow (for walking through it live)

1. **Dashboard** — show the live stats (all zero on a fresh DB).
2. **Tables** — show the floor plan, all tables free.
3. **Orders** → seat a free table → you land on the order's kitchen ticket.
4. Add 2–3 items with different quantities — watch the ticket update and the running subtotal change.
5. Apply a discount % and click **Generate bill** — table flips back to free, tax and totals are calculated automatically.
6. **Bills** — see the closed check in the list, click in for the final receipt.
7. **Reports** — revenue and top-seller numbers now reflect that sale.
8. **Menu** — add a new dish, edit a price, toggle one item unavailable (86'd) and show it disappears from the "Add items" dropdown on a new order.

## Design notes

The visual identity ("The Pass" — industry term for the kitchen counter
where finished dishes are handed off to servers) uses a charcoal + amber
palette with a monospace receipt font for order tickets and bills, styled
like an actual kitchen order chit with a perforated edge. Condensed
uppercase headings (Oswald) evoke a chalkboard menu board; body text is set
in Inter for readability at data-table density.

## Notes for extending this project

- **Swap SQLite for MySQL/Postgres:** only `database.py` needs to change — replace `sqlite3.connect` with the driver of your choice (e.g. `psycopg2`, `mysql-connector-python`) and adjust the `?` placeholders to `%s` if using MySQL/Postgres.
- **Authentication:** add a `users` table and Flask-Login for staff/admin roles.
- **API layer:** the route functions in `app.py` are a natural place to add JSON responses (`jsonify(...)`) alongside the HTML views if you want a REST API for a mobile app.
- **Deployment:** swap `app.run(debug=True)` for a production WSGI server (gunicorn/uWSGI) behind nginx, and turn debug mode off.
"# restaurant-management-system" 
