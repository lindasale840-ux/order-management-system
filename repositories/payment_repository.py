import pandas as pd
import streamlit as st

from sqlalchemy import text

from database.connection import engine


class PaymentRepository:

    @staticmethod
    def upsert_payment(
        order_number,
        invoice_date,
        payment_terms,
        payment_status,
        total,
        commission_percent,
        commission_actual,
        note
    ):

        query = text("""
        INSERT INTO payments (
            order_number,
            invoice_date,
            payment_terms,
            payment_status,
            total,
            commission_percent,
            commission_actual,
            note
        )

        VALUES (
            :order_number,
            :invoice_date,
            :payment_terms,
            :payment_status,
            :total,
            :commission_percent,
            :commission_actual,
            :note
        )

        ON CONFLICT(order_number)

        DO UPDATE SET

            invoice_date=excluded.invoice_date,
            payment_terms=excluded.payment_terms,
            payment_status=excluded.payment_status,
            total=excluded.total,
            commission_percent=excluded.commission_percent,
            commission_actual=excluded.commission_actual,
            note=excluded.note,
            updated_at=CURRENT_TIMESTAMP
        """)

        with engine.begin() as conn:

            conn.execute(query, {

                "order_number": order_number,
                "invoice_date": invoice_date,
                "payment_terms": payment_terms,
                "payment_status": payment_status,
                "total": total,
                "commission_percent": commission_percent,
                "commission_actual": commission_actual,
                "note": note
            })

        st.cache_data.clear()

    @staticmethod
    @st.cache_data(ttl=30)
    def get_all_payments():

        query = """
        SELECT *
        FROM payments
        ORDER BY id DESC
        """

        return pd.read_sql(query, engine)