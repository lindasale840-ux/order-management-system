import pandas as pd

from sqlalchemy import text

from database.connection import engine

from utils.datetime_utils import convert_utc_columns


class OtherRevenueRepository:

    @staticmethod
    def get_all_revenues():

        query = """

        SELECT *

        FROM external_expenses

        ORDER BY expense_date DESC

        """

        df = pd.read_sql(

            query,

            engine
        )
        
        return convert_utc_columns(df)

    @staticmethod
    def add_revenue(

        revenue_date,

        amount,

        note
    ):

        with engine.begin() as conn:

            conn.execute(text("""

            INSERT INTO external_expenses (

                expense_date,

                amount,

                note

            )

            VALUES (

                :expense_date,

                :amount,

                :note

            )

            """),

            {

                "expense_date": revenue_date,

                "amount": amount,

                "note": note
            })

    @staticmethod
    def delete_revenue(
        revenue_id
    ):

        with engine.begin() as conn:

            conn.execute(

                text("""

                DELETE FROM external_expenses

                WHERE id = :id

                """),

                {
                    "id": revenue_id
                }
            )