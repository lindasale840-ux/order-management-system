from sqlalchemy import text
from database.connection import engine
from utils.password_utils import hash_password

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

        try: conn.execute(text("ALTER TABLE orders ADD COLUMN sale_owner TEXT"))
        except Exception: pass
        try: conn.execute(text("ALTER TABLE orders ADD COLUMN created_by TEXT"))
        except Exception: pass
        try: conn.execute(text("ALTER TABLE orders ADD COLUMN disable_calibration_notification INTEGER DEFAULT 0"))
        except Exception: pass
        try: conn.execute(text("ALTER TABLE orders ADD COLUMN disable_document_notification INTEGER DEFAULT 0"))
        except Exception: pass    
        try: conn.execute(text("ALTER TABLE orders ADD COLUMN invoice_group TEXT"))
        except Exception: pass
        try: conn.execute(text("ALTER TABLE orders ADD COLUMN is_deleted INTEGER DEFAULT 0"))
        except Exception: pass
        try: conn.execute(text("ALTER TABLE orders ADD COLUMN deleted_at TEXT"))
        except Exception: pass
        try: conn.execute(text("ALTER TABLE orders ADD COLUMN deleted_by TEXT"))
        except Exception: pass

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

        try: conn.execute(text("ALTER TABLE payments ADD COLUMN invoice_group TEXT"))
        except Exception: pass
        try: conn.execute(text("ALTER TABLE payments ADD COLUMN invoice_created_by TEXT"))
        except Exception: pass

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

        try: conn.execute(text("ALTER TABLE logs ADD COLUMN username TEXT"))
        except Exception: pass

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

        try: conn.execute(text("ALTER TABLE users ADD COLUMN sale_owner TEXT"))
        except Exception: pass

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

        # ========================================================
        # DOCUMENT TEMPLATES
        # ========================================================
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS document_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            template_type TEXT, 
            language_type TEXT, 
            title TEXT,
            content TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(template_type, language_type)
        )
        """))
        
        try: conn.execute(text("ALTER TABLE document_templates ADD COLUMN language_type TEXT"))
        except Exception: pass

        check_templates = conn.execute(text("SELECT COUNT(*) FROM document_templates")).scalar()
        if check_templates == 0:
            conn.execute(text("""
            INSERT OR IGNORE INTO document_templates (template_type, language_type, title, content) 
            VALUES 
            ('contract', 'zh_vi', 'Hợp đồng Mua bán Trung - Việt', '<h2 style="text-align: center; color: #1e3a8a;">买卖合同 / HỢP ĐỒNG MUA BÁN (TRUNG-VIỆT)</h2><p>Vui lòng nhập nội dung form chuẩn tại đây...</p>'),
            ('contract', 'en_vi', 'Hợp đồng Mua bán Anh - Việt', '<h2 style="text-align: center; color: #047857;">SALES CONTRACT / HỢP ĐỒNG MUA BÁN (ANH-VIỆT)</h2><p>Vui lòng nhập nội dung form chuẩn tại đây...</p>'),
            ('payment_request', 'zh_vi', 'Đề nghị thanh toán Trung - Việt', '<h3 style="text-align: center;">付款申请书 / ĐỀ NGHỊ THANH TOÁN</h3>'),
            ('payment_request', 'en_vi', 'Đề nghị thanh toán Anh - Việt', '<h3 style="text-align: center;">PAYMENT REQUEST / ĐỀ NGHỊ THANH TOÁN</h3>')
            """))

        # ========================================================
        # BUSINESS FORMS - ÉP BUỘC VÁ CỘT CHO DB CŨ
        # ========================================================
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS erp_business_forms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            form_name TEXT,
            description TEXT,
            file_path TEXT,
            file_name TEXT
        )
        """))
        
        # Đảm bảo các cột file phải xuất hiện đầy đủ trong database cũ
        try: conn.execute(text("ALTER TABLE erp_business_forms ADD COLUMN description TEXT"))
        except Exception: pass
        try: conn.execute(text("ALTER TABLE erp_business_forms ADD COLUMN file_path TEXT"))
        except Exception: pass
        try: conn.execute(text("ALTER TABLE erp_business_forms ADD COLUMN file_name TEXT"))
        except Exception: pass

        conn.execute(text("DELETE FROM erp_business_forms WHERE form_name LIKE '%Mẫu báo giá chuẩn%' OR form_name LIKE '%Biên bản nghiệm thu%'"))

        # ========================================================
        # CERTIFICATES - ÉP BUỘC VÁ CỘT CHO DB CŨ
        # ========================================================
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS erp_certificates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cert_name TEXT,
            contractor_name TEXT,
            version TEXT,
            expiry_date TEXT,
            file_path TEXT,
            file_name TEXT
        )
        """))
        
        # Đảm bảo các cột file phải xuất hiện đầy đủ trong database cũ tránh lỗi OperationalError
        try: conn.execute(text("ALTER TABLE erp_certificates ADD COLUMN contractor_name TEXT"))
        except Exception: pass
        try: conn.execute(text("ALTER TABLE erp_certificates ADD COLUMN version TEXT"))
        except Exception: pass
        try: conn.execute(text("ALTER TABLE erp_certificates ADD COLUMN expiry_date TEXT"))
        except Exception: pass
        try: conn.execute(text("ALTER TABLE erp_certificates ADD COLUMN file_path TEXT"))
        except Exception: pass
        try: conn.execute(text("ALTER TABLE erp_certificates ADD COLUMN file_name TEXT"))
        except Exception: pass

        conn.execute(text("DELETE FROM erp_certificates WHERE cert_name LIKE '%ISO 9001%' OR cert_name LIKE '%Hồ sơ năng lực%'"))

        # =========================
        # INDEXES
        # =========================
        conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_name)
        """))
        conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_orders_order ON orders(order_number)
        """))
        conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_payments_order ON payments(order_number)
        """))
        conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_logs_order ON logs(order_number)
        """))
        conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_logs_customer ON logs(customer_name)
        """))

        # =========================
        # DEFAULT ADMIN
        # =========================
        admin_exist = conn.execute(text("SELECT COUNT(*) FROM users WHERE username='admin'")).scalar()
        if admin_exist == 0:
            conn.execute(
                text("INSERT INTO users (username, password_hash, role) VALUES (:username, :password_hash, :role)"),
                {"username": "admin", "password_hash": hash_password("123456"), "role": "ADMIN"}
            )