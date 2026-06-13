import pandas as pd
from sqlalchemy import create_engine

sqlite_engine = create_engine(
    "sqlite:///database/app.db"
)

postgres_engine = create_engine(
    "postgresql+psycopg2://postgres:gstfamily@localhost:5432/order_management"
)

TABLES = [
    "orders",
    "payments",
    "logs",
    "users",
    "error_logs",
    "external_expenses",
    "document_tracking",
    "equipment_tracking",
    "revenue_kpi",
    "other_document_tracking"
]

for table in TABLES:

    print(f"Migrating {table}...")

    df = pd.read_sql(
        f"SELECT * FROM {table}",
        sqlite_engine
    )

    df.to_sql(
        table,
        postgres_engine,
        if_exists="replace",
        index=False
    )

    print(
        f"{table}: {len(df)} rows"
    )

print("DONE")