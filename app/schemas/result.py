from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class SaveResultRequest(BaseModel):
    nama_makanan: str
    confidence: str
    emisi_co2_kg: Optional[float] = None
    kategori_dampak: Optional[str] = None


class ScanResultResponse(BaseModel):
    id: int
    nama_makanan: str
    confidence: str
    emisi_co2_kg: Optional[float]
    kategori_dampak: Optional[str]
    scanned_at: datetime

    model_config = {"from_attributes": True}


class ResultSummaryResponse(BaseModel):
    total_scan: int
    total_co2e: float
    history: List[float]  # 7 angka, index 0 = hari ini, index 6 = 6 hari lalu