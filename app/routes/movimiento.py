from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.config import obtener_comision_porcentaje, calcular_comision, BROKERS
from app.models.inversion import Movimiento
from app.schemas.inversion import Movimiento as MovimientoSchema, MovimientoCreate

router = APIRouter(prefix="/movimientos", tags=["Movimientos"])

@router.get("/brokers/disponibles")
def listar_brokers():
    """Lista todos los brokers disponibles con sus comisiones"""
    return {
        broker: {
            "comision_porcentaje": datos["comision_porcentaje"],
            "descripcion": datos["descripcion"]
        }
        for broker, datos in BROKERS.items()
    }

@router.post("/", response_model=MovimientoSchema)
def crear_movimiento(movimiento: MovimientoCreate, db: Session = Depends(get_db)):
    # Obtener el porcentaje de comisión según el broker
    broker = movimiento.broker or "Banco Santander"
    comision_porcentaje = obtener_comision_porcentaje(broker)
    comision_monto = calcular_comision(movimiento.monto, broker)
    
    # Crear el movimiento con la comisión calculada
    db_mov = Movimiento(
        **movimiento.dict(exclude={"comision", "comision_porcentaje"}),
        broker=broker,
        comision=comision_monto,
        comision_porcentaje=comision_porcentaje
    )
    db.add(db_mov)
    db.commit()
    db.refresh(db_mov)
    return db_mov

@router.get("/", response_model=List[MovimientoSchema])
def listar_movimientos(db: Session = Depends(get_db)):
    return db.query(Movimiento).all()

@router.get("/{movimiento_id}", response_model=MovimientoSchema)
def obtener_movimiento(movimiento_id: int, db: Session = Depends(get_db)):
    mov = db.query(Movimiento).filter(Movimiento.id == movimiento_id).first()
    if not mov:
        raise HTTPException(status_code=404, detail="Movimiento no encontrado")
    return mov

@router.delete("/{movimiento_id}")
def eliminar_movimiento(movimiento_id: int, db: Session = Depends(get_db)):
    mov = db.query(Movimiento).filter(Movimiento.id == movimiento_id).first()
    if not mov:
        raise HTTPException(status_code=404, detail="Movimiento no encontrado")
    db.delete(mov)
    db.commit()
    return {"ok": True}
