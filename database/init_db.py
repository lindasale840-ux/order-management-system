from sqlalchemy import text
from database.connection import engine
from utils.password_utils import hash_password

def initialize_database():
    with engine.begin() as conn:
        # Kiểm tra xem hệ thống đang dùng dialect nào (postgresql hay sqlite)
        is_postgres = conn.dialect.name == "postgresql"

        # Định nghĩa kiểu dữ liệu và cú pháp tăng tự động theo từng DB
        id_type = "SERIAL PRIMARY KEY" if is_postgres else "INTEGER PRIMARY KEY AUTOINCREMENT"
        float_type = "DOUBLE PRECISION" if is_postgres else "FLOAT"

        # =========================
        # ORDERS
        # =========================
        conn.execute(text(f"""
        CREATE TABLE IF NOT EXISTS orders (
            id {id_type},
            customer_name TEXT,
            order_number TEXT UNIQUE,
            measurement_date DATE,
            cert_status DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """))

        # Xử lý bẫy thêm cột động dựa trên hệ quản trị DB đang kết nối
        if is_postgres:
            conn.execute(text("""
            DO $$ 
            BEGIN 
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='orders' AND column_name='sale_owner') THEN
                    ALTER TABLE orders ADD COLUMN sale_owner TEXT;
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='orders' AND column_name='created_by') THEN
                    ALTER TABLE orders ADD COLUMN created_by TEXT;
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='orders' AND column_name='disable_calibration_notification') THEN
                    ALTER TABLE orders ADD COLUMN disable_calibration_notification INTEGER DEFAULT 0;
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='orders' AND column_name='disable_document_notification') THEN
                    ALTER TABLE orders ADD COLUMN disable_document_notification INTEGER DEFAULT 0;
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='orders' AND column_name='invoice_group') THEN
                    ALTER TABLE orders ADD COLUMN invoice_group TEXT;
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='orders' AND column_name='is_deleted') THEN
                    ALTER TABLE orders ADD COLUMN is_deleted INTEGER DEFAULT 0;
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='orders' AND column_name='deleted_at') THEN
                    ALTER TABLE orders ADD COLUMN deleted_at TEXT;
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='orders' AND column_name='deleted_by') THEN
                    ALTER TABLE orders ADD COLUMN deleted_by TEXT;
                END IF;
            END $$;
            """))
        else:
            # Fallback về khối try-except cũ nếu chạy trên SQLite local
            for col, dtype in [("sale_owner", "TEXT"), ("created_by", "TEXT"), 
                               ("disable_calibration_notification", "INTEGER DEFAULT 0"),
                               ("disable_document_notification", "INTEGER DEFAULT 0"), 
                               ("invoice_group", "TEXT"), ("is_deleted", "INTEGER DEFAULT 0"),
                               ("deleted_at", "TEXT"), ("deleted_by", "TEXT")]:
                try:
                    conn.execute(text(f"ALTER TABLE orders ADD COLUMN {col} {dtype}"))
                except Exception:
                    pass

        # =========================
        # PAYMENTS
        # =========================
        conn.execute(text(f"""
        CREATE TABLE IF NOT EXISTS payments (
            id {id_type},
            order_number TEXT UNIQUE,
            invoice_date DATE,
            payment_terms INTEGER,
            payment_status DATE,
            total {float_type},
            commission_percent {float_type},
            commission_actual {float_type},
            note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """))

        if is_postgres:
            conn.execute(text("""
            DO $$ 
            BEGIN 
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='payments' AND column_name='invoice_group') THEN
                    ALTER TABLE payments ADD COLUMN invoice_group TEXT;
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='payments' AND column_name='invoice_created_by') THEN
                    ALTER TABLE payments ADD COLUMN invoice_created_by TEXT;
                END IF;
            END $$;
            """))
        else:
            for col, dtype in [("invoice_group", "TEXT"), ("invoice_created_by", "TEXT")]:
                try:
                    conn.execute(text(f"ALTER TABLE payments ADD COLUMN {col} {dtype}"))
                except Exception:
                    pass

        # =========================
        # LOGS
        # =========================
        conn.execute(text(f"""
        CREATE TABLE IF NOT EXISTS logs (
            id {id_type},
            action TEXT,
            customer_name TEXT,
            order_number TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """))

        if is_postgres:
            conn.execute(text("""
            DO $$ 
            BEGIN 
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='logs' AND column_name='username') THEN
                    ALTER TABLE logs ADD COLUMN username TEXT;
                END IF;
            END $$;
            """))
        else:
            try:
                conn.execute(text("ALTER TABLE logs ADD COLUMN username TEXT"))
            except Exception:
                pass

        # =========================
        # USERS
        # =========================
        conn.execute(text(f"""
        CREATE TABLE IF NOT EXISTS users (
            id {id_type},
            username TEXT UNIQUE,
            password_hash TEXT,
            role TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """))

        if is_postgres:
            conn.execute(text("""
            DO $$ 
            BEGIN 
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='sale_owner') THEN
                    ALTER TABLE users ADD COLUMN sale_owner TEXT;
                END IF;
            END $$;
            """))
        else:
            try:
                conn.execute(text("ALTER TABLE users ADD COLUMN sale_owner TEXT"))
            except Exception:
                pass

        # =========================
        # EXTERNAL EXPENSES
        # =========================
        conn.execute(text(f"""
        CREATE TABLE IF NOT EXISTS external_expenses (
            id {id_type},
            expense_date DATE,
            amount {float_type},
            note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """))

        # =========================
        # REVENUE KPI
        # =========================
        conn.execute(text(f"""
        CREATE TABLE IF NOT EXISTS revenue_kpi (
            id {id_type},
            year INTEGER NOT NULL,
            month INTEGER NOT NULL,
            target_amount {float_type} NOT NULL,
            UNIQUE(year, month)
        )
        """))

        # =========================
        # ERROR LOGS
        # =========================
        conn.execute(text(f"""
        CREATE TABLE IF NOT EXISTS error_logs (
            id {id_type},
            page_name TEXT,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """))

        # =========================
        # DOCUMENT TRACKING
        # =========================
        conn.execute(text(f"""
        CREATE TABLE IF NOT EXISTS document_tracking (
            id {id_type},
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
        conn.execute(text(f"""
        CREATE TABLE IF NOT EXISTS other_document_tracking (
            id {id_type},
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
        conn.execute(text(f"""
        CREATE TABLE IF NOT EXISTS equipment_tracking (
            id {id_type},
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
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_name)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_orders_order ON orders(order_number)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_payments_order ON payments(order_number)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_logs_order ON logs(order_number)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_logs_customer ON logs(customer_name)"))
        
        # =========================
        # ASSISTANT SALE MAPPING
        # =========================
        conn.execute(text(f"""
        CREATE TABLE IF NOT EXISTS assistant_sale_mapping (
            id {id_type},
            assistant_username TEXT NOT NULL,
            sale_owner TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(assistant_username, sale_owner)
        )
        """))

        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_assistant_mapping_assistant ON assistant_sale_mapping(assistant_username)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_assistant_mapping_sale ON assistant_sale_mapping(sale_owner)"))
        
        # =========================
        # NOTES
        # =========================
        conn.execute(text(f"""
        CREATE TABLE IF NOT EXISTS notes (
            id {id_type},
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            content TEXT,
            category TEXT DEFAULT 'general',
            priority TEXT DEFAULT 'medium',
            layer INTEGER DEFAULT 1,
            status TEXT DEFAULT 'pending',
            due_date DATE,
            is_read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """))

        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_notes_user_id ON notes(user_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_notes_status ON notes(status)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_notes_priority ON notes(priority)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_notes_layer ON notes(layer)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_notes_is_read ON notes(is_read)"))

        # =========================
        # DEFAULT ADMIN
        # =========================
        admin_exist = conn.execute(
            text("SELECT COUNT(*) FROM users WHERE username='admin'")
        ).scalar()

        if admin_exist == 0:
            conn.execute(
                text("""
                INSERT INTO users (username, password_hash, role)
                VALUES (:username, :password_hash, :role)
                """),
                {
                    "username": "admin",
                    "password_hash": hash_password("123456"),
                    "role": "ADMIN"
                }
            )