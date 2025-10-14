from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse
from pathlib import Path

from src.services.secure import require_roles
from src.services.etl_adapter import run_etl_from_upload
from src.models.api_etl import EtlImportResponse
from src.services.util import get_templates

# ETL router declaration
router = APIRouter(prefix="/etl", tags=["etl"])
# Role verification dependency
RequireTeacherOrAdmin = Depends(require_roles({"teacher", "admin"}))

ALLOWED_CT = {"text/csv","application/vnd.ms-excel","application/csv"}

# Directory where ETL rapports are generated
DATA_LOG = Path("data/log").resolve()

# 1)HTML import page endpoint
@router.get("/", response_class=HTMLResponse)
def etl_page(request: Request, _user=RequireTeacherOrAdmin):
    # page with a file upload form
    return get_templates().TemplateResponse("etl_import.html", {"request": request})

# 2) import CSV file endpoint
@router.post("/import",status_code=201,summary="Import a CSV file of questions",
    response_model=EtlImportResponse,
)
async def import_csv(request:Request, file: UploadFile = File(..., description="CSV UTF-8"), _user = RequireTeacherOrAdmin):
    # 1) type MIME (the type and purpose of a file)
    if file.content_type not in ALLOWED_CT:
        return get_templates().TemplateResponse(
            "etl_import.html",
            {
                "request": request,
                "error": f"Type de fichier invalide ({file.content_type}). "
                         f"Veuillez importer un CSV."
            },
            status_code=400
        )
    author = _user["username"]
    # 2) try reading uploaded file; return 400 if it fails
    try:
        # Run the ETL pipeline
        filename = file.filename or "questions.csv"
        data = await file.read()
        stats, rapport_path = run_etl_from_upload(filename, data, author)
        rapport_url = request.url_for("etl_get_rapport", name=rapport_path.name)
        return get_templates().TemplateResponse(
            "etl_import.html",
            {
                "request": request,
                "stats": stats,
                "rapport_url": rapport_url
            },
        )
    except ValueError as ve:
        # ETL process returns
        return get_templates().TemplateResponse(
        "etl_import.html",
        {"request": request, "error": str(ve)},
        status_code=400
    )
    except Exception as e:
    # unexpected error case
        return get_templates().TemplateResponse(
        "etl_import.html",
        {"request": request, "error": f"Erreur ETL: {e}"},
        status_code=500
    )

# 3) get rapport file endpoint
@router.get("/rapport/{name}", name="etl_get_rapport")
def etl_get_rapport(name: str, _user=RequireTeacherOrAdmin):
    rapport_path = (DATA_LOG / name).resolve()
     # Security check: the file must exist and remain within the DATA_LOG folder
    if not str(rapport_path).startswith(str(DATA_LOG)) or not rapport_path.exists():
        raise HTTPException(404, "Rapport introuvable")

    # Return the CSV file as a download
    return FileResponse(
        rapport_path,
        media_type="text/csv",
        filename=name
    )
