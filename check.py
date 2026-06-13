from sqlalchemy import text
from database.postgres_connection import postgres_engine

constraints = [

    """
    ALTER TABLE orders
    ADD CONSTRAINT uq_orders_order_number
    UNIQUE(order_number)
    """,

    """
    ALTER TABLE payments
    ADD CONSTRAINT uq_payments_order_number
    UNIQUE(order_number)
    """,

    """
    ALTER TABLE users
    ADD CONSTRAINT uq_users_username
    UNIQUE(username)
    """,

    """
    ALTER TABLE revenue_kpi
    ADD CONSTRAINT uq_revenue_kpi_year_month
    UNIQUE(year, month)
    """

]

with postgres_engine.begin() as conn:

    for sql in constraints:

        try:
            conn.execute(text(sql))
            print("OK")
        except Exception as e:
            print("SKIP:", e)

print("DONE")
input()