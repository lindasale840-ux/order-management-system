import pandas as pd
from database.connection import engine

df = pd.read_sql(

    """

    PRAGMA table_info(orders)

    """,

    engine

)

print(df[["name"]])