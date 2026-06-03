import pandas as pd
import streamlit as st

from sqlalchemy import text

from database.connection import engine


class PaymentRepository:

    @staticmethod
    @st.cache_data(ttl=30)

    def get_all_payments():

        query = """

        SELECT *

        FROM payments

        ORDER BY id DESC

        """

        return pd.read_sql(
            query,
            engine
        )

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

        note
    ):

        with engine.begin() as conn:

            conn.execute(text("""

            INSERT INTO payments (

                order_number,

                invoice_date,
                              
                invoice_group,              

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
                              
                :invoice_group,             

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
                              
                invoice_group=excluded.invoice_group,              

                payment_terms=excluded.payment_terms,

                payment_status=excluded.payment_status,

                total=excluded.total,

                commission_percent=excluded.commission_percent,

                commission_actual=excluded.commission_actual,

                note=excluded.note,

                updated_at=CURRENT_TIMESTAMP

            """),

            {

                "order_number": order_number,

                "invoice_date": invoice_date,

                "invoice_group": invoice_group,

                "payment_terms": payment_terms,

                "payment_status": payment_status,

                "total": total,

                "commission_percent": commission_percent,

                "commission_actual": commission_actual,

                "note": note
            })

        st.cache_data.clear()