from sqlalchemy import text
from database.connection import engine

with engine.begin() as conn:

    conn.execute(text("""
    UPDATE orders
    SET updated_at = datetime(updated_at,'+7 hours')
    """))

    conn.execute(text("""
    UPDATE payments
    SET updated_at = datetime(updated_at,'+7 hours')
    """))

print("DONE")