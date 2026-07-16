import pandas as pd
from database.pg_database import query_pg_to_dataframe, execute_pg_query
from datetime import datetime
class DocumentArchiveRepository:
    
    @staticmethod
    def get_all_archives():
        """Lấy toàn bộ hồ sơ trong kho lưu trữ"""
        query = """
            SELECT id, order_number, customer_name, customer_code, 
                   document_type, file_type, file_path, archive_date, created_by, note
            FROM document_archives
            ORDER BY created_at DESC
        """
        return query_pg_to_dataframe(query)

    @staticmethod
    def add_archive_entry(order_number, customer_name, customer_code, document_type, file_type, file_path, note, username):
        """[ĐÃ FIX TRUYỀN NGÀY TỰ ĐỘNG] Thêm mới thủ công hoặc tự động một hồ sơ lưu trữ"""
        query = """
            INSERT INTO document_archives 
            (order_number, customer_name, customer_code, document_type, file_type, file_path, note, created_by, archive_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        now = datetime.now() # Đảm bảo lấy cả Giờ : Phút : Giây thực tế
        execute_pg_query(query, (
            order_number, customer_name, customer_code, 
            document_type, file_type, file_path, note, username, now
        ))