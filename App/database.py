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

async def connect_to_db():
    """Ensure database connection is established"""
    if not database.is_connected:
        await database.connect()

async def disconnect_from_db():
    """Close database connection"""
    if database.is_connected:
        await database.disconnect()

async def wait_for_db(max_retries=5, delay=2.0):
    """Wait for database to become available"""
    retry_count = 0
    while retry_count < max_retries:
        try:
            await connect_to_db()
            await database.execute("SELECT 1")
            return True
        except Exception as e:
            retry_count += 1
            print(f"Database connection failed (attempt {retry_count}/{max_retries}): {str(e)}")
            await asyncio.sleep(delay)
    raise ConnectionError(f"Could not connect to database after {max_retries} attempts")

async def ensure_tables_exist():
    """Create tables if they don't exist"""
    await wait_for_db()
    async with database.transaction():
        await database.execute("""
            CREATE TABLE IF NOT EXISTS counters (
                id INTEGER PRIMARY KEY,
                value INTEGER DEFAULT 0
            )
        """)
        await database.execute("""
            INSERT INTO counters (id, value) VALUES (1, 0) 
            ON CONFLICT (id) DO NOTHING
        """)