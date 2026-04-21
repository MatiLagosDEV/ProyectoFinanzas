from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.historial_diario import HistorialDiario
from app.schemas.historial_diario import HistorialDiario as HistorialDiarioSchema, HistorialDiarioCreate

router = APIRouter(prefix="/historial_diario", tags=["Historial Diario"])

@router.post("/", response_model=HistorialDiarioSchema)
def crear_historial(historial: HistorialDiarioCreate, db: Session = Depends(get_db)):
    db_hist = HistorialDiario(**historial.dict())
    db.add(db_hist)
    db.commit()
    db.refresh(db_hist)
    return db_hist

@router.get("/", response_model=List[HistorialDiarioSchema])
def listar_historial(db: Session = Depends(get_db)):
    return db.query(HistorialDiario).all()

@router.get("/{historial_id}", response_model=HistorialDiarioSchema)
def obtener_historial(historial_id: int, db: Session = Depends(get_db)):
    hist = db.query(HistorialDiario).filter(HistorialDiario.id == historial_id).first()
    if not hist:
        raise HTTPException(status_code=404, detail="Historial no encontrado")
    return hist

@router.delete("/{historial_id}")
def eliminar_historial(historial_id: int, db: Session = Depends(get_db)):
    hist = db.query(HistorialDiario).filter(HistorialDiario.id == historial_id).first()
    if not hist:
        raise HTTPException(status_code=404, detail="Historial no encontrado")
    db.delete(hist)
    db.commit()
    return {"ok": True}
