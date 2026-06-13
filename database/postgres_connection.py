from sqlalchemy import create_engine

POSTGRES_URL = (
    "postgresql+psycopg2://postgres:gstfamily@localhost:5432/order_management"
)

postgres_engine = create_engine(
    POSTGRES_URL,
    pool_pre_ping=True
)