# ...existing code...
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Request
from fastapi.responses import ORJSONResponse, FileResponse
from pathlib import Path

from services.secure import require_roles
from services.etl_adapter import run_etl_from_upload
from models.api_etl import EtlImportResponse

router = APIRouter(prefix="/etl", tags=["etl"])
RequireTeacherOrAdmin = Depends(require_roles({"teacher", "admin"}))

ALLOWED_CT = {"text/csv", "application/vnd.ms-excel", "application/csv", "text/plain"}

DATA_LOG = Path("data/log").resolve()


@router.post(
    "/import",
    status_code=201,
    summary="Import a CSV file of questions",
    name="etl_import_apply",
)
async def import_csv(
    request: Request,
    file: UploadFile = File(..., description="CSV UTF-8"),
    _user=RequireTeacherOrAdmin,
) -> ORJSONResponse:
    # REFACTORING MVT // API REST pour importer CSV : renvoie JSON avec stats ou erreur
    if file.content_type not in ALLOWED_CT:
        return ORJSONResponse(
            content={
                "success": False,
                "message": f"Type de fichier invalide ({file.content_type})",
            },
            status_code=400,
        )

    author = _user["username"]
    try:
        filename = file.filename or "questions.csv"
        data = await file.read()
        stats, rapport_path = run_etl_from_upload(filename, data, author)
        # Provide endpoint to download rapport
        rapport_name = rapport_path.name if rapport_path else None
        return ORJSONResponse(
            content={"success": True, "file": rapport_name, "stats": stats}
        )
    except ValueError as ve:
        return ORJSONResponse(
            content={"success": False, "message": str(ve)}, status_code=400
        )
    except Exception as e:
        return ORJSONResponse(
            content={"success": False, "message": f"Erreur ETL: {e}"}, status_code=500
        )


@router.get("/rapport/{name}", name="etl_get_rapport")
def etl_get_rapport(name: str, _user=RequireTeacherOrAdmin):
    # REFACTORING MVT // Téléchargement du rapport conservé côté API
    rapport_path = (DATA_LOG / name).resolve()
    if not str(rapport_path).startswith(str(DATA_LOG)) or not rapport_path.exists():
        raise HTTPException(404, "Rapport introuvable")
    return FileResponse(rapport_path, media_type="text/csv", filename=name)


# ...existing code...
