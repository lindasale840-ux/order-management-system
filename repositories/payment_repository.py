import pandas as pd
import streamlit as st
from database.pg_database import query_pg_to_dataframe, execute_pg_query
from utils.datetime_utils import convert_utc_columns

class PaymentRepository:

    @staticmethod
    @st.cache_data(ttl=30)
    def get_all_payments():
        query = """
        SELECT *
        FROM payments
        ORDER BY id DESC
        """
        df = query_pg_to_dataframe(query)
        return convert_utc_columns(df)

    @staticmethod
    def upsert_payment(
        order_number,
        invoice_date,
        invoice_group,
        payment_terms,
        payment_status,
        total,
        commission_percent,
        commission_actual,
        note,
        invoice_created_by
    ):
        # Chuyển đổi tên biến từ :name sang %s. Cú pháp ON CONFLICT giữ nguyên.
        query = """
        INSERT INTO payments (
            order_number,
            invoice_date,
            invoice_group,             
            payment_terms,
            payment_status,
            total,
            commission_percent,
            commission_actual,
            note,
            invoice_created_by
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT(order_number)
        DO UPDATE SET
            invoice_date = EXCLUDED.invoice_date,
            invoice_group = EXCLUDED.invoice_group,              
            payment_terms = EXCLUDED.payment_terms,
            payment_status = EXCLUDED.payment_status,
            total = EXCLUDED.total,
            commission_percent = EXCLUDED.commission_percent,
            commission_actual = EXCLUDED.commission_actual,
            note = EXCLUDED.note,
            invoice_created_by = EXCLUDED.invoice_created_by,
            updated_at = CURRENT_TIMESTAMP
        """
        
        params = (
            order_number, invoice_date, invoice_group, payment_terms, 
            payment_status, total, commission_percent, commission_actual, 
            note, invoice_created_by
        )
        execute_pg_query(query, params)
        st.cache_data.clear()
        
    @staticmethod
    def bulk_transfer_invoice_owner(old_owner, new_owner):
        query = """
        UPDATE payments
        SET invoice_created_by = %s
        WHERE invoice_created_by = %s
        """
        execute_pg_query(query, (new_owner, old_owner))
        st.cache_data.clear()  
        
    @staticmethod
    def transfer_invoice_owner_by_orders(order_numbers, new_assistant):
        if not order_numbers:
            return

        # PostgreSQL sử dụng %s làm placeholder
        placeholders = ",".join(["%s"] * len(order_numbers))
        
        query = f"""
        UPDATE payments
        SET invoice_created_by = %s
        WHERE order_number IN ({placeholders})
        """
        
        # Tạo tuple tham số: Biến new_assistant đứng đầu, sau đó unpack toàn bộ danh sách order_numbers ra phía sau
        params = (new_assistant, *order_numbers)

        execute_pg_query(query, params)
        st.cache_data.clear()