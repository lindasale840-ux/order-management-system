from sqlalchemy import text

from database.connection import engine

with engine.begin() as conn:

    result = conn.execute(text("""

        SELECT name

        FROM sqlite_master

        WHERE type='table'

        AND name='revenue_kpi'

    """))

    row = result.fetchone()

if row:

    print("FOUND")
else:

    print("NOT FOUND")