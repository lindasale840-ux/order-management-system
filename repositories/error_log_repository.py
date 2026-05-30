import pandas as pd

from sqlalchemy import text

from database.connection import engine


class ErrorLogRepository:

    @staticmethod
    def add_error(

        page_name,

        error_message

    ):

        query = text("""

        INSERT INTO error_logs (

            page_name,

            error_message

        )

        VALUES (

            :page_name,

            :error_message

        )

        """)

        with engine.begin() as conn:

            conn.execute(

                query,

                {

                    "page_name": page_name,

                    "error_message": error_message
                }
            )

    @staticmethod
    def get_errors():

        query = """

        SELECT *

        FROM error_logs

        ORDER BY id DESC

        """

        return pd.read_sql(
            query,
            engine
        )