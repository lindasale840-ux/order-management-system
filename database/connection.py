import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv  # <-- THÊM DÒNG NÀY
load_dotenv()  # <-- THÊM DÒNG NÀY ĐỂ ĐỌC FILE .env
# 1. Tự động đọc DATABASE_URL từ môi trường hệ thống (.env), nếu không thấy sẽ fallback về SQLite cũ để không làm sập app
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///database/app.db")
print(f"DEBUG: Đang kết nối tới: {DATABASE_URL}")

# 2. Cấu hình connect_args riêng biệt (vì check_same_thread chỉ dành cho SQLite)
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False
    connect_args["timeout"] = 30

# 3. Khởi tạo Engine
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# 4. Chỉ kích hoạt PRAGMA tối ưu nếu DB thực sự là SQLite
@event.listens_for(engine, "connect")
def configure_connection(dbapi_connection, connection_record):
    # Kiểm tra xem engine hiện tại có phải là SQLite hay không thông qua tên dialect
    if engine.dialect.name == "sqlite":
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()