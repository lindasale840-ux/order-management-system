import pandas as pd
import streamlit as st

from sqlalchemy import text

from database.connection import engine

from utils.datetime_utils import (
    convert_utc_columns
)


class OtherDocumentTrackingRepository:

    @staticmethod
    @st.cache_data(ttl=30)
    def get_all():

        query = """

        SELECT *

        FROM other_document_tracking

        ORDER BY id DESC

        """

        df = pd.read_sql(
            query,
            engine
        )

        return convert_utc_columns(df)

    @staticmethod
    def add_tracking(

        customer_name,

        document_type,

        sent_date,

        received_date,

        note

    ):

        with engine.begin() as conn:

            conn.execute(

                text("""

                INSERT INTO other_document_tracking (

                    customer_name,

                    document_type,

                    sent_date,

                    received_date,

                    note

                )

                VALUES (

                    :customer_name,

                    :document_type,

                    :sent_date,

                    :received_date,

                    :note

                )

                """),

                {

                    "customer_name": customer_name,

                    "document_type": document_type,

                    "sent_date": sent_date,

                    "received_date": received_date,

                    "note": note

                }

            )

        st.cache_data.clear()

    @staticmethod
    def delete_tracking(record_id):

        with engine.begin() as conn:

            conn.execute(

                text("""

                DELETE FROM other_document_tracking

                WHERE id = :id

                """),

                {

                    "id": record_id

                }

            )

        st.cache_data.clear()