import os
import psycopg2
from psycopg2.extras import RealDictCursor
import streamlit as st
import warnings
from dotenv import load_dotenv
from urllib.parse import urlparse

warnings.filterwarnings("ignore", category=UserWarning, module="pandas")

# =====================================================================
# 1. TỰ ĐỘNG CẤU HÌNH THÔNG TIN KẾT NỐI TỪ FILE .env
# =====================================================================
# Nạp các biến môi trường từ file .env
load_dotenv()

# Đọc chuỗi kết nối DATABASE_URL từ file .env
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Tự động bóc tách chuỗi URL thành các thông số riêng lẻ để tương thích với logic cũ
    parsed_url = urlparse(DATABASE_URL)
    DB_HOST = parsed_url.hostname or "localhost"
    DB_PORT = str(parsed_url.port) or "5432"
    DB_NAME = parsed_url.path.lstrip("/") or "erp_production"
    DB_USER = parsed_url.username or "postgres"
    DB_PASS = parsed_url.password or ""
else:
    # Cấu hình dự phòng (Fallback) nếu không tìm thấy file .env
    DB_HOST = "localhost"
    DB_PORT = "5432"
    DB_NAME = "erp_production"
    DB_USER = "postgres"
    DB_PASS = "famille123"

# =====================================================================
# 2. CÁC HÀM TIÊU CHUẨN ĐỂ THAO TÁC VỚI DATABASE (GIỮ NGUYÊN LOGIC)
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

def execute_pg_query(query, params=None):
    import pandas as pd
    
    # 1. TỰ ĐỘNG ÉP KIỂU CHO TOÀN HỆ THỐNG:
    if params:
        new_params = []
        for p in params:
            if isinstance(p, bool):
                new_params.append(1 if p else 0)
            elif pd.isna(p):  
                new_params.append(None)
            else:
                new_params.append(p)
        params = tuple(new_params)

    conn = None
    try:
        conn = get_pg_connection() 
        # ĐỔI THÀNH SỬ DỤNG RealDictCursor ĐỂ LẤY DỮ LIỆU DẠNG KEY-VALUE
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(query, params)
        
        # Lấy dữ liệu nếu đây là câu lệnh SELECT
        result = None
        if cur.description: 
            result = cur.fetchall()
        
        # Đảm bảo LUÔN commit để Postgres lưu dữ liệu thực tế
        conn.commit() 
        
        cur.close()
        return result 
        
    except Exception as e:
        if conn:
            conn.rollback()
        raise e 
    finally:
        if conn:
            conn.close()
        
def query_pg_to_dataframe(sql, params=None):
    """
    Hàm đọc dữ liệu từ Postgres và trả về một chiếc Pandas Dataframe chuẩn chỉnh.
    """
    import pandas as pd
    
    try:
        # 1. Lấy dữ liệu dạng danh sách các Dictionary nhờ có RealDictCursor
        data = execute_pg_query(sql, params)
        
        # 2. Chuyển thẳng danh sách Dictionary thành DataFrame (Tên cột tự động nhận diện chính xác)
        if data:
            return pd.DataFrame(data)
        else:
            return pd.DataFrame()
            
    except Exception as e:
        print(f"❌ Lỗi truy vấn Dataframe từ Postgres: {e}")
        return pd.DataFrame()
            
def export_pg_backup():
    """Hàm xuất toàn bộ cấu trúc và dữ liệu PostgreSQL thành dạng chuỗi văn bản (SQL Script)"""
    conn = get_pg_connection()
    if not conn:
        return None
    try:
        import subprocess
        # Gọi lệnh pg_dump tích hợp sẵn của Postgres
        command = f'"C:\\Program Files\\PostgreSQL\\18\\bin\\pg_dump.exe" -h {DB_HOST} -p {DB_PORT} -U {DB_USER} -d {DB_NAME} --clean'
        
        import os
        env = os.environ.copy()
        env["PGPASSWORD"] = DB_PASS
        
        result = subprocess.run(command, shell=True, capture_output=True, env=env)

        if result.returncode == 0:
            return result.stdout
        else:
            error_msg = result.stderr.decode('utf-8', errors='ignore')
            print(f"❌ Lỗi pg_dump: {error_msg}")
            return None
    except Exception as e:
        print(f"❌ Lỗi khi tạo bản sao lưu Postgres: {e}")
        return None
    finally:
        conn.close()