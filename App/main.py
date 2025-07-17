# sudo aa-remove-unknown
# /etc/init.d/redis-server stop
# docker-compose down -v && docker-compose up --build

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from database import database, Counter, ensure_tables_exist
from redis_client import redis 
from sqlalchemy import update, select

app = FastAPI(root_path="/api")
templates = Jinja2Templates(directory="templates")

REDIS_COUNTER_KEY = "app_counter"

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/docs") or request.url.path.startswith("/redoc"):
        script = f"""
        <script>
            window.onload = function() {{
                const ui = window.ui;
                ui.servers = [
                    {{
                        url: '{request.url.scheme}://{request.headers.get("host")}/api',
                        description: "Nginx proxy"
                    }}
                ]
            }}
        </script>
        """
        response.body = response.body.decode().replace("</body>", f"{script}</body>").encode()
    return response

@app.on_event("startup")
async def startup():
    await database.connect()
    await ensure_tables_exist()
    await redis.ping() 
    await database.execute(
        "INSERT INTO counters (id, value) VALUES (1, 0) ON CONFLICT (id) DO NOTHING"
    )

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()
    await redis.close()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    cached_counter = await redis.get(REDIS_COUNTER_KEY)
    if cached_counter is not None:
        return templates.TemplateResponse(
            "index.html", 
            {"request": request, "counter": int(cached_counter)}
        )

    query = select(Counter.value).where(Counter.id == 1)
    counter = await database.fetch_val(query)
    await redis.setex(REDIS_COUNTER_KEY, 60, counter)
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "counter": counter}
    )

@app.post("/increment", response_class=HTMLResponse)
async def increment_counter(request: Request):
    query = update(Counter).where(Counter.id == 1).values(value=Counter.value + 1)
    await database.execute(query)
    await redis.delete(REDIS_COUNTER_KEY)
    return await read_root(request)

@app.post("/decrement", response_class=HTMLResponse)
async def decrement_counter(request: Request):
    query = update(Counter).where(Counter.id == 1).values(value=Counter.value - 1)
    await database.execute(query)
    await redis.delete(REDIS_COUNTER_KEY)
    return await read_root(request)