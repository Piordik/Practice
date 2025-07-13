import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, MetaData, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import NullPool
from databases import Database

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@db:5432/postgres"
)

sync_engine = create_engine(
    DATABASE_URL.replace("+asyncpg", ""),
    poolclass=NullPool,
    echo=bool(os.getenv("DEBUG", False))
)

async def create_tables_async():
    if not database.is_connected:
        await database.connect()
    
    await database.execute(
        """
        CREATE TABLE IF NOT EXISTS counters (
            id INTEGER PRIMARY KEY,
            value INTEGER DEFAULT 0
        )
        """
    )

database = Database(DATABASE_URL)
metadata = MetaData()
Base = declarative_base(metadata=metadata)

class Counter(Base):
    __tablename__ = "counters"
    id = Column(Integer, primary_key=True)
    value = Column(Integer, default=0)

def create_tables():
    Base.metadata.create_all(bind=sync_engine)