import pandas as pd
from sqlalchemy import text
from database.connection import engine


class AssistantSaleRepository:

    @staticmethod
    def get_sales_by_assistant(
        assistant_username
    ):
        query = """
        SELECT sale_owner
        FROM assistant_sale_mapping
        WHERE assistant_username=:assistant_username
        """

        df = pd.read_sql(
            text(query),
            engine,
            params={
                "assistant_username":
                    assistant_username
            }
        )

        if df.empty:
            return []

        return (
            df["sale_owner"]
            .astype(str)
            .tolist()
        )

    @staticmethod
    def delete_by_assistant(
        assistant_username
    ):
        with engine.begin() as conn:
            conn.execute(
                text("""
                DELETE
                FROM assistant_sale_mapping
                WHERE assistant_username=
                    :assistant_username
                """),
                {
                    "assistant_username":
                        assistant_username
                }
            )

    @staticmethod
    def add_mapping(
        assistant_username,
        sale_owner
    ):
        with engine.begin() as conn:
            conn.execute(
                text("""
                INSERT OR IGNORE
                INTO assistant_sale_mapping
                (
                    assistant_username,
                    sale_owner
                )
                VALUES
                (
                    :assistant_username,
                    :sale_owner
                )
                """),
                {
                    "assistant_username":
                        assistant_username,
                    "sale_owner":
                        sale_owner
                }
            )

    @staticmethod
    def get_all():
        query = """
        SELECT *
        FROM assistant_sale_mapping
        ORDER BY assistant_username,
                 sale_owner
        """

        return pd.read_sql(
            query,
            engine
        )