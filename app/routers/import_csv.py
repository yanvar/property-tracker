from fastapi import APIRouter, Request, Depends, Form, UploadFile, File
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.csv_parser import parse_redfin_csv
from app.services.property_service import PropertyService

router = APIRouter(prefix="/import")
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
async def import_page(request: Request):
    """CSV import page."""
    return templates.TemplateResponse(
        "import.html",
        {"request": request}
    )


@router.post("/")
async def process_import(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Process CSV import."""
    service = PropertyService(db)

    # Read file content
    content = await file.read()
    csv_content = content.decode("utf-8")

    # Parse CSV
    try:
        properties_data = parse_redfin_csv(csv_content)
    except Exception as e:
        return templates.TemplateResponse(
            "import.html",
            {
                "request": request,
                "error": f"Error parsing CSV: {str(e)}"
            }
        )

    # Import properties
    summary = service.import_properties(properties_data)

    return templates.TemplateResponse(
        "import.html",
        {
            "request": request,
            "summary": summary
        }
    )
