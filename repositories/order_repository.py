import pandas as pd
import streamlit as st

from sqlalchemy import text

from database.connection import engine


class OrderRepository:

    # =========================
    # GET ALL ORDERS
    # =========================

    @staticmethod
    @st.cache_data(ttl=30)

    def get_all_orders():

        query = """

        SELECT *

        FROM orders

        ORDER BY id DESC

        """

        return pd.read_sql(
            query,
            engine
        )

    # =========================
    # GET CUSTOMERS
    # =========================

    @staticmethod
    @st.cache_data(ttl=30)

    def get_customers():

        query = """

        SELECT DISTINCT customer_name

        FROM orders

        ORDER BY customer_name

        """

        return pd.read_sql(
            query,
            engine
        )

    # =========================
    # GET ORDERS BY CUSTOMER
    # =========================

    @staticmethod
    @st.cache_data(ttl=30)

    def get_orders_by_customer(
        customer_name
    ):

        query = """

        SELECT *

        FROM orders

        WHERE customer_name = :customer_name

        ORDER BY id DESC

        """

        return pd.read_sql(

            text(query),

            engine,

            params={
                "customer_name": customer_name
            }
        )

    # =========================
    # UPSERT ORDER
    # =========================

    @staticmethod
    def upsert_order(

        customer_name,

        order_number,

        measurement_date,

        cert_status,

        sale_owner
    ):

        with engine.begin() as conn:

            conn.execute(text("""

            INSERT INTO orders (

                customer_name,

                order_number,

                measurement_date,

                cert_status,
                              
                sale_owner                

            )

            VALUES (

                :customer_name,

                :order_number,

                :measurement_date,

                :cert_status,
                              
                :sale_owner                
            )

            ON CONFLICT(order_number)

            DO UPDATE SET

                customer_name=excluded.customer_name,

                measurement_date=excluded.measurement_date,

                cert_status=excluded.cert_status,
                              
                sale_owner=excluded.sale_owner,              

                updated_at=CURRENT_TIMESTAMP

            """),

            {

                "customer_name": customer_name,

                "order_number": order_number,

                "measurement_date": measurement_date,

                "cert_status": cert_status,

                "sale_owner": sale_owner
            })

        # =========================
        # CLEAR CACHE
        # =========================

        st.cache_data.clear()

    # =========================
    # DELETE ORDER
    # =========================
    @staticmethod
    def delete_order_cascade(
        order_number
    ):

        with engine.begin() as conn:

            conn.execute(
                text("""
                DELETE FROM payments
                WHERE order_number = :order_number
                """),
                {
                    "order_number": order_number
                }
            )

            conn.execute(
                text("""
                DELETE FROM document_tracking
                WHERE order_number = :order_number
                """),
                {
                    "order_number": order_number
                }
            )

            conn.execute(
                text("""
                DELETE FROM orders
                WHERE order_number = :order_number
                """),
                {
                    "order_number": order_number
                }
            )

        st.cache_data.clear()