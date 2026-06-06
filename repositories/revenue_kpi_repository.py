import pandas as pd
import streamlit as st

from sqlalchemy import text

from database.connection import engine


class RevenueKPIRepository:

    @staticmethod
    @st.cache_data(ttl=30)
    def get_all():

        return pd.read_sql(

            """

            SELECT *

            FROM revenue_kpi

            ORDER BY year DESC

            """,

            engine
        )

    @staticmethod
    def upsert_kpi(

        year,
        month,
        target_amount

    ):

        with engine.begin() as conn:

            conn.execute(

                text("""

                INSERT INTO revenue_kpi(

                    year,
                    month,
                    target_amount

                )

                VALUES(

                    :year,
                    :month,
                    :target_amount

                )

                ON CONFLICT(year, month)

                DO UPDATE SET

                    target_amount=excluded.target_amount

                """),

                {

                    "year": year,
                    "month": month,
                    "target_amount": target_amount

                }
            )

        st.cache_data.clear()

    @staticmethod
    def get_by_year(

        year

    ):

        return pd.read_sql(

            text("""

            SELECT *

            FROM revenue_kpi

            WHERE year=:year

            """),

            engine,

            params={

                "year": year

            }
        )