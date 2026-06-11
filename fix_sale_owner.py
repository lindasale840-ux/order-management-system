from sqlalchemy import text

from database.connection import engine


def update_all_sale_owner():

    with engine.begin() as conn:

        result = conn.execute(
            text("""
                UPDATE orders
                SET sale_owner = 'LINDA'
            """)
        )

        print(
            f"Updated {result.rowcount} orders."
        )


if __name__ == "__main__":

    update_all_sale_owner()