import pandas as pd
import streamlit as st
from database.pg_database import query_pg_to_dataframe, execute_pg_query
from utils.datetime_utils import convert_utc_columns

class OrderRepository:

    @staticmethod
    def init_payment_notification_column():
        """Tự động kiểm tra và thêm cột disable_payment_notification nếu database chưa có"""
        # Postgres sử dụng kiểu dữ liệu INTEGER hoặc SMALLINT. Ta đồng bộ INTEGER giống SQLite cũ.
        query = "ALTER TABLE orders ADD COLUMN IF NOT EXISTS disable_payment_notification INTEGER DEFAULT 0;"
        try:
            execute_pg_query(query)
        except Exception:
            pass  # Cột đã tồn tại hoặc bảng chưa tạo, bỏ qua để hệ thống không crash

    @staticmethod
    @st.cache_data(ttl=30)
    def get_all_orders():
        OrderRepository.init_payment_notification_column()
        query = """
        SELECT *
        FROM orders
        WHERE is_deleted = 0
        ORDER BY id DESC
        """
        df = query_pg_to_dataframe(query)
        return convert_utc_columns(df)

    @staticmethod
    @st.cache_data(ttl=30)
    def get_customers():
        query = """
        SELECT DISTINCT customer_name
        FROM orders
        ORDER BY customer_name
        """
        return query_pg_to_dataframe(query)

    @staticmethod
    @st.cache_data(ttl=30)
    def get_orders_by_customer(customer_name):
        OrderRepository.init_payment_notification_column()
        query = """
        SELECT *
        FROM orders
        WHERE customer_name = %s
        AND is_deleted = 0
        ORDER BY id DESC
        """
        df = query_pg_to_dataframe(query, (customer_name,))
        return convert_utc_columns(df)

    @staticmethod
    def upsert_order(
        customer_name,
        order_number,
        measurement_date,
        cert_status,
        sale_owner,
        created_by,
        disable_calibration_notification=0,
        disable_document_notification=0,
        disable_payment_notification=0  
    ):
        OrderRepository.init_payment_notification_column()
        query = """
        INSERT INTO orders (
            customer_name, order_number, measurement_date, cert_status,               
            sale_owner, created_by, disable_calibration_notification, 
            disable_document_notification, disable_payment_notification              
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT(order_number)
        DO UPDATE SET
            customer_name = EXCLUDED.customer_name,
            measurement_date = EXCLUDED.measurement_date,
            cert_status = EXCLUDED.cert_status,              
            sale_owner = EXCLUDED.sale_owner,
            created_by = EXCLUDED.created_by,
            disable_calibration_notification = EXCLUDED.disable_calibration_notification,
            disable_document_notification = EXCLUDED.disable_document_notification,
            disable_payment_notification = EXCLUDED.disable_payment_notification,              
            updated_at = CURRENT_TIMESTAMP
        """
        
        params = (
            customer_name, order_number, measurement_date, cert_status,
            sale_owner, created_by, disable_calibration_notification,
            disable_document_notification, disable_payment_notification
        )
        execute_pg_query(query, params)
        st.cache_data.clear()

    @staticmethod
    def delete_order_cascade(order_number):
        # Tách biệt rõ ràng các lệnh thực thi độc lập
        execute_pg_query("DELETE FROM payments WHERE order_number = %s", (order_number,))
        execute_pg_query("DELETE FROM document_tracking WHERE order_number = %s", (order_number,))
        execute_pg_query("DELETE FROM orders WHERE order_number = %s", (order_number,))
        st.cache_data.clear()

    @staticmethod
    def update_invoice_group(order_number, invoice_group):
        query = "UPDATE orders SET invoice_group = %s WHERE order_number = %s"
        execute_pg_query(query, (invoice_group, order_number))
        st.cache_data.clear()

    @staticmethod
    def soft_delete_order(order_number, deleted_by):
        query = """
        UPDATE orders 
        SET is_deleted = 1, deleted_at = CURRENT_TIMESTAMP, deleted_by = %s 
        WHERE order_number = %s
        """
        execute_pg_query(query, (deleted_by, order_number))
        st.cache_data.clear()   

    @staticmethod
    @st.cache_data(ttl=30)
    def get_deleted_orders():
        OrderRepository.init_payment_notification_column()
        query = "SELECT * FROM orders WHERE is_deleted = 1 ORDER BY deleted_at DESC"
        df = query_pg_to_dataframe(query)
        return convert_utc_columns(df)  

    @staticmethod
    def restore_order(order_number):
        query = """
        UPDATE orders 
        SET is_deleted = 0, deleted_at = NULL, deleted_by = NULL 
        WHERE order_number = %s
        """
        execute_pg_query(query, (order_number,))
        st.cache_data.clear()   
        
    @staticmethod
    def bulk_transfer_sale_owner(old_owner, new_owner):
        query = "UPDATE orders SET sale_owner = %s WHERE sale_owner = %s"
        execute_pg_query(query, (new_owner, old_owner))
        st.cache_data.clear()    

    @staticmethod
    def transfer_sale_owner_by_orders(order_numbers, new_sale):
        if not order_numbers: 
            return
        placeholders = ",".join(["%s"] * len(order_numbers))
        query = f"UPDATE orders SET sale_owner = %s WHERE order_number IN ({placeholders})"
        params = (new_sale, *order_numbers)
        execute_pg_query(query, params)
        st.cache_data.clear()
        
    @staticmethod
    def get_by_order_number(order_number):
        OrderRepository.init_payment_notification_column()
        query = "SELECT * FROM orders WHERE order_number = %s LIMIT 1"
        return query_pg_to_dataframe(query, (order_number,))