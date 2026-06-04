import pandas as pd
import streamlit as st

from sqlalchemy import text

from database.connection import engine


class DocumentTrackingRepository:

    @staticmethod
    @st.cache_data(ttl=30)
    def get_all():

        query = """

        SELECT

            dt.*,

            o.customer_name

        FROM document_tracking dt

        LEFT JOIN orders o

            ON dt.order_number = o.order_number

        ORDER BY dt.id DESC

        """

        return pd.read_sql(
            query,
            engine
        )

    @staticmethod
    def add_tracking(

        order_number,

        sent_date,

        received_date,

        note

    ):

        with engine.begin() as conn:

            conn.execute(

                text("""

                INSERT INTO document_tracking (

                    order_number,

                    sent_date,

                    received_date,

                    note

                )

                VALUES (

                    :order_number,

                    :sent_date,

                    :received_date,

                    :note

                )

                """),

                {

                    "order_number": order_number,

                    "sent_date": sent_date,

                    "received_date": received_date,

                    "note": note
                }
            )

        st.cache_data.clear()

    @staticmethod
    def delete_tracking(
        tracking_id
    ):

        with engine.begin() as conn:

            conn.execute(

                text("""

                DELETE FROM document_tracking

                WHERE id=:id

                """),

                {
                    "id": tracking_id
                }
            )
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

        return pd.read_sql(
            query,
            engine
        )
    
    @staticmethod
    @st.cache_data(ttl=30)
    def get_latest_tracking():

        query = """

        SELECT *

        FROM document_tracking

        WHERE id IN (

            SELECT MAX(id)

            FROM document_tracking

            GROUP BY order_number

        )

        """

        return pd.read_sql(
            query,
            engine
        )
            