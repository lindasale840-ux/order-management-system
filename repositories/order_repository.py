import pandas as pd
import streamlit as st

from sqlalchemy import text

from database.connection import engine


class OrderRepository:

    @staticmethod
    def upsert_order(
        customer_name,
        order_number,
        measurement_date,
        cert_status
    ):

        query = text("""
        INSERT INTO orders (
            customer_name,
            order_number,
            measurement_date,
            cert_status
        )

        VALUES (
            :customer_name,
            :order_number,
            :measurement_date,
            :cert_status
        )

        ON CONFLICT(order_number)

        DO UPDATE SET

            customer_name=excluded.customer_name,
            measurement_date=excluded.measurement_date,
            cert_status=excluded.cert_status,
            updated_at=CURRENT_TIMESTAMP
        """)

        with engine.begin() as conn:

            conn.execute(query, {

                "customer_name": customer_name,
                "order_number": order_number,
                "measurement_date": measurement_date,
                "cert_status": cert_status
            })

        st.cache_data.clear()

    @staticmethod
    @st.cache_data(ttl=30)
    def get_all_orders():

        query = """
        SELECT *
        FROM orders
        ORDER BY id DESC
        """

        return pd.read_sql(query, engine)

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
    def get_orders_by_customer(customers):

        if not customers:
            return pd.DataFrame()

        placeholders = ",".join(
            [f"'{c}'" for c in customers]
        )

        query = f"""
        SELECT *
        FROM orders
        WHERE customer_name IN ({placeholders})
        ORDER BY id DESC
        """

        return pd.read_sql(query, engine)