import pandas as pd

from sqlalchemy import text

from database.connection import engine


class LogRepository:

    @staticmethod
    def add_log(
        action,
        customer_name,
        order_number,
        description
    ):

        query = text("""
        INSERT INTO logs (
            action,
            customer_name,
            order_number,
            description
        )

        VALUES (
            :action,
            :customer_name,
            :order_number,
            :description
        )
        """)

        with engine.begin() as conn:

            conn.execute(query, {

                "action": action,
                "customer_name": customer_name,
                "order_number": order_number,
                "description": description
            })

    @staticmethod
    def get_logs():

        query = """
        SELECT *
        FROM logs
        ORDER BY id DESC
        """

        return pd.read_sql(query, engine)