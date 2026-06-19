import pandas as pd
import streamlit as st
from sqlalchemy import text
from database.connection import engine
from utils.datetime_utils import convert_utc_columns

class OrderRepository:

    @staticmethod
    def init_payment_notification_column():
        """Tự động kiểm tra và thêm cột disable_payment_notification nếu database chưa có"""
        query = "ALTER TABLE orders ADD COLUMN disable_payment_notification INTEGER DEFAULT 0;"
        with engine.begin() as conn:
            try:
                conn.execute(text(query))
            except Exception:
                pass # Cột đã tồn tại hoặc bảng trống, bỏ qua

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
        df = pd.read_sql(query, engine)
        return convert_utc_columns(df)

    @staticmethod
    @st.cache_data(ttl=30)
    def get_customers():
        query = """
        SELECT DISTINCT customer_name
        FROM orders
        ORDER BY customer_name
        """
        return pd.read_sql(query, engine)

    @staticmethod
    @st.cache_data(ttl=30)
    def get_orders_by_customer(customer_name):
        OrderRepository.init_payment_notification_column()
        query = """
        SELECT *
        FROM orders
        WHERE customer_name = :customer_name
        AND is_deleted = 0
        ORDER BY id DESC
        """
        df = pd.read_sql(text(query), engine, params={"customer_name": customer_name})
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
        disable_payment_notification=0  # Tham số mới bổ sung
    ):
        OrderRepository.init_payment_notification_column()
        with engine.begin() as conn:
            conn.execute(text("""
            INSERT INTO orders (
                customer_name, order_number, measurement_date, cert_status,               
                sale_owner, created_by, disable_calibration_notification, 
                disable_document_notification, disable_payment_notification              
            )
            VALUES (
                :customer_name, :order_number, :measurement_date, :cert_status,               
                :sale_owner, :created_by, :disable_calibration_notification, 
                :disable_document_notification, :disable_payment_notification              
            )
            ON CONFLICT(order_number)
            DO UPDATE SET
                customer_name=excluded.customer_name,
                measurement_date=excluded.measurement_date,
                cert_status=excluded.cert_status,              
                sale_owner=excluded.sale_owner,
                created_by=excluded.created_by,
                disable_calibration_notification=excluded.disable_calibration_notification,
                disable_document_notification=excluded.disable_document_notification,
                disable_payment_notification=excluded.disable_payment_notification,              
                updated_at=CURRENT_TIMESTAMP
            """),
            {
                "customer_name": customer_name,
                "order_number": order_number,
                "measurement_date": measurement_date,
                "cert_status": cert_status,
                "sale_owner": sale_owner,
                "created_by": created_by,
                "disable_calibration_notification": disable_calibration_notification,
                "disable_document_notification": disable_document_notification,
                "disable_payment_notification": disable_payment_notification
            })
        st.cache_data.clear()

    @staticmethod
    def delete_order_cascade(order_number):
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM payments WHERE order_number = :order_number"), {"order_number": order_number})
            conn.execute(text("DELETE FROM document_tracking WHERE order_number = :order_number"), {"order_number": order_number})
            conn.execute(text("DELETE FROM orders WHERE order_number = :order_number"), {"order_number": order_number})
        st.cache_data.clear()

    @staticmethod
    def update_invoice_group(order_number, invoice_group):
        with engine.begin() as conn:
            conn.execute(text("""
                UPDATE orders SET invoice_group = :invoice_group WHERE order_number = :order_number
            """), {"invoice_group": invoice_group, "order_number": order_number})
        st.cache_data.clear()

    @staticmethod
    def soft_delete_order(order_number, deleted_by):
        with engine.begin() as conn:
            conn.execute(text("""
                UPDATE orders SET is_deleted = 1, deleted_at = CURRENT_TIMESTAMP, deleted_by = :deleted_by WHERE order_number = :order_number
            """), {"order_number": order_number, "deleted_by": deleted_by})
        st.cache_data.clear()   

    @staticmethod
    @st.cache_data(ttl=30)
    def get_deleted_orders():
        OrderRepository.init_payment_notification_column()
        query = "SELECT * FROM orders WHERE is_deleted = 1 ORDER BY deleted_at DESC"
        df = pd.read_sql(query, engine)
        return convert_utc_columns(df)  

    @staticmethod
    def restore_order(order_number):
        with engine.begin() as conn:
            conn.execute(text("""
                UPDATE orders SET is_deleted = 0, deleted_at = NULL, deleted_by = NULL WHERE order_number = :order_number
            """), {"order_number": order_number})
        st.cache_data.clear()   
        
    @staticmethod
    def bulk_transfer_sale_owner(old_owner, new_owner):
        with engine.begin() as conn:
            conn.execute(text("""
                UPDATE orders SET sale_owner = :new_owner WHERE sale_owner = :old_owner
            """), {"old_owner": old_owner, "new_owner": new_owner})
        st.cache_data.clear()    

    @staticmethod
    def transfer_sale_owner_by_orders(order_numbers, new_sale):
        if not order_numbers: return
        placeholders = ",".join([f":p{i}" for i in range(len(order_numbers))])
        params = {f"p{i}": order_numbers[i] for i in range(len(order_numbers))}
        params["new_sale"] = new_sale
        with engine.begin() as conn:
            conn.execute(text(f"UPDATE orders SET sale_owner = :new_sale WHERE order_number IN ({placeholders})"), params)
        st.cache_data.clear()
        
    @staticmethod
    def get_by_order_number(order_number):
        OrderRepository.init_payment_notification_column()
        query = "SELECT * FROM orders WHERE order_number = :order_number LIMIT 1"
        df = pd.read_sql(text(query), engine, params={"order_number": order_number})
        return df