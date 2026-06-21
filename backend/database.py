import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Default to SQLite for local execution, switch to postgres in Docker Compose
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sentineliq.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
pool_kwargs = {}
if not DATABASE_URL.startswith("sqlite"):
    pool_kwargs["pool_size"] = 20
    pool_kwargs["max_overflow"] = 20

engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args, **pool_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
