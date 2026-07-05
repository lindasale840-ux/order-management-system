import sqlite3
import psycopg2
from psycopg2 import sql

# ==============================================================================
# ⚙️ CẤU HÌNH THÔNG TIN KẾT NỐI (Hãy sửa theo thông tin máy của bạn)
# ==============================================================================
SQLITE_DB_PATH = "app.db"  # Đường dẫn tới file SQLite mới nhất mang từ công ty về

POSTGRES_CONFIG = {
    "host": "localhost",
    "database": "erp_prod_test",  # Tên database Postgres (phải tạo trống trước trên pgAdmin)
    "user": "postgres",
    "password": "famille123",  # Điền mật khẩu Postgres của bạn vào đây
    "port": "5432"
}

# Danh sách các bảng cần đồng bộ bộ đếm ID tự tăng
#TABLES_WITH_SEQUENCES = ["orders", "payments", "logs", "document_tracking"]

# ==============================================================================
# 🚀 TIẾN TRÌNH MIGRATION TỰ ĐỘNG
# ==============================================================================
def migrate():
    print("🔌 Đang kết nối tới cả 2 cơ sở dữ liệu...")
    sl_conn = sqlite3.connect(SQLITE_DB_PATH)
    sl_cursor = sl_conn.cursor()
    
    pg_conn = psycopg2.connect(**POSTGRES_CONFIG)
    pg_cursor = pg_conn.cursor()
    
    try:
        # Bước 1: Lấy danh sách tất cả các bảng từ SQLite (trừ các bảng hệ thống)
        sl_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = [row[0] for row in sl_cursor.fetchall()]
        
        print(f"📦 Tìm thấy {len(tables)} bảng trong SQLite cần chuyển đổi.")
        
        for table in tables:
            print(f"--- Đang xử lý bảng: {table} ---")
            
            # Đọc cấu trúc cột từ SQLite
            sl_cursor.execute(f"PRAGMA table_info({table});")
            columns_info = sl_cursor.fetchall()
            
            # Xây dựng câu lệnh CREATE TABLE cho Postgres (Chuyển đổi kiểu dữ liệu cơ bản)
            pg_cols = []
            col_names = []
            for col in columns_info:
                col_name = col[1]
                col_type = col[2].upper()
                is_nullable = "NULL" if col[3] == 0 else "NOT NULL"
                is_pk = col[5]
                
                col_names.append(col_name)
                
                # Ánh xạ kiểu dữ liệu thông minh từ SQLite sang Postgres
                if is_pk and "INT" in col_type:
                    pg_type = "SERIAL PRIMARY KEY"
                elif "INT" in col_type:
                    pg_type = "INTEGER"
                elif "REAL" in col_type or "NUM" in col_type or "DOUBLE" in col_type:
                    pg_type = "DOUBLE PRECISION"
                elif "TEXT" in col_type or "CHAR" in col_type:
                    pg_type = "TEXT"
                elif "BLOB" in col_type:
                    pg_type = "BYTEA"
                else:
                    pg_type = "TEXT" # Mặc định nếu không rõ kiểu
                
                # Tạo chuỗi định nghĩa cột (nếu là khóa chính SERIAL thì không cần thêm NOT NULL nữa)
                if "PRIMARY KEY" in pg_type:
                    pg_cols.append(f'"{col_name}" {pg_type}')
                else:
                    pg_cols.append(f'"{col_name}" {pg_type} {is_nullable}')
            
            # Xóa bảng cũ ở Postgres nếu tồn tại và tạo bảng mới tinh
            pg_cursor.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE;')
            create_query = f'CREATE TABLE "{table}" ({", ".join(pg_cols)});'
            pg_cursor.execute(create_query)
            
            # Đọc toàn bộ dữ liệu từ SQLite
            sl_cursor.execute(f'SELECT * FROM "{table}";')
            rows = sl_cursor.fetchall()
            
            if rows:
                # Chèn dữ liệu hàng loạt vào Postgres
                placeholders = ", ".join(["%s"] * len(col_names))
                insert_query = f'INSERT INTO "{table}" ({", ".join([f'"{c}"' for c in col_names])}) VALUES ({placeholders})'
                pg_cursor.executemany(insert_query, rows)
                print(f"✅ Đã đổ thành công {len(rows)} dòng dữ liệu.")
            else:
                print("ℹ️ Bảng trống, không có dữ liệu để đổ.")

        # ==============================================================================
        # 🛠️ Bước 2: CHẠY LOẠT LỆNH VÁ CẤU TRÚC VÀ ĐỒNG BỘ BỘ ĐẾM
        # ==============================================================================
        print("\n🔧 Đang tiến hành vá cấu trúc và đồng bộ bộ đếm ID...")
        
        # 1. Vá lỗi hiển thị tổng đơn hàng (bảng orders)
        pg_cursor.execute("""
            UPDATE orders SET is_deleted = 0 WHERE is_deleted IS NULL;
            ALTER TABLE orders ALTER COLUMN is_deleted SET DEFAULT 0;
        """)
        print("  -> Đã vá lỗi cột is_deleted bảng orders.")

        # 2. Xử lý trùng lặp và tạo ràng buộc UNIQUE cho bảng payments
        pg_cursor.execute("""
            DELETE FROM payments WHERE id NOT IN (SELECT MIN(id) FROM payments GROUP BY order_number);
            ALTER TABLE payments ADD CONSTRAINT unique_order_number UNIQUE (order_number);
        """)
        print("  -> Đã lọc trùng và tạo ràng buộc UNIQUE (order_number) cho bảng payments.")

        # 🔥 ĐOẠN ĐƯỢC CẢI TIẾN TỰ ĐỘNG: Tự động tìm tất cả các bảng có Sequence ID
        find_sequences_query = """
            SELECT table_name 
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
              AND column_name = 'id' 
              AND column_default LIKE 'nextval%';
        """
        pg_cursor.execute(find_sequences_query)
        dynamic_tables = [row[0] for row in pg_cursor.fetchall()]
        
        print(f"🔍 Hệ thống tự động quét và tìm thấy {len(dynamic_tables)} bảng có bộ đếm ID tự tăng.")

        # 3. Đồng bộ lại tất cả bộ đếm ID (Sequence ID) cho các bảng vừa quét được
        for seq_table in dynamic_tables:
            sync_seq_query = f"""
                SELECT setval(
                    pg_get_serial_sequence('{seq_table}', 'id'), 
                    COALESCE(MAX(id), 0) + 1, 
                    false
                ) FROM "{seq_table}";
            """
            pg_cursor.execute(sync_seq_query)
            print(f"  -> Đã đồng bộ thành công bộ đếm ID cho bảng: {seq_table}")

        # Lưu lại toàn bộ thay đổi vào Postgres
        pg_conn.commit()
        print("\n🎉 CHÚC MỪNG! Quá trình Migration hoàn tất 100% một cách hoàn hảo!")

    except Exception as e:
        pg_conn.rollback()
        print(f"❌ Có lỗi xảy ra trong quá trình Migration, hệ thống đã rollback. Lỗi chi tiết: {e}")
    finally:
        sl_conn.close()
        pg_conn.close()
        print("🔌 Đã ngắt kết nối an toàn.")

if __name__ == "__main__":
    migrate()