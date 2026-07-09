import os
import psycopg2
from psycopg2.extras import RealDictCursor
import streamlit as st
import warnings
import time
GLOBAL_SQL_CACHE = {}
CACHE_TTL = 15  # Thời gian lưu dữ liệu (30 giây). Bạn có thể tăng lên 30 nếu muốn nhanh hơn nữa

warnings.filterwarnings("ignore", category=UserWarning, module="pandas")
warnings.filterwarnings("ignore", category=UserWarning, module="pandas")
warnings.filterwarnings("ignore", message=".*pandas only supports SQLAlchemy connectable.*")
# =====================================================================
# 1. QUẢN LÝ KẾT NỐI THEO CHUẨN KẾT NỐI TRUYỀN THỐNG (TƯƠNG THÍCH 100% CODE CŨ)
# =====================================================================

def get_pg_connection():
    """
    Hàm khởi tạo kết nối PostgreSQL thông minh.
    Ưu tiên đọc file .env ở Local trước để phục vụ đội ngũ dev, 
    chỉ đọc st.secrets khi triển khai thực tế trên Production Cloud.
    """
    try:
        # 1. Nạp file .env cũ dưới local lên trước
        from dotenv import load_dotenv
        load_dotenv()
        db_url = os.getenv("DATABASE_URL")
        
        # 2. Nếu file .env không tồn tại (trên Cloud), lúc này mới dùng đến st.secrets
        if not db_url:
            if "connections" in st.secrets and "postgresql" in st.secrets["connections"]:
                db_url = st.secrets["connections"]["postgresql"]["url"]
            elif "DATABASE_URL" in st.secrets:
                db_url = st.secrets["DATABASE_URL"]
                
        # Trả về kết nối psycopg2 thuần túy
        return psycopg2.connect(db_url)
    except Exception as e:
        st.error(f"❌ Lỗi kết nối PostgreSQL: {e}")
        return None 
# Hàm phụ trợ tách cấu hình phục vụ riêng cho lệnh pg_dump (Hàm backup)
from urllib.parse import urlparse
def _get_db_credentials():
    try:
        from dotenv import load_dotenv
        load_dotenv()
        url = os.getenv("DATABASE_URL")
        
        if not url:
            if "connections" in st.secrets and "postgresql" in st.secrets["connections"]:
                url = st.secrets["connections"]["postgresql"]["url"]
            elif "DATABASE_URL" in st.secrets:
                url = st.secrets["DATABASE_URL"]
                
        parsed_url = urlparse(url)
        return {
            "host": parsed_url.hostname or "localhost",
            "port": str(parsed_url.port) or "5432",
            "name": parsed_url.path.lstrip("/") or "erp_production",
            "user": parsed_url.username or "postgres",
            "pass": parsed_url.password or ""
        }
    except Exception:
        return {"host": "localhost", "port": "5432", "name": "erp_production", "user": "postgres", "pass": ""}
# =====================================================================
# 2. CÁC HÀM TIÊU CHUẨN THAO TÁC DATA (GIỮ NGUYÊN HOÀN TOÀN CẤU TRÚC CỦA BẠN)
# =====================================================================

def init_pg_db():
    conn = get_pg_connection()
    if conn:
        print("🎉 Kết nối thành công đến PostgreSQL!")
        conn.close()
    else:
        print("💀 Kết nối thất bại. Hãy kiểm tra lại thông tin cấu hình.")

def execute_pg_query(query, params=None):
    import pandas as pd
    
    # Chuẩn hóa params để tránh lỗi dữ liệu cũ của bạn
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
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(query, params)
        
        result = None
        if cur.description: 
            result = cur.fetchall()
        
        conn.commit() 
        cur.close()
        return result 
        
    except Exception as e:
        if conn:
            conn.rollback()
        raise e 
    finally:
        if conn:
            conn.close() # Đóng kết nối an toàn

def query_pg_to_dataframe(sql, params=None):
    import pandas as pd
    try:
        data = execute_pg_query(sql, params)
        if data:
            return pd.DataFrame(data)
        else:
            return pd.DataFrame()
    except Exception as e:
        print(f"❌ Lỗi truy vấn Dataframe từ Postgres: {e}")
        return pd.DataFrame()
            
def export_pg_backup():
    creds = _get_db_credentials()
    try:
        import subprocess
        import platform
        if platform.system() == "Windows":
            command = f'"C:\\Program Files\\PostgreSQL\\18\\bin\\pg_dump.exe" -h {creds["host"]} -p {creds["port"]} -U {creds["user"]} -d {creds["name"]} --clean'
        else:
            command = f'pg_dump -h {creds["host"]} -p {creds["port"]} -U {creds["user"]} -d {creds["name"]} --clean'
        
        env = os.environ.copy()
        env["PGPASSWORD"] = creds["pass"]
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