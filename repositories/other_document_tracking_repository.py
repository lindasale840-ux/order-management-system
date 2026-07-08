import pandas as pd
import streamlit as st
from database.pg_database import query_pg_to_dataframe, execute_pg_query
from utils.datetime_utils import convert_utc_columns

class OtherDocumentTrackingRepository:

    @staticmethod
    @st.cache_data(ttl=30)
    def get_all():
        query = """
        SELECT *
        FROM other_document_tracking
        ORDER BY id DESC
        """
        df = query_pg_to_dataframe(query)
        return convert_utc_columns(df)

    @staticmethod
    def add_tracking(
        customer_name,
        document_type,
        sent_date,
        received_date,
        note,
        created_by,   
        sale_owner    
    ):
        query = """
        INSERT INTO other_document_tracking (
            customer_name,
            document_type,
            sent_date,
            received_date,
            note,
            created_by,   
            sale_owner   
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        params = (customer_name, document_type, sent_date, received_date, note, created_by, sale_owner)
        execute_pg_query(query, params)
        st.cache_data.clear()

    @staticmethod
    def delete_tracking(record_id):
        query = """
        DELETE FROM other_document_tracking
        WHERE id = %s
        """
        execute_pg_query(query, (record_id,))
        st.cache_data.clear()
        
    # === HÀM THÊM MỚI ĐỂ CẬP NHẬT NGÀY NHẬN HỒ SƠ AD-HOC ===
    @staticmethod
    def update_received_date(record_id, received_date):
        query = """
        UPDATE other_document_tracking
        SET received_date = %s
        WHERE id = %s
        """
        params = (received_date, record_id)
        execute_pg_query(query, params)
        st.cache_data.clear() # Xóa cache để giao diện tải lại data mới lập tức    