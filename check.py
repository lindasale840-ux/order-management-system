import pandas as pd
from database.connection import engine

df = pd.read_sql(

    """

    SELECT *

    FROM document_tracking

    WHERE order_number='check.py'

    """,

    engine

)

print(df)