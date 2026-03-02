from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import init_db
from app.routers import dashboard, kanban, properties, import_csv

app = FastAPI(title="Property Tracker", version="1.0.0")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include routers
app.include_router(dashboard.router)
app.include_router(kanban.router)
app.include_router(properties.router)
app.include_router(import_csv.router)


@app.on_event("startup")
async def startup():
    """Initialize database on startup."""
    init_db()
