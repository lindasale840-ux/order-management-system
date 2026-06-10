import pandas as pd

import streamlit as st

from sqlalchemy import text

from database.connection import engine

from utils.datetime_utils import convert_utc_columns


class LogRepository:

    MAX_LOG_ROWS = 5000

    @staticmethod
    def add_log(
        action,
        customer_name,
        order_number,
        description,
        username="SYSTEM"
    ):
        
        username = st.session_state.get(
            "username",
            "SYSTEM"
        )

        query = text("""
        INSERT INTO logs (
            username,          
            action,
            customer_name,
            order_number,
            description
        )

        VALUES (
            :username,         
            :action,
            :customer_name,
            :order_number,
            :description
        )
        """)

        with engine.begin() as conn:

            conn.execute(
                query,
                {
                    "username": username,
                    "action": action,
                    "customer_name": customer_name,
                    "order_number": order_number,
                    "description": description
                }
            )

            # =========================
            # AUTO PURGE
            # KEEP ONLY NEWEST 5000
            # =========================

            conn.execute(text(f"""
            DELETE FROM logs
            WHERE id NOT IN (

                SELECT id
                FROM logs
                ORDER BY id DESC
                LIMIT {LogRepository.MAX_LOG_ROWS}

            )
            """))

    @staticmethod
    def get_logs():

        query = """
        SELECT *
        FROM logs
        ORDER BY id DESC
        """

        df = pd.read_sql(
            query,
            engine
        )
        
        return convert_utc_columns(df)

    @staticmethod
    def delete_all_logs():

        with engine.begin() as conn:

            conn.execute(
                text(
                    "DELETE FROM logs"
                )
            )

    @staticmethod
    def get_log_count():

        with engine.begin() as conn:

            return conn.execute(
                text(
                    "SELECT COUNT(*) FROM logs"
                )
            ).scalar()