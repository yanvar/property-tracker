from fastapi import APIRouter, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date

from app.database import get_db
from app.services.property_service import PropertyService
from app.models import WorkflowStatus

router = APIRouter(prefix="/kanban")
templates = Jinja2Templates(directory="app/templates")


def sort_by_expired_first(properties):
    """Sort properties with expired follow-up dates first."""
    today = date.today()

    def sort_key(p):
        if p.follow_up_date:
            # Expired dates come first (negative days), then by date ascending
            is_expired = p.follow_up_date <= today
            return (0 if is_expired else 1, p.follow_up_date)
        # Properties without follow-up date go last
        return (2, date.max)

    return sorted(properties, key=sort_key)


@router.get("/")
async def kanban_board(request: Request, db: Session = Depends(get_db)):
    """Kanban board view."""
    service = PropertyService(db)
    today = date.today()

    columns = {}
    for status in WorkflowStatus:
        properties = service.get_all(workflow_status=status)
        # Sort Follow Up column with expired first
        if status == WorkflowStatus.FOLLOW_UP:
            properties = sort_by_expired_first(properties)
        columns[status.value] = properties

    # Get properties with price changes
    price_changed_ids = service.get_properties_with_price_changes()

    return templates.TemplateResponse(
        "kanban.html",
        {
            "request": request,
            "columns": columns,
            "statuses": [s.value for s in WorkflowStatus],
            "today": today,
            "price_changed_ids": price_changed_ids,
        }
    )


@router.post("/move/{property_id}")
async def move_property(
    request: Request,
    property_id: int,
    new_status: str = Form(...),
    follow_up_date: Optional[str] = Form(None),
    skip_reason: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Move property to a new workflow status (called via htmx)."""
    service = PropertyService(db)

    try:
        status = WorkflowStatus(new_status)
    except ValueError:
        return HTMLResponse(content="Invalid status", status_code=400)

    property_obj = service.update_workflow_status(
        property_id,
        status,
        follow_up_date=follow_up_date,
        skip_reason=skip_reason
    )

    if not property_obj:
        return HTMLResponse(content="Property not found", status_code=404)

    return templates.TemplateResponse(
        "partials/property_card.html",
        {"request": request, "property": property_obj, "today": date.today()}
    )
