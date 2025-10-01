from pydantic import BaseModel

class EtlStats(BaseModel):
    accepted: int
    rejected: int
    total: int

class EtlImportResponse(BaseModel):
    file: str
    stats: EtlStats
