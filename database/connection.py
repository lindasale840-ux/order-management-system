from decouple import config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = (
    f"postgresql+psycopg2://"
    f"{config('POSTGRES_USER')}:"
    f"{config('POSTGRES_PASSWORD')}@"
    f"{config('POSTGRES_HOST')}:"
    f"{config('POSTGRES_PORT')}/"
    f"{config('POSTGRES_DB')}"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)