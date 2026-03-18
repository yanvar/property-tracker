from fastapi import APIRouter, Request, Depends, Form, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date
from pydantic import BaseModel

from app.database import get_db
from app.services.property_service import PropertyService
from app.models import WorkflowStatus, MarketStatus


def calculate_target_price(property_obj):
    """Calculate target price for investment based on rent estimate and expenses."""
    if not property_obj.calc_rent_estimate:
        return {"can_calculate": False, "target_price": None, "noi": None, "actual_yield": None}

    # Convert from storage (cents/basis points) to dollars/percentages
    monthly_rent = property_obj.calc_rent_estimate / 100
    rehab = (property_obj.calc_rehab_estimate or 2000000) / 100
    prop_tax = (property_obj.calc_property_tax or 350000) / 100
    insurance = (property_obj.calc_insurance or 70000) / 100
    maintenance = (property_obj.calc_maintenance or 100000) / 100
    target_yield = (property_obj.calc_target_yield or 700) / 10000
    broker_fee = (property_obj.calc_broker_fee or 300) / 10000
    closing_fee = (property_obj.calc_closing_fee or 150) / 10000
    inspection = (property_obj.calc_inspection or 50000) / 100

    # Calculate NOI (Net Operating Income)
    annual_rent = monthly_rent * 12 * (23/24)  # vacancy: 1 month every 2 years
    annual_expenses = prop_tax + insurance + maintenance
    noi = annual_rent - annual_expenses

    # Calculate target price
    if target_yield <= 0:
        return {"can_calculate": False, "target_price": None, "noi": noi, "actual_yield": None}

    target_price = (noi / target_yield - rehab - inspection) / (1 + broker_fee + closing_fee)

    # Also calculate yield at list price if available
    actual_yield = None
    if property_obj.price:
        list_price = property_obj.price / 100
        total_inv = list_price * (1 + broker_fee + closing_fee) + rehab + inspection
        actual_yield = (noi / total_inv) * 100 if total_inv > 0 else 0

    return {
        "can_calculate": True,
        "target_price": target_price,
        "noi": noi,
        "actual_yield": actual_yield
    }


class BulkDeleteRequest(BaseModel):
    property_ids: List[int]

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
    calculated = calculate_target_price(property_obj)

    return templates.TemplateResponse(
        "partials/detail_panel.html",
        {
            "request": request,
            "property": property_obj,
            "price_history": price_history,
            "notes": notes,
            "calculated": calculated,
            "workflow_statuses": [s.value for s in WorkflowStatus],
            "market_statuses": [s.value for s in MarketStatus],
            "today": date.today(),
        }
    )


@router.post("/{property_id}/workflow")
async def update_workflow(
    request: Request,
    property_id: int,
    workflow_status: str = Form(...),
    follow_up_date: Optional[str] = Form(None),
    skip_reason: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Update property workflow status."""
    service = PropertyService(db)

    try:
        status = WorkflowStatus(workflow_status)
    except ValueError:
        return HTMLResponse(content="Invalid status", status_code=400)

    property_obj = service.update_workflow_status(
        property_id, status, follow_up_date, skip_reason
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


@router.post("/{property_id}/calculator")
async def update_calculator(
    request: Request,
    property_id: int,
    calc_rent_estimate: Optional[int] = Form(None),
    calc_rehab_estimate: Optional[int] = Form(None),
    calc_property_tax: Optional[int] = Form(None),
    calc_insurance: Optional[int] = Form(None),
    calc_maintenance: Optional[int] = Form(None),
    calc_target_yield: Optional[int] = Form(None),
    calc_broker_fee: Optional[int] = Form(None),
    calc_closing_fee: Optional[int] = Form(None),
    calc_inspection: Optional[int] = Form(None),
    db: Session = Depends(get_db)
):
    """Update calculator inputs for a property and return updated results."""
    service = PropertyService(db)

    update_data = {}
    if calc_rent_estimate is not None:
        update_data["calc_rent_estimate"] = calc_rent_estimate
    if calc_rehab_estimate is not None:
        update_data["calc_rehab_estimate"] = calc_rehab_estimate
    if calc_property_tax is not None:
        update_data["calc_property_tax"] = calc_property_tax
    if calc_insurance is not None:
        update_data["calc_insurance"] = calc_insurance
    if calc_maintenance is not None:
        update_data["calc_maintenance"] = calc_maintenance
    if calc_target_yield is not None:
        update_data["calc_target_yield"] = calc_target_yield
    if calc_broker_fee is not None:
        update_data["calc_broker_fee"] = calc_broker_fee
    if calc_closing_fee is not None:
        update_data["calc_closing_fee"] = calc_closing_fee
    if calc_inspection is not None:
        update_data["calc_inspection"] = calc_inspection

    property_obj = service.update(property_id, update_data)

    if not property_obj:
        return HTMLResponse(content="Property not found", status_code=404)

    calculated = calculate_target_price(property_obj)

    return templates.TemplateResponse(
        "partials/investment_calculator.html",
        {
            "request": request,
            "property": property_obj,
            "calculated": calculated,
        }
    )


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


@router.post("/bulk-delete")
async def delete_properties_bulk(
    request: Request,
    body: BulkDeleteRequest,
    db: Session = Depends(get_db)
):
    """Delete multiple properties at once."""
    service = PropertyService(db)
    result = service.delete_properties_bulk(body.property_ids)

    # Return empty response - the UI will refresh the table
    return HTMLResponse(content="", status_code=200)


@router.delete("/{property_id}")
async def delete_property(
    request: Request,
    property_id: int,
    db: Session = Depends(get_db)
):
    """Delete a property and all related data."""
    service = PropertyService(db)
    success = service.delete_property(property_id)

    if not success:
        return HTMLResponse(content="Property not found", status_code=404)

    # Return empty response - the UI will handle redirect/refresh
    return HTMLResponse(content="", status_code=200)
