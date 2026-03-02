from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.property_service import PropertyService

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
async def dashboard(request: Request, db: Session = Depends(get_db)):
    """Dashboard home page with priority cards and stats."""
    service = PropertyService(db)

    stats = service.get_dashboard_stats()
    followups = service.get_properties_needing_followup()
    new_properties = service.get_new_properties(limit=5)

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "stats": stats,
            "followups": followups,
            "new_properties": new_properties,
        }
    )
