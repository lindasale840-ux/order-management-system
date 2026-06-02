import pandas as pd

from sqlalchemy import text

from database.connection import engine


class ExternalExpenseRepository:

    @staticmethod
    def get_all_expenses():

        query = """

        SELECT *

        FROM external_expenses

        ORDER BY expense_date DESC

        """

        return pd.read_sql(

            query,

            engine
        )

    @staticmethod
    def add_expense(

        expense_date,

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

                "expense_date": expense_date,

                "amount": amount,

                "note": note
            })

    @staticmethod
    def delete_expense(
        expense_id
    ):

        with engine.begin() as conn:

            conn.execute(

                text("""

                DELETE FROM external_expenses

                WHERE id = :id

                """),

                {
                    "id": expense_id
                }
            )
        
        