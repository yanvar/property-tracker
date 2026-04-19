from typing import List

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
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """Process CSV import from one or more files."""
    service = PropertyService(db)

    summary = {
        "added": 0,
        "updated": 0,
        "price_changes": [],
        "unchanged": 0,
        "errors": []
    }
    file_results = []

    for upload_file in files:
        file_result = {
            "filename": upload_file.filename,
            "added": 0,
            "updated": 0,
            "unchanged": 0,
            "error": None
        }

        try:
            content = await upload_file.read()
            csv_content = content.decode("utf-8")
        except Exception as e:
            file_result["error"] = f"Error reading file: {str(e)}"
            summary["errors"].append(f"{upload_file.filename}: {file_result['error']}")
            file_results.append(file_result)
            continue

        try:
            properties_data = parse_redfin_csv(csv_content)
        except Exception as e:
            file_result["error"] = f"Error parsing CSV: {str(e)}"
            summary["errors"].append(f"{upload_file.filename}: {file_result['error']}")
            file_results.append(file_result)
            continue

        result = service.import_properties(properties_data)

        file_result["added"] = result["added"]
        file_result["updated"] = result["updated"]
        file_result["unchanged"] = result["unchanged"]

        summary["added"] += result["added"]
        summary["updated"] += result["updated"]
        summary["unchanged"] += result["unchanged"]
        summary["price_changes"].extend(result["price_changes"])
        summary["errors"].extend(result["errors"])

        file_results.append(file_result)

    return templates.TemplateResponse(
        "import.html",
        {
            "request": request,
            "summary": summary,
            "file_results": file_results
        }
    )
