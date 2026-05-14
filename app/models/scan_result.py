from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base


class ScanResult(Base):
    __tablename__ = "scan_results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    nama_makanan = Column(String(150), nullable=False)
    confidence = Column(String(20), nullable=False)
    emisi_co2_kg = Column(Float, nullable=True)
    kategori_dampak = Column(String(50), nullable=True)
    scanned_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="scan_results")