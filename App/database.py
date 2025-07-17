import os
import asyncpg
from dotenv import load_dotenv
from sqlalchemy import Column, Integer, MetaData
from sqlalchemy.ext.declarative import declarative_base
from databases import Database
import asyncio

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

database = Database(DATABASE_URL)
metadata = MetaData()
Base = declarative_base(metadata=metadata)

class Counter(Base):
    __tablename__ = "counters"
    id = Column(Integer, primary_key=True)
    value = Column(Integer, default=0)

async def wait_for_db(max_retries: int = 5, delay: float = 2.0):
    """Wait for database to become available."""
    retry_count = 0
    last_error = None
    
    while retry_count < max_retries:
        try:
            conn = await asyncpg.connect(
                user=os.getenv("POSTGRES_USER"),
                password=os.getenv("POSTGRES_PASSWORD"),
                database=os.getenv("POSTGRES_DB"),
                host="db",
                port=5432
            )
            await conn.close()
            return True
        except Exception as e:
            last_error = e
            retry_count += 1
            print(f"Database connection failed (attempt {retry_count}/{max_retries}): {str(e)}")
            await asyncio.sleep(delay)
    
    raise ConnectionError(f"Could not connect to database after {max_retries} attempts. Last error: {str(last_error)}")

async def ensure_tables_exist():
    await wait_for_db()
    
    async with database.transaction():
        await database.execute(
            """
            CREATE TABLE IF NOT EXISTS counters (
                id INTEGER PRIMARY KEY,
                value INTEGER DEFAULT 0
            )
            """
        )
        await database.execute(
            "INSERT INTO counters (id, value) VALUES (1, 0) ON CONFLICT (id) DO NOTHING"
        )