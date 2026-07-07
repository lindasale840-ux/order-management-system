import pandas as pd
# Import 2 hàm tiện ích từ file pg_database của bạn
from database.pg_database import query_pg_to_dataframe, execute_pg_query
from utils.datetime_utils import convert_utc_columns

class OtherRevenueRepository:

    @staticmethod
    def get_all_revenues():
        query = """
        SELECT *
        FROM external_expenses
        ORDER BY expense_date DESC
        """
        df = query_pg_to_dataframe(query)
        return convert_utc_columns(df)

    @staticmethod
    def add_revenue(
        revenue_date,
        amount,
        note,
        created_by="System"
    ):
        query = """
        INSERT INTO external_expenses (
            expense_date,
            amount,
            note,
            created_by,
            created_at
        )
        VALUES (%s, %s, %s, %s, NOW())
        """
        
        params = (revenue_date, amount, note, created_by)
        execute_pg_query(query, params)

    @staticmethod
    def delete_revenue(revenue_id):
        query = """
        DELETE FROM external_expenses
        WHERE id = %s
        """
        
        execute_pg_query(query, (revenue_id,))