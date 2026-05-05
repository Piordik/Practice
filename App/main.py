# sudo aa-remove-unknown
# /etc/init.d/redis-server stop
# docker-compose down -v && docker-compose up --build

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from database import database, Counter, ensure_tables_exist, connect_to_db, disconnect_from_db
from redis_client import redis
from sqlalchemy import update, select
import prometheus_client as prom
from fastapi import Response

app = FastAPI(root_path="/api")
templates = Jinja2Templates(directory="templates")

REDIS_COUNTER_KEY = "app_counter"

REQUEST_COUNT = prom.Counter('app_request_count', 'Total HTTP Requests')
REQUEST_LATENCY = prom.Histogram('app_request_latency_seconds', 'Request latency')

@app.on_event("startup")
async def startup():
    print("Starting application initialization...") 
    try:
        print("Connecting to database...")
        await connect_to_db()
        print("Creating tables if needed...")
        await ensure_tables_exist()
        print("Testing Redis connection...")
        await redis.ping()
        print("All services connected successfully!")
    except Exception as e:
        print(f"STARTUP FAILED: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown():
    await disconnect_from_db()
    await redis.close()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        await database.execute("SELECT 1")
        await redis.ping()
        return {"status": "healthy"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}, 503

@app.get("/metrics")
async def metrics():
    return Response(
        media_type="text/plain",
        content=prom.generate_latest()
    )

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    REQUEST_COUNT.inc()
    with REQUEST_LATENCY.time():
        cached_counter = await redis.get(REDIS_COUNTER_KEY)
        if cached_counter:
            return templates.TemplateResponse("index.html", {"request": request, "counter": int(cached_counter)})

        query = select(Counter.value).where(Counter.id == 1)
        counter = await database.fetch_val(query)
        await redis.setex(REDIS_COUNTER_KEY, 60, counter)
        return templates.TemplateResponse("index.html", {"request": request, "counter": counter})

@app.post("/increment")
async def increment_counter(request: Request):
    query = update(Counter).where(Counter.id == 1).values(value=Counter.value + 1)
    await database.execute(query)
    await redis.delete(REDIS_COUNTER_KEY)
    return await read_root(request)

@app.post("/decrement")
async def decrement_counter(request: Request):
    query = update(Counter).where(Counter.id == 1).values(value=Counter.value - 1)
    await database.execute(query)
    await redis.delete(REDIS_COUNTER_KEY)
    return await read_root(request)