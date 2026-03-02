from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import get_settings
import os

settings = get_settings()

# Ensure data directory exists
os.makedirs("data", exist_ok=True)

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False}  # Needed for SQLite
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from app.models import property  # noqa: F401
    Base.metadata.create_all(bind=engine)


def run_migrations():
    """Run Alembic migrations to update database schema."""
    from alembic.config import Config
    from alembic import command
    from sqlalchemy import inspect

    alembic_cfg = Config("alembic.ini")

    # Check if alembic_version table exists (indicates migrations have been used before)
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    if "alembic_version" not in tables and "properties" in tables:
        # Database was created by init_db() without migrations
        # Stamp it as current so migrations don't try to re-add columns
        command.stamp(alembic_cfg, "head")
    else:
        # Run migrations normally
        command.upgrade(alembic_cfg, "head")
