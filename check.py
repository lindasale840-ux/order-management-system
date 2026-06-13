from database.connection import engine
from sqlalchemy import text

with engine.begin() as conn:
    result = conn.execute(
        text("SELECT COUNT(*) FROM orders")
    )

    print(result.scalar())