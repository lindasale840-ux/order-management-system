from sqlalchemy import text
from database.connection import engine

with engine.begin() as conn:

    result = conn.execute(text("""
    SELECT
        id,
        order_number,
        created_at,
        updated_at
    FROM orders
    WHERE order_number='test71'
    """))

    print(result.fetchone())