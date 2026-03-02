from fastapi import APIRouter, Request, Depends, Form, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.services.property_service import PropertyService
from app.models import WorkflowStatus, MarketStatus

router = APIRouter(prefix="/properties")
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
async def list_properties(
    request: Request,
    workflow_status: Optional[str] = Query(None),
    market_status: Optional[str] = Query(None),
    zip_code: Optional[str] = Query(None),
    sort_by: str = Query("created_at"),
    sort_dir: str = Query("desc"),
    db: Session = Depends(get_db)
):
    """List all properties with filters."""
    service = PropertyService(db)

    # Convert string filters to enums
    wf_status = WorkflowStatus(workflow_status) if workflow_status else None
    mk_status = MarketStatus(market_status) if market_status else None

    properties = service.get_all(
        workflow_status=wf_status,
        market_status=mk_status,
        zip_code=zip_code,
        sort_by=sort_by,
        sort_dir=sort_dir
    )

    # Get unique zip codes for filter dropdown
    all_props = service.get_all()
    zip_codes = sorted(set(p.zip_code for p in all_props if p.zip_code))

    return templates.TemplateResponse(
        "list.html",
        {
            "request": request,
            "properties": properties,
            "workflow_statuses": [s.value for s in WorkflowStatus],
            "market_statuses": [s.value for s in MarketStatus],
            "zip_codes": zip_codes,
            "current_filters": {
                "workflow_status": workflow_status,
                "market_status": market_status,
                "zip_code": zip_code,
                "sort_by": sort_by,
                "sort_dir": sort_dir,
            }
        }
    )


@router.get("/table")
async def properties_table(
    request: Request,
    workflow_status: Optional[str] = Query(None),
    market_status: Optional[str] = Query(None),
    zip_code: Optional[str] = Query(None),
    sort_by: str = Query("created_at"),
    sort_dir: str = Query("desc"),
    db: Session = Depends(get_db)
):
    """Return just the table body for htmx updates."""
    service = PropertyService(db)

    wf_status = WorkflowStatus(workflow_status) if workflow_status else None
    mk_status = MarketStatus(market_status) if market_status else None

    properties = service.get_all(
        workflow_status=wf_status,
        market_status=mk_status,
        zip_code=zip_code,
        sort_by=sort_by,
        sort_dir=sort_dir
    )

    return templates.TemplateResponse(
        "partials/property_table_body.html",
        {"request": request, "properties": properties}
    )


@router.get("/{property_id}")
async def property_detail(
    request: Request,
    property_id: int,
    db: Session = Depends(get_db)
):
    """Get property detail panel (for htmx side panel)."""
    service = PropertyService(db)
    property_obj = service.get_by_id(property_id)

    if not property_obj:
        return HTMLResponse(content="Property not found", status_code=404)

    price_history = service.get_price_history(property_id)
    notes = service.get_notes(property_id)

    return templates.TemplateResponse(
        "partials/detail_panel.html",
        {
            "request": request,
            "property": property_obj,
            "price_history": price_history,
            "notes": notes,
            "workflow_statuses": [s.value for s in WorkflowStatus],
            "market_statuses": [s.value for s in MarketStatus],
        }
    )


@router.post("/{property_id}/workflow")
async def update_workflow(
    request: Request,
    property_id: int,
    workflow_status: str = Form(...),
    follow_up_date: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Update property workflow status."""
    service = PropertyService(db)

    try:
        status = WorkflowStatus(workflow_status)
    except ValueError:
        return HTMLResponse(content="Invalid status", status_code=400)

    property_obj = service.update_workflow_status(
        property_id, status, follow_up_date
    )

    if not property_obj:
        return HTMLResponse(content="Property not found", status_code=404)

    return templates.TemplateResponse(
        "partials/property_row.html",
        {"request": request, "property": property_obj}
    )


@router.post("/{property_id}/market")
async def update_market_status(
    request: Request,
    property_id: int,
    market_status: str = Form(...),
    db: Session = Depends(get_db)
):
    """Update property market status."""
    service = PropertyService(db)

    try:
        status = MarketStatus(market_status)
    except ValueError:
        return HTMLResponse(content="Invalid status", status_code=400)

    property_obj = service.update_market_status(property_id, status)

    if not property_obj:
        return HTMLResponse(content="Property not found", status_code=404)

    return templates.TemplateResponse(
        "partials/property_row.html",
        {"request": request, "property": property_obj}
    )


@router.post("/{property_id}/agent")
async def update_agent_info(
    request: Request,
    property_id: int,
    agent_name: Optional[str] = Form(None),
    agent_phone: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Update agent info for a property."""
    service = PropertyService(db)

    property_obj = service.update(property_id, {
        "agent_name": agent_name,
        "agent_phone": agent_phone
    })

    if not property_obj:
        return HTMLResponse(content="Property not found", status_code=404)

    return HTMLResponse(content="Agent info updated", status_code=200)


@router.post("/{property_id}/notes")
async def add_note(
    request: Request,
    property_id: int,
    content: str = Form(...),
    db: Session = Depends(get_db)
):
    """Add a note to a property."""
    service = PropertyService(db)
    note = service.add_note(property_id, content)

    notes = service.get_notes(property_id)

    return templates.TemplateResponse(
        "partials/notes_list.html",
        {"request": request, "notes": notes, "property_id": property_id}
    )


@router.delete("/notes/{note_id}")
async def delete_note(
    request: Request,
    note_id: int,
    property_id: int = Query(...),
    db: Session = Depends(get_db)
):
    """Delete a note."""
    service = PropertyService(db)
    service.delete_note(note_id)

    notes = service.get_notes(property_id)

    return templates.TemplateResponse(
        "partials/notes_list.html",
        {"request": request, "notes": notes, "property_id": property_id}
    )
