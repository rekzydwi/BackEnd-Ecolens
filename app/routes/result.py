from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date
from datetime import datetime, timezone, timedelta

from app.db.database import get_db
from app.models.user import User
from app.models.scan_result import ScanResult
from app.schemas.result import SaveResultRequest, ResultSummaryResponse, ScanResultResponse
from app.core.security import get_current_user

router = APIRouter(tags=["Result"])

@router.post("/result", response_model=ScanResultResponse, status_code=201)
def save_result(
    payload: SaveResultRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    scan = ScanResult(
        user_id=current_user.id,
        nama_makanan=payload.nama_makanan,
        confidence=payload.confidence,
        emisi_co2_kg=payload.emisi_co2_kg,
        kategori_dampak=payload.kategori_dampak,
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)
    return scan


@router.get("/result", response_model=ResultSummaryResponse)
def get_result(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    today = datetime.now(timezone.utc).date()

    all_scans = db.query(ScanResult).filter(
        ScanResult.user_id == current_user.id
    ).all()

    total_scan = len(all_scans)
    total_co2e = sum(s.emisi_co2_kg for s in all_scans if s.emisi_co2_kg is not None)

    seven_days_ago = today - timedelta(days=6)

    daily_data = (
        db.query(
            cast(ScanResult.scanned_at, Date).label("tanggal"),
            func.sum(ScanResult.emisi_co2_kg).label("total_co2")
        )
        .filter(
            ScanResult.user_id == current_user.id,
            cast(ScanResult.scanned_at, Date) >= seven_days_ago
        )
        .group_by(cast(ScanResult.scanned_at, Date))
        .all()
    )

    co2_by_date = {row.tanggal: float(row.total_co2 or 0) for row in daily_data}

    history = []
    for i in range(7):
        target_date = today - timedelta(days=i)
        history.append(co2_by_date.get(target_date, 0.0))

    return ResultSummaryResponse(
        total_scan=total_scan,
        total_co2e=round(total_co2e, 4),
        history=history
    )