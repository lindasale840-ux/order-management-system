import pandas as pd
import streamlit as st
from database.pg_database import query_pg_to_dataframe, execute_pg_query
from utils.datetime_utils import convert_utc_columns

class DocumentAccountingRepository:

    @staticmethod
    @st.cache_data(ttl=15)
    def get_pending_send_to_accounting():
        """
        Lấy các đơn đã nhận từ khách hàng (received_date IS NOT NULL ở bảng cũ)
        nhưng CHƯA từng được tạo luồng gửi sang kế toán ở bảng mới.
        """
        query = """
        SELECT 
            dt.id AS document_tracking_id,
            dt.order_number,
            dt.received_date AS client_received_date,
            dt.note AS tracking_note,
            o.customer_name,
            o.sale_owner,
            o.created_by
        FROM document_tracking dt
        LEFT JOIN orders o ON dt.order_number = o.order_number
        LEFT JOIN document_accounting_flows daf ON dt.id = daf.document_tracking_id
        WHERE dt.received_date IS NOT NULL 
          AND daf.document_tracking_id IS NULL
        ORDER BY dt.id DESC
        """
        df = query_pg_to_dataframe(query)
        return convert_utc_columns(df)

    @staticmethod
    def batch_add_accounting_flow(records):
        """Thêm hàng loạt đơn gửi sang kế toán (Xử lý trong 1 Transaction ngầm)"""
        query = """
        INSERT INTO document_accounting_flows (
            document_tracking_id, order_number, sent_to_accounting_date, note, sale_owner, created_by
        ) VALUES (%s, %s, %s, %s, %s, %s)
        """
        for r in records:
            params = (
                r["document_tracking_id"], r["order_number"], 
                r["sent_to_accounting_date"], r["note"], 
                r["sale_owner"], r["created_by"]
            )
            execute_pg_query(query, params)
        st.cache_data.clear()

    @staticmethod
    @st.cache_data(ttl=15)
    def get_all_accounting_history():
        """Lấy toàn bộ lịch sử luồng kế toán phục vụ bảng theo dõi tổng hợp"""
        query = """
        SELECT 
            daf.*,
            o.customer_name,
            dt.received_date AS client_received_date
        FROM document_accounting_flows daf
        LEFT JOIN orders o ON daf.order_number = o.order_number
        LEFT JOIN document_tracking dt ON daf.document_tracking_id = dt.id
        ORDER BY daf.id DESC
        """
        df = query_pg_to_dataframe(query)
        return convert_utc_columns(df)

    @staticmethod
    def accountant_confirm_receive(flow_id, receive_date):
        """Phía kế toán tích xác nhận đã nhận tài liệu"""
        query = """
        UPDATE document_accounting_flows
        SET accounting_received_date = %s,
            is_received_by_accounting = TRUE,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """
        execute_pg_query(query, (receive_date, flow_id))
        st.cache_data.clear()