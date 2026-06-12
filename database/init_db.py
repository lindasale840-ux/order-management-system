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

        try:

            conn.execute(text("""

            ALTER TABLE orders
            ADD COLUMN sale_owner TEXT

            """))

        except Exception:

            pass
        
        try:

            conn.execute(text("""

            ALTER TABLE orders
            ADD COLUMN created_by TEXT

            """))

        except Exception:

            pass

        try:

            conn.execute(text("""

            ALTER TABLE orders
            ADD COLUMN invoice_group TEXT

            """))

        except Exception:

            pass

        try:

            conn.execute(text("""

            ALTER TABLE orders
            ADD COLUMN is_deleted INTEGER DEFAULT 0

            """))

        except Exception:

            pass


        try:

            conn.execute(text("""

            ALTER TABLE orders
            ADD COLUMN deleted_at TEXT

            """))

        except Exception:

            pass


        try:

            conn.execute(text("""

            ALTER TABLE orders
            ADD COLUMN deleted_by TEXT

            """))

        except Exception:

            pass

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

        try:

            conn.execute(text("""

            ALTER TABLE payments
            ADD COLUMN invoice_group TEXT

            """))

        except Exception:

            pass
        
        try:

            conn.execute(text("""

            ALTER TABLE payments
            ADD COLUMN invoice_created_by TEXT

            """))

        except Exception:

            pass

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

        try:

            conn.execute(text("""

            ALTER TABLE logs
            ADD COLUMN username TEXT

            """))

        except Exception:

            pass

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

        try:

            conn.execute(text("""

            ALTER TABLE users
            ADD COLUMN sale_owner TEXT

            """))

        except Exception:

            pass

        # =========================
        # EXTERNAL EXPENSES
        # =========================

        conn.execute(text("""

        CREATE TABLE IF NOT EXISTS external_expenses (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            expense_date DATE,

            amount FLOAT,

            note TEXT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )

        """))

        # =========================
        # REVENUE KPI
        # =========================
        conn.execute(text("""

        CREATE TABLE IF NOT EXISTS revenue_kpi (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            year INTEGER NOT NULL,

            month INTEGER NOT NULL,

            target_amount REAL NOT NULL,

            UNIQUE(year, month)

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
        # DOCUMENT TRACKING
        # =========================

        conn.execute(text("""

        CREATE TABLE IF NOT EXISTS document_tracking (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            order_number TEXT,

            sent_date DATE,

            received_date DATE,

            note TEXT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )

        """))


        # =========================
        # OTHER DOCUMENT TRACKING
        # =========================

        conn.execute(text("""

        CREATE TABLE IF NOT EXISTS other_document_tracking (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            customer_name TEXT,

            document_type TEXT,

            sent_date DATE,

            received_date DATE,

            note TEXT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )

        """))
        # =========================
        # EQUIPMENT TRACKING
        # =========================

        conn.execute(text("""

        CREATE TABLE IF NOT EXISTS equipment_tracking (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            order_number TEXT,

            service_type TEXT,

            direct_to_customer INTEGER DEFAULT 0,

            subcontract_name TEXT,

            customer_send_date DATE,

            gst_receive_date DATE,

            gst_send_sub_date DATE,

            sub_receive_date DATE,

            sub_send_date DATE,

            gst_receive_back_date DATE,

            gst_send_customer_date DATE,

            customer_receive_date DATE,

            note TEXT,

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