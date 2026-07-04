import psycopg2
from psycopg2.extras import RealDictCursor
import streamlit as st
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pandas")

# =====================================================================
# 1. CẤU HÌNH THÔNG TIN KẾT NỐI (MÁY LOCAL CỦA BẠN)
# =====================================================================
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "erp_order_system"  # Tên database bạn tạo ở bước 4 lúc nãy
DB_USER = "postgres"          # Tài khoản mặc định tối cao của Postgres
DB_PASS = "famille123"            # Hãy thay bằng mật khẩu bạn đã đặt khi cài đặt nhé!

# =====================================================================
# 2. CÁC HÀM TIÊU CHUẨN ĐỂ THAO TÁC VỚI DATABASE
# =====================================================================

def get_pg_connection():
    """Hàm khởi tạo kết nối đến PostgreSQL"""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
        return conn
    except Exception as e:
        st.error(f"❌ Lỗi kết nối PostgreSQL: {e}")
        return None

def init_pg_db():
    """Hàm kiểm tra kết nối đầu vào (Chạy thử khi khởi động ứng dụng)"""
    conn = get_pg_connection()
    if conn:
        print("🎉 Kết nối thành công đến PostgreSQL!")
        conn.close()
    else:
        print("💀 Kết nối thất bại. Hãy kiểm tra lại thông tin cấu hình.")

# Bạn có thể thêm các hàm thực thi câu lệnh SQL dùng chung ở đây sau này

# Chèn đoạn này vào cuối file pg_database.py của bạn:

def query_pg_to_dataframe(sql, params=None):
    """
    Hàm đọc dữ liệu từ Postgres và trả về một chiếc Pandas Dataframe.
    Thay thế hoàn toàn cho lệnh `pd.read_sql_query(sql, conn_sqlite)` cũ.
    """
    import pandas as pd
    conn = get_pg_connection()
    if not conn:
        return pd.DataFrame()
    try:
        # Sử dụng pd.read_sql_query trực tiếp với kết nối Postgres
        df = pd.read_sql_query(sql, conn, params=params)
        return df
    except Exception as e:
        print(f"❌ Lỗi truy vấn Dataframe từ Postgres: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def execute_pg_query(sql, params=None):
    """
    Hàm thực thi các câu lệnh thay đổi dữ liệu (INSERT, UPDATE, DELETE).
    Thay thế cho cursor.execute() và conn.commit() cũ.
    """
    conn = get_pg_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"❌ Lỗi thực thi lệnh SQL trên Postgres: {e}")
        return False
    finally:
        conn.close()
        
def export_pg_backup():
    """Hàm xuất toàn bộ cấu trúc và dữ liệu PostgreSQL thành dạng chuỗi văn bản (SQL Script)"""
    import io
    conn = get_pg_connection()
    if not conn:
        return None
    try:
        # Sử dụng sub-process hoặc giải pháp loop qua từng bảng để tạo file SQL
        # Để đơn giản và không phụ thuộc vào tool ngoài, ta đọc trực tiếp cấu trúc
        # Tuy nhiên cách nhanh nhất là dùng pg_dump nếu máy có cài, hoặc tạo script backup.
        # Ở đây ta sẽ giả định tạo nội dung text SQL hoặc dùng thư viện có sẵn:
        
        # Mẹo: Cách an toàn nhất không lỗi font là xuất dữ liệu thông qua pg_dump script của Postgres.
        # Nhưng để app Streamlit tự chạy độc lập mượt mà, ta sử dụng câu lệnh kết nối:
        import subprocess
        # Gọi lệnh pg_dump tích hợp sẵn của Postgres
        command = f'"C:\\Program Files\\PostgreSQL\\18\\bin\\pg_dump.exe" -h {DB_HOST} -p {DB_PORT} -U {DB_USER} -d {DB_NAME} --clean'
        # Lưu ý: Postgres sẽ đòi mật khẩu, ta truyền mật khẩu qua biến môi trường PGPASSWORD
        import os
        env = os.environ.copy()
        env["PGPASSWORD"] = DB_PASS
        
        # BẠN SỬA LẠI THÀNH ĐOẠN NÀY (Bỏ text=True và thêm errors='ignore' để ép kiểu an toàn):
        result = subprocess.run(command, shell=True, capture_output=True, env=env)

        if result.returncode == 0:
            # Trả về trực tiếp dữ liệu dạng bytes dạng utf-8 mà không qua bộ giải mã của Windows
            return result.stdout
        else:
            # Nếu lỗi, ta decode bằng utf-8 và bỏ qua ký tự lỗi để in ra log
            error_msg = result.stderr.decode('utf-8', errors='ignore')
            print(f"❌ Lỗi pg_dump: {error_msg}")
            return None
    except Exception as e:
        print(f"❌ Lỗi khi tạo bản sao lưu Postgres: {e}")
        return None
    finally:
        conn.close()        