from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.inversion import Inversion

router = APIRouter(prefix="/rendimiento", tags=["Rendimiento"])

@router.get("/{inversion_id}")
def calcular_rendimiento(inversion_id: int, db: Session = Depends(get_db)):
    inversion = db.query(Inversion).filter(Inversion.id == inversion_id).first()
    if not inversion:
        raise HTTPException(status_code=404, detail="Inversión no encontrada")
    # Ejemplo simple: rendimiento = monto actual - monto inicial
    # Aquí deberías agregar la lógica real según tus necesidades
    return {"inversion_id": inversion_id, "rendimiento": 0.0}
