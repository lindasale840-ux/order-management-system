from database.connection import engine
import pandas as pd

df = pd.read_sql(
    """
    SELECT
        order_number,
        customer_name,
        sale_owner
    FROM orders
    LIMIT 30
    """,
    engine
)

print(df)