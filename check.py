import pandas as pd
from database.connection import engine

df = pd.read_sql("""

SELECT
    order_number,
    is_deleted,
    deleted_at
FROM orders
WHERE order_number IN ('test','test1','test2')

""", engine)

print(df)