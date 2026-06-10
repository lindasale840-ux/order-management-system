from sqlalchemy import text
from database.connection import engine

with engine.begin() as conn:

    conn.execute(text("""
    UPDATE orders
    SET created_at = datetime(created_at,'+7 hours')
    """))

    conn.execute(text("""
    UPDATE payments
    SET created_at = datetime(created_at,'+7 hours')
    """))

    conn.execute(text("""
    UPDATE logs
    SET created_at = datetime(created_at,'+7 hours')
    """))

    conn.execute(text("""
    UPDATE document_tracking
    SET created_at = datetime(created_at,'+7 hours')
    """))

    conn.execute(text("""
    UPDATE equipment_tracking
    SET created_at = datetime(created_at,'+7 hours')
    """))

print("DONE")