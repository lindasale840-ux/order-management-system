import pandas as pd
from database.connection import engine

df = pd.read_sql(

    """

    SELECT

        order_number,

        is_deleted,

        deleted_by

    FROM orders

    """,

    engine

)

print(df)