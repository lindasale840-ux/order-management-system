import pandas as pd
import streamlit as st
from database.pg_database import query_pg_to_dataframe, execute_pg_query
from utils.datetime_utils import convert_utc_columns

class LogRepository:

    MAX_LOG_ROWS = 5000

    @staticmethod
    def add_log(
        action,
        customer_name,
        order_number,
        description,
        username="SYSTEM"
    ):
        # Lấy username từ session_state của Streamlit nếu có
        username = st.session_state.get("username", username)

        query_insert = """
        INSERT INTO logs (
            username, action, customer_name, order_number, description
        )
        VALUES (%s, %s, %s, %s, %s)
        """
        
        params_insert = (username, action, customer_name, order_number, description)
        execute_pg_query(query_insert, params_insert)

        # ========================================================
        # AUTO PURGE - PHIÊN BẢN TỐI ƯU CHO POSTGRESQL
        # Giữ lại 5000 dòng mới nhất bằng cách xóa các dòng có id 
        # nhỏ hơn id nhỏ nhất của top 5000 dòng đầu tiên.
        # ========================================================
        query_purge = f"""
        DELETE FROM logs
        WHERE id < COALESCE((
            SELECT min_id FROM (
                SELECT id AS min_id 
                FROM logs 
                ORDER BY id DESC 
                LIMIT {LogRepository.MAX_LOG_ROWS}
            ) as tmp
        ), 0);
        """
        execute_pg_query(query_purge)

    @staticmethod
    def get_logs():
        query = """
        SELECT *
        FROM logs
        ORDER BY id DESC
        """
        df = query_pg_to_dataframe(query)
        return convert_utc_columns(df)

    @staticmethod
    def delete_all_logs():
        query = "DELETE FROM logs"
        execute_pg_query(query)

    @staticmethod
    def get_log_count():
        query = "SELECT COUNT(*) as count FROM logs"
        df = query_pg_to_dataframe(query)
        if not df.empty:
            return int(df.iloc[0]['count'])
        return 0