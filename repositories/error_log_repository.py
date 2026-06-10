import pandas as pd

from sqlalchemy import text

from database.connection import engine

from utils.datetime_utils import convert_utc_columns


class ErrorLogRepository:

    @staticmethod
    def add_error(

        page_name,

        error_message

    ):

        with engine.begin() as conn:

            conn.execute(

                text("""

                INSERT INTO error_logs (

                    page_name,

                    error_message

                )

                VALUES (

                    :page_name,

                    :error_message

                )

                """),

                {

                    "page_name": page_name,

                    "error_message": error_message
                }
            )

            # =========================
            # KEEP ONLY LAST 20 ERRORS
            # =========================

            conn.execute(

                text("""

                DELETE FROM error_logs

                WHERE id NOT IN (

                    SELECT id

                    FROM error_logs

                    ORDER BY id DESC

                    LIMIT 20

                )

                """)
            )

    @staticmethod
    def get_errors():

        query = """

        SELECT *

        FROM error_logs

        ORDER BY id DESC

        """

        df = pd.read_sql(
            query,
            engine
        )
        
        return convert_utc_columns(df)

    @staticmethod
    def delete_all_errors():

        with engine.begin() as conn:

            conn.execute(

                text("""

                DELETE FROM error_logs

                """)
            )