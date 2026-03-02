from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import init_db, run_migrations
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
    """Initialize database and run migrations on startup."""
    init_db()
    try:
        run_migrations()
    except Exception as e:
        # Log but don't fail - migrations may already be applied
        print(f"Migration note: {e}")
