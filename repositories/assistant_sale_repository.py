import pandas as pd
# Import 2 hàm tiện ích thần thánh từ file cấu hình của bạn
from database.pg_database import query_pg_to_dataframe, execute_pg_query

class AssistantSaleRepository:

    @staticmethod
    def get_sales_by_assistant(assistant_username):
        # Đổi tham số định danh :name thành %s của Postgres
        query = """
        SELECT sale_owner
        FROM assistant_sale_mapping
        WHERE assistant_username = %s
        """
        # Gọi hàm chuyên đọc Dataframe, truyền tuple tham số vào
        df = query_pg_to_dataframe(query, params=(assistant_username,))

        if df.empty:
            return []

        # Giữ nguyên logic xử lý dữ liệu đầu ra của bạn
        return df["sale_owner"].astype(str).tolist()

    @staticmethod
    def delete_by_assistant(assistant_username):
        query = """
        DELETE FROM assistant_sale_mapping
        WHERE assistant_username = %s
        """
        # Gọi hàm chuyên Thêm/Sửa/Xóa, không cần mở/đóng connection bằng tay nữa
        execute_pg_query(query, params=(assistant_username,))

    @staticmethod
    def add_mapping(assistant_username, sale_owner):
        # LƯU Ý QUAN TRỌNG: Postgres không có "INSERT OR IGNORE" mà dùng cú pháp chuẩn quốc tế:
        # "ON CONFLICT DO NOTHING" (Với điều kiện bảng phải có khóa chính hoặc UNIQUE constraint)
        query = """
        INSERT INTO assistant_sale_mapping (assistant_username, sale_owner)
        VALUES (%s, %s)
        ON CONFLICT DO NOTHING
        """
        execute_pg_query(query, params=(assistant_username, sale_owner))

    @staticmethod
    def get_all():
        query = """
        SELECT *
        FROM assistant_sale_mapping
        ORDER BY assistant_username, sale_owner
        """
        # Trả về trực tiếp một Dataframe hoàn chỉnh cho tầng giao diện dùng
        return query_pg_to_dataframe(query)