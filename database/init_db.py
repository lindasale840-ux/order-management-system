from sqlalchemy import text

from database.connection import engine


def initialize_database():

    with engine.begin() as conn:

        # =========================
        # ORDERS TABLE
        # =========================

        conn.execute(text("""

        CREATE TABLE IF NOT EXISTS orders (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            customer_name TEXT,

            order_number TEXT UNIQUE,

            measurement_date DATE,

            cert_status DATE,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )

        """))

        # =========================
        # PAYMENTS TABLE
        # =========================

        conn.execute(text("""

        CREATE TABLE IF NOT EXISTS payments (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            order_number TEXT UNIQUE,

            invoice_date DATE,

            payment_terms INTEGER,

            payment_status DATE,

            total FLOAT,

            commission_percent FLOAT,

            commission_actual FLOAT,

            note TEXT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )

        """))

        # =========================
        # LOGS TABLE
        # =========================

        conn.execute(text("""

        CREATE TABLE IF NOT EXISTS logs (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            action TEXT,

            customer_name TEXT,

            order_number TEXT,

            description TEXT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )

        """))

        # =========================
        # INDEXES
        # =========================

        conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_orders_customer
        ON orders(customer_name)
        """))

        conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_orders_order
        ON orders(order_number)
        """))

        conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_payments_order
        ON payments(order_number)
        """))

        conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_logs_order
        ON logs(order_number)
        """))

        conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_logs_customer
        ON logs(customer_name)
        """))