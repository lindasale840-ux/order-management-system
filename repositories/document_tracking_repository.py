import pandas as pd
import streamlit as st
from database.pg_database import query_pg_to_dataframe, execute_pg_query
from utils.datetime_utils import convert_utc_columns


class DocumentTrackingRepository:

    @staticmethod
    @st.cache_data(ttl=30)
    def get_all():
        query = """
        SELECT
            dt.*,
            o.customer_name,
            o.created_by,
            o.sale_owner
        FROM document_tracking dt
        LEFT JOIN orders o ON dt.order_number = o.order_number
        ORDER BY dt.id DESC
        """
        df = query_pg_to_dataframe(query)
        df = convert_utc_columns(df)
        # Thay thế toàn bộ NaT / NaN thành None để Streamlit không bị lỗi
        return convert_utc_columns(df)

    @staticmethod
    def add_tracking(order_number, sent_date, received_date, note):
        query = """
        INSERT INTO document_tracking (
            order_number, sent_date, received_date, note
        )
        VALUES (%s, %s, %s, %s)
        """
        params = (order_number, sent_date, received_date, note)
        execute_pg_query(query, params)
        st.cache_data.clear()

    @staticmethod
    def delete_tracking(tracking_id):
        query = """
        DELETE FROM document_tracking
        WHERE id = %s
        """
        execute_pg_query(query, (tracking_id,))
        st.cache_data.clear()
        
    @staticmethod
    @st.cache_data(ttl=30)
    def get_pending_return():
        query = """
        SELECT *
        FROM document_tracking
        WHERE received_date IS NULL
        ORDER BY id DESC
        """
        df = query_pg_to_dataframe(query)
        df = convert_utc_columns(df)
        return convert_utc_columns(df)
    
    @staticmethod
    @st.cache_data(ttl=30)
    def get_latest_tracking():
        query = """
        SELECT
            dt.*,
            o.customer_name,
            o.created_by,
            o.sale_owner
        FROM document_tracking dt
        LEFT JOIN orders o ON dt.order_number = o.order_number
        WHERE dt.id IN (
            SELECT MAX(id)
            FROM document_tracking
            GROUP BY order_number
        )
        ORDER BY dt.id DESC
        """
        df = query_pg_to_dataframe(query)
        df = convert_utc_columns(df)
        return convert_utc_columns(df)
    
    @staticmethod
    @st.cache_data(ttl=30)
    def get_latest_by_order(order_number):
        query = """
        SELECT *
        FROM document_tracking
        WHERE order_number = %s
        ORDER BY id DESC
        LIMIT 1
        """
        df = query_pg_to_dataframe(query, (order_number,))
        df = convert_utc_columns(df)
        return convert_utc_columns(df)
    
    @staticmethod
    @st.cache_data(ttl=30)
    def get_by_order(order_number):
        query = """
        SELECT *
        FROM document_tracking
        WHERE order_number = %s
        ORDER BY id DESC
        """
        df = query_pg_to_dataframe(query, (order_number,))
        df = convert_utc_columns(df)
        return convert_utc_columns(df)