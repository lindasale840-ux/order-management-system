import pandas as pd
from database.connection import engine

df = pd.read_sql("""

SELECT
order_number,
sale_owner,
created_by

FROM orders

LIMIT 20

""", engine)

print(df)