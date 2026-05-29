from sqlalchemy import text
from database.connection import engine


def init_database():

    with engine.connect() as conn:

        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS orders (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            customer_name TEXT NOT NULL,

            order_number TEXT UNIQUE NOT NULL,

            measurement_date DATE,

            cert_status DATE,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """))

        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS payments (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            order_number TEXT UNIQUE NOT NULL,

            invoice_date DATE,

            payment_terms INTEGER,

            payment_status DATE,

            total REAL DEFAULT 0,

            commission_percent REAL DEFAULT 0,

            commission_actual REAL DEFAULT 0,

            note TEXT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """))

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

        conn.commit()