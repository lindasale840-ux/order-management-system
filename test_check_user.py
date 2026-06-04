import sqlite3

conn = sqlite3.connect(
    "database/app.db"
)

cursor = conn.cursor()

cursor.execute("""
SELECT
    order_number,
    invoice_group,
    invoice_date
FROM payments
WHERE invoice_group IS NOT NULL
  AND invoice_date IS NULL
""")

rows = cursor.fetchall()

print(
    "\n===== RECORDS WITH NULL INVOICE DATE =====\n"
)

if not rows:
    print("No problem found.")
else:
    for row in rows:
        print(row)

conn.close()