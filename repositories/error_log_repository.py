import pandas as pd
from database.pg_database import query_pg_to_dataframe, execute_pg_query
from utils.datetime_utils import convert_utc_columns


class ErrorLogRepository:

    @staticmethod
    @staticmethod
    def add_error(page_name, error_message):
        # 1. Thêm bản ghi lỗi mới
        query_insert = """
        INSERT INTO error_logs (
            page_name,
            error_message
        )
        VALUES (%s, %s)
        """
        params_insert = (page_name, error_message)
        execute_pg_query(query_insert, params_insert)

        # ========================================================
        # KEEP ONLY LAST 20 ERRORS - SỬA LẠI CHO POSTGRESQL
        # Dùng MIN() để đảm bảo subquery chỉ trả về đúng 1 giá trị số duy nhất
        # ========================================================
        query_purge = """
        DELETE FROM error_logs
        WHERE id < COALESCE((
            SELECT MIN(min_id) FROM (
                SELECT id AS min_id 
                FROM error_logs 
                ORDER BY id DESC 
                LIMIT 20
            ) as tmp
        ), 0);
        """
        execute_pg_query(query_purge)

    @staticmethod
    def get_errors():
        query = """
        SELECT *
        FROM error_logs
        ORDER BY id DESC
        """
        df = query_pg_to_dataframe(query)
        return convert_utc_columns(df)

    @staticmethod
    def delete_all_errors():
        query = "DELETE FROM error_logs"
        execute_pg_query(query)