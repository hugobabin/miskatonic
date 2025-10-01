from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from backend.services.secure import require_roles
from backend.services.etl_adapter import run_etl_from_upload
from backend.models.api_etl import EtlImportResponse

router = APIRouter(prefix="/etl", tags=["etl"])
ALLOWED_CT = {"text/csv"}

RequireTeacherOrAdmin = Depends(require_roles({"teacher", "admin"}))

@router.post(
    "/import",
    status_code=201,
    summary="Import a CSV file of questions",
    response_model=EtlImportResponse,
)

def import_csv(file: UploadFile = File(..., description="CSV UTF-8"), _user = RequireTeacherOrAdmin):
    # 1) type MIME (the type and purpose of a file)
    if file.content_type not in ALLOWED_CT:
        raise HTTPException(status_code=415, detail="content_type must be text/csv")

    # 2) try reading uploaded file; return 400 if it fails
    try:
        data = file.file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"read_error: {e}")

    # 3) author forced from token
    author = _user[1]

    # 4) execute ETL
    try:
        filename = file.filename if file.filename else "questions.csv"
        fname, stats = run_etl_from_upload(filename, data, author)
    except ValueError as ve:               # ex: "No valid data from uploaded CSV"
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"etl_error: {e}")

    return EtlImportResponse(file=fname, stats=stats)
