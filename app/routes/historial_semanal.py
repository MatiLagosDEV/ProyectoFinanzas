from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.historial_diario import HistorialDiario
from datetime import timedelta

router = APIRouter(prefix="/historial_semanal", tags=["Historial Semanal"])

@router.get("/{inversion_id}")
def historial_semanal(inversion_id: int, db: Session = Depends(get_db)):
    # Ejemplo: devolver los últimos 7 días de historial
    historiales = db.query(HistorialDiario).filter(HistorialDiario.inversion_id == inversion_id).order_by(HistorialDiario.fecha.desc()).limit(7).all()
    return historiales
