import pandas as pd

from sqlalchemy import text

from database.connection import engine


class UserRepository:

    @staticmethod
    def get_all_users():

        query = """

        SELECT *

        FROM users

        ORDER BY username

        """

        return pd.read_sql(
            query,
            engine
        )

    @staticmethod
    def get_user_by_username(
        username
    ):

        query = text("""

        SELECT *

        FROM users

        WHERE username = :username

        LIMIT 1

        """)

        with engine.begin() as conn:

            result = conn.execute(

                query,

                {
                    "username": username
                }

            ).mappings().first()

            return result

    @staticmethod
    def create_user(

        username,

        password_hash,

        role,

        sale_owner

    ):

        query = text("""

        INSERT INTO users (

            username,

            password_hash,

            role,
                     
            sale_owner         

        )

        VALUES (

            :username,

            :password_hash,

            :role,
                     
            :sale_owner          

        )

        """)

        with engine.begin() as conn:

            conn.execute(

                query,

                {

                    "username": username,

                    "password_hash": password_hash,

                    "role": role,

                    "sale_owner": sale_owner
                }
            )

    @staticmethod
    def delete_user(
        username
    ):

        query = text("""

        DELETE FROM users

        WHERE username = :username

        """)

        with engine.begin() as conn:

            conn.execute(

                query,

                {
                    "username": username
                }
            )