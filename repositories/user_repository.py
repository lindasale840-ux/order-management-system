import pandas as pd
from sqlalchemy import text
from database.connection import engine

class UserRepository:
    
    @staticmethod
    def init_security_columns():
        """Tự động kiểm tra và thêm các cột bảo mật nếu database chưa có"""
        queries = [
            "ALTER TABLE users ADD COLUMN login_attempts INTEGER DEFAULT 0;",
            "ALTER TABLE users ADD COLUMN locked_until TEXT;",
            "ALTER TABLE users ADD COLUMN reset_requested INTEGER DEFAULT 0;"
        ]
        with engine.begin() as conn:
            for q in queries:
                try:
                    conn.execute(text(q))
                except Exception:
                    pass # Cột đã tồn tại, bỏ qua

    @staticmethod
    def get_all_users():
        UserRepository.init_security_columns()
        query = "SELECT * FROM users ORDER BY username"
        return pd.read_sql(query, engine)

    @staticmethod
    def get_user_by_username(username):
        UserRepository.init_security_columns()
        query = text("""
            SELECT * FROM users WHERE username = :username LIMIT 1
        """)
        with engine.begin() as conn:
            result = conn.execute(query, {"username": username}).mappings().first()
            return result

    @staticmethod
    def create_user(username, password_hash, role, sale_owner):
        UserRepository.init_security_columns()
        query = text("""
        INSERT INTO users (username, password_hash, role, sale_owner, login_attempts, reset_requested)
        VALUES (:username, :password_hash, :role, :sale_owner, 0, 0)
        """)
        with engine.begin() as conn:
            conn.execute(query, {
                "username": username,
                "password_hash": password_hash,
                "role": role,
                "sale_owner": sale_owner
            })

    @staticmethod
    def delete_user(username):
        query = text("DELETE FROM users WHERE username = :username")
        with engine.begin() as conn:
            conn.execute(query, {"username": username})

    # =========================================================
    # CÁC HÀM BẢO MẬT MỚI THÊM VÀO
    # =========================================================
    @staticmethod
    def update_login_attempts(username, attempts):
        query = text("UPDATE users SET login_attempts = :attempts WHERE username = :username")
        with engine.begin() as conn:
            conn.execute(query, {"attempts": attempts, "username": username})

    @staticmethod
    def lock_user(username, lock_time_str):
        query = text("UPDATE users SET locked_until = :lock_time WHERE username = :username")
        with engine.begin() as conn:
            conn.execute(query, {"lock_time": lock_time_str, "username": username})

    @staticmethod
    def reset_security_status(username):
        """Mở khóa và reset số lần sai về 0"""
        query = text("""
            UPDATE users 
            SET login_attempts = 0, locked_until = NULL, reset_requested = 0 
            WHERE username = :username
        """)
        with engine.begin() as conn:
            conn.execute(query, {"username": username})

    @staticmethod
    def request_password_reset(username):
        query = text("UPDATE users SET reset_requested = 1 WHERE username = :username")
        with engine.begin() as conn:
            conn.execute(query, {"username": username})

    @staticmethod
    def update_password(username, new_password_hash):
        query = text("""
            UPDATE users 
            SET password_hash = :password_hash, login_attempts = 0, locked_until = NULL, reset_requested = 0 
            WHERE username = :username
        """)
        with engine.begin() as conn:
            conn.execute(query, {"password_hash": new_password_hash, "username": username})