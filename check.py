from sqlalchemy import text

from database.connection import engine

order_number = "GST_VN2026060107HN"

with engine.begin() as conn:

    conn.execute(

        text("""

        UPDATE payments

        SET payment_terms = 30

        WHERE order_number = :order_number

        """),

        {
            "order_number": order_number
        }

    )

print("Done")