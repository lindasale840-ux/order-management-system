from sqlalchemy import text

from database.connection import engine

from utils.password_utils import (
    hash_password
)


def initialize_database():

    with engine.begin() as conn:

        # =========================
        # ORDERS
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
        # PAYMENTS
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
        # LOGS
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
        # USERS
        # =========================

        conn.execute(text("""

        CREATE TABLE IF NOT EXISTS users (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            username TEXT UNIQUE,

            password_hash TEXT,

            role TEXT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )

        """))

                # =========================
        # ERROR LOGS
        # =========================

        conn.execute(text("""

        CREATE TABLE IF NOT EXISTS error_logs (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            page_name TEXT,

            error_message TEXT,

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

        # =========================
        # DEFAULT ADMIN
        # =========================

        admin_exist = conn.execute(

            text("""

            SELECT COUNT(*)

            FROM users

            WHERE username='admin'

            """)

        ).scalar()

        if admin_exist == 0:

            conn.execute(

                text("""

                INSERT INTO users (

                    username,

                    password_hash,

                    role

                )

                VALUES (

                    :username,

                    :password_hash,

                    :role

                )

                """),

                {

                    "username": "admin",

                    "password_hash": hash_password(
                        "123456"
                    ),

                    "role": "ADMIN"
                }
            )