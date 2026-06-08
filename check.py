import pandas as pd
from database.connection import engine

order_no = "test1"

df = pd.read_sql(

    f"""

    SELECT

        order_number,

        is_deleted,

        deleted_at,

        deleted_by

    FROM orders

    WHERE order_number = '{order_no}'

    """,

    engine

)

print(df)