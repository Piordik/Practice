# sudo aa-remove-unknown
# /etc/init.d/redis-server stop
# docker-compose down -v && docker-compose up --build

from fastapi import FastAPI, Request, BackgroundTasks, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from database import database, Counter, ensure_tables_exist, connect_to_db, disconnect_from_db
from redis_client import redis
from sqlalchemy import update, select
import prometheus_client as prom
import logging


# ====================== Конфигурация ======================
REDIS_COUNTER_KEY = "app_counter"
DEFAULT_COUNTER_ID = 1

app = FastAPI(root_path="/api", title="Counter Service")
templates = Jinja2Templates(directory="templates")

# Prometheus метрики
REQUEST_COUNT = prom.Counter('app_request_count', 'Total HTTP Requests')
REQUEST_LATENCY = prom.Histogram('app_request_latency_seconds', 'Request latency')


logger = logging.getLogger(__name__)


@app.on_event("startup")
async def startup():
    print("Starting Counter Service...")
    try:
        await connect_to_db()
        await ensure_tables_exist()
        await redis.ping()
        print("All services connected successfully!")
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise


@app.on_event("shutdown")
async def shutdown():
    await disconnect_from_db()
    if not redis.is_closed:
        await redis.close()


@app.get("/health")
async def health_check():
    try:
        await database.execute("SELECT 1")
        await redis.ping()
        return {"status": "healthy"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}, 503


@app.get("/metrics")
async def metrics():
    return Response(media_type="text/plain", content=prom.generate_latest())


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    REQUEST_COUNT.inc()
    
    with REQUEST_LATENCY.time():
        cached = await redis.get(REDIS_COUNTER_KEY)
        if cached is not None:
            return templates.TemplateResponse("index.html", {
                "request": request, 
                "counter": int(cached)
            })

        query = select(Counter.value).where(Counter.id == DEFAULT_COUNTER_ID)
        value = await database.fetch_val(query) or 0
        
        await redis.setex(REDIS_COUNTER_KEY, 600, value)
        return templates.TemplateResponse("index.html", {
            "request": request, 
            "counter": value
        })


async def update_counter(delta: int):
    """Фоновая задача обновления счётчика"""
    try:
        query = update(Counter).where(
            Counter.id == DEFAULT_COUNTER_ID
        ).values(value=Counter.value + delta)
        
        await database.execute(query)

        # Обновляем Redis
        new_value = await database.fetch_val(
            select(Counter.value).where(Counter.id == DEFAULT_COUNTER_ID)
        )
        await redis.setex(REDIS_COUNTER_KEY, 600, new_value)
        
        COUNTER_VALUE.set(new_value)
        COUNTER_CHANGES.inc()

    except Exception as e:
        logger.error(f"Failed to update counter: {e}")


# ==================== POST с редиректом ====================
@app.post("/increment")
async def increment_counter(background_tasks: BackgroundTasks):
    await update_counter(1) 
    return RedirectResponse(url="/", status_code=303)


@app.post("/decrement")
async def decrement_counter(background_tasks: BackgroundTasks):
    await update_counter(-1) 
    return RedirectResponse(url="/", status_code=303)


# Для удобства
@app.get("/increment")
async def increment_get():
    return RedirectResponse(url="/", status_code=303)


@app.get("/decrement")
async def decrement_get():
    return RedirectResponse(url="/", status_code=303)