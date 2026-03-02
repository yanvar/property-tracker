from fastapi import APIRouter, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.services.property_service import PropertyService
from app.models import WorkflowStatus

router = APIRouter(prefix="/kanban")
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
async def kanban_board(request: Request, db: Session = Depends(get_db)):
    """Kanban board view."""
    service = PropertyService(db)

    columns = {}
    for status in WorkflowStatus:
        columns[status.value] = service.get_all(workflow_status=status)

    return templates.TemplateResponse(
        "kanban.html",
        {
            "request": request,
            "columns": columns,
            "statuses": [s.value for s in WorkflowStatus],
        }
    )


@router.post("/move/{property_id}")
async def move_property(
    request: Request,
    property_id: int,
    new_status: str = Form(...),
    follow_up_date: Optional[str] = Form(None),
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
        follow_up_date=follow_up_date
    )

    if not property_obj:
        return HTMLResponse(content="Property not found", status_code=404)

    return templates.TemplateResponse(
        "partials/property_card.html",
        {"request": request, "property": property_obj}
    )
