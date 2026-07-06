import pandas as pd
from database.pg_database import query_pg_to_dataframe, execute_pg_query, get_pg_connection
from datetime import datetime  # <-- THÊM DÒNG NÀY Ở ĐẦU FILE

class UserRepository:
    
    @staticmethod
    def init_security_columns():
        """Tự động kiểm tra và thêm các cột bảo mật nếu database chưa có"""
        # Lưu ý: Postgres cần kiểm tra lỗi chi tiết để bỏ qua trường hợp cột đã tồn tại
        queries = [
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS login_attempts INTEGER DEFAULT 0;",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS locked_until TEXT;",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_requested INTEGER DEFAULT 0;"
        ]
        for q in queries:
            try:
                execute_pg_query(q)
            except Exception:
                pass # Cột đã tồn tại, bỏ qua

    @staticmethod
    def get_all_users():
        UserRepository.init_security_columns()
        query = "SELECT * FROM users ORDER BY username"
        return query_pg_to_dataframe(query)

    @staticmethod
    def get_user_by_username(username):
        UserRepository.init_security_columns()
        query = "SELECT * FROM users WHERE username = %s LIMIT 1"
        
        # Vì hàm cũ cần trả về một cấu trúc dạng Dict/Mapping để tầng ngoài chấm đọc (ví dụ: user['role'])
        # Chúng ta sẽ mở kết nối trực tiếp sử dụng RealDictCursor đã viết ngầm trong file pg_database
        from psycopg2.extras import RealDictCursor
        conn = get_pg_connection()
        if not conn:
            return None
        try:
            # RealDictCursor giúp kết quả trả về tự động biến thành Dict
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, (username,))
                result = cursor.fetchone()
                return result # Trả về dict hoặc None, y hệt .mappings().first() cũ!
        except Exception as e:
            print(f"❌ Lỗi lấy thông tin user: {e}")
            return None
        finally:
            conn.close()

    @staticmethod
    def create_user(username, password_hash, role, sale_owner):
        UserRepository.init_security_columns()
        # 1. Tự sinh thời gian hiện tại từ phía Python
        current_time = datetime.now()
        query = """
        INSERT INTO users (username, password_hash, role, sale_owner, login_attempts, reset_requested, created_at)
        VALUES (%s, %s, %s, %s, 0, 0, %s)
        """
        # 3. Truyền biến current_time vào tuple tham số
        execute_pg_query(query, (username, password_hash, role, sale_owner, current_time))

    @staticmethod
    def delete_user(username):
        query = "DELETE FROM users WHERE username = %s"
        execute_pg_query(query, (username,))

    # =========================================================
    # CÁC HÀM BẢO MẬT MỚI THÊM VÀO
    # =========================================================
    @staticmethod
    def update_login_attempts(username, attempts):
        query = "UPDATE users SET login_attempts = %s WHERE username = %s"
        execute_pg_query(query, (attempts, username))

    @staticmethod
    def lock_user(username, lock_time_str):
        query = "UPDATE users SET locked_until = %s WHERE username = %s"
        execute_pg_query(query, (lock_time_str, username))

    @staticmethod
    def reset_security_status(username):
        """Mở khóa và reset số lần sai về 0"""
        query = """
        UPDATE users 
        SET login_attempts = 0, locked_until = NULL, reset_requested = 0 
        WHERE username = %s
        """
        execute_pg_query(query, (username,))

    @staticmethod
    def request_password_reset(username):
        query = "UPDATE users SET reset_requested = 1 WHERE username = %s"
        execute_pg_query(query, (username,))

    @staticmethod
    def update_password(username, new_password_hash):
        query = """
        UPDATE users 
        SET password_hash = %s, login_attempts = 0, locked_until = NULL, reset_requested = 0 
        WHERE username = %s
        """
        execute_pg_query(query, (new_password_hash, username))