import sqlite3

conn = sqlite3.connect("database/app.db")
cursor = conn.cursor()

cursor.execute("""
SELECT
order_number,
customer_name,
sale_owner
FROM orders
ORDER BY id DESC
LIMIT 5
""")

for row in cursor.fetchall():
    print(row)