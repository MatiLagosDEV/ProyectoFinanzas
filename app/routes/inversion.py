from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import yfinance as yf
from app.core.database import get_db
from app.core.config import obtener_comision_porcentaje, calcular_comision, BROKER_DEFAULT
from app.models.inversion import Inversion, Movimiento
from app.schemas.inversion import Inversion as InversionSchema, InversionCreate, Movimiento as MovimientoSchema, MovimientoCreate

from app.schemas.inversion import InversionBase, MovimientoBase

router = APIRouter(prefix="/inversiones", tags=["Inversiones"])

@router.post("/", response_model=InversionSchema)
def crear_inversion(inversion: InversionCreate, db: Session = Depends(get_db)):
    db_inversion = Inversion(**inversion.dict())
    db.add(db_inversion)
    db.commit()
    db.refresh(db_inversion)
    # Crear automáticamente el primer movimiento de compra con el monto de la inversión
    # Obtener el precio de compra de yfinance
    import math
    precio_compra = None
    try:
        data = yf.Ticker(db_inversion.nombre)
        hist = data.history(period="max")
        if not hist.empty:
            fechas_validas = hist.loc[:str(db_inversion.fecha)]
            if not fechas_validas.empty:
                precio_compra = float(fechas_validas["Close"].iloc[-1])
    except Exception:
        precio_compra = None
    # Calcular acciones compradas (como en resumen)
    acciones_compradas = None
    if precio_compra and precio_compra > 0:
        acciones_compradas_decimal = db_inversion.monto / precio_compra
        acciones_compradas = round(acciones_compradas_decimal, 2)  # Mantener decimales
    
    # Calcular comisión usando Banco Santander por defecto
    broker = BROKER_DEFAULT
    comision_porcentaje = obtener_comision_porcentaje(broker)
    comision_monto = calcular_comision(db_inversion.monto, broker)
    
    movimiento = Movimiento(
        inversion_id=db_inversion.id,
        tipo="compra",
        monto=db_inversion.monto,
        acciones_compradas=acciones_compradas,
        fecha=db_inversion.fecha,
        comision=comision_monto,
        broker=broker,
        comision_porcentaje=comision_porcentaje
    )
    db.add(movimiento)
    db.commit()
    db.refresh(db_inversion)
    return db_inversion


@router.get("/")
def listar_inversiones(db: Session = Depends(get_db)):
    inversiones = db.query(Inversion).all()
    def format_pesos(n):
        if n is None:
            return None
        # Mantener precisión interna con decimales, pero mostrar sin decimales (formato chileno)
        rounded = round(float(n), 0)  # Redondear a entero para mostrar
        formatted = f"{int(rounded):,}".replace(",", ".")
        return "$" + formatted + " CLP"

    def format_precio(n):
        if n is None:
            return None
        return f"{n:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
    resultado = []
    for inv in inversiones:
        precio_actual = None
        precio_compra = None
        try:
            data = yf.Ticker(inv.nombre)
            hist = data.history(period="max")
            if not hist.empty:
                precio_actual = float(hist["Close"].iloc[-1])
                fechas_validas = hist.loc[:str(inv.fecha)]
                if not fechas_validas.empty:
                    precio_compra = float(fechas_validas["Close"].iloc[-1])
                else:
                    precio_compra = None
        except Exception:
            precio_actual = None
            precio_compra = None
        resultado.append({
            "id": inv.id,
            "nombre": inv.nombre,
            "tipo": inv.tipo,
            "monto": format_pesos(inv.monto),
            "precio_compra": format_precio(precio_compra),
            "precio_actual": format_precio(precio_actual),
            "fecha": inv.fecha,
            "moneda": inv.moneda,
            "acciones_compradas": int(sum(m.acciones_compradas or 0 for m in inv.movimientos if m.tipo.lower() == "compra") - sum(m.acciones_compradas or 0 for m in inv.movimientos if m.tipo.lower() == "venta")),
            "movimientos": [
                {
                    "id": m.id,
                    "tipo": m.tipo,
                    "monto": format_pesos(m.monto),
                    "acciones_compradas": int(m.acciones_compradas) if m.acciones_compradas is not None else None,
                    "fecha": m.fecha,
                    "broker": m.broker or "Banco Santander",
                    "comision_porcentaje": f"{m.comision_porcentaje}%" if m.comision_porcentaje is not None else None,
                    "comision": format_pesos(m.comision) if m.comision is not None else None
                } for m in inv.movimientos
            ]
        })
    return resultado

@router.get("/{inversion_id}", response_model=InversionSchema)
def obtener_inversion(inversion_id: int, db: Session = Depends(get_db)):
    inv = db.query(Inversion).filter(Inversion.id == inversion_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Inversión no encontrada")
    return inv

@router.delete("/{inversion_id}")
def eliminar_inversion(inversion_id: int, db: Session = Depends(get_db)):
    inv = db.query(Inversion).filter(Inversion.id == inversion_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Inversión no encontrada")
    db.delete(inv)
    db.commit()
    return {"ok": True}


# Endpoint para actualizar una inversión
@router.put("/{inversion_id}", response_model=InversionSchema)
def actualizar_inversion(inversion_id: int, inversion: InversionBase, db: Session = Depends(get_db)):
    db_inv = db.query(Inversion).filter(Inversion.id == inversion_id).first()
    if not db_inv:
        raise HTTPException(status_code=404, detail="Inversión no encontrada")

    # Solo actualizar los campos definidos en InversionBase
    data = inversion.dict(exclude_unset=True)
    for key, value in data.items():
        setattr(db_inv, key, value)
    db.commit()
    db.refresh(db_inv)
    return db_inv



# Endpoint para agregar un movimiento a una inversión

@router.post("/{inversion_id}/movimientos", response_model=MovimientoSchema)
def agregar_movimiento(inversion_id: int, movimiento: MovimientoCreate, db: Session = Depends(get_db)):
    inv = db.query(Inversion).filter(Inversion.id == inversion_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Inversión no encontrada")
    db_mov = Movimiento(**movimiento.dict(), inversion_id=inversion_id)
    db.add(db_mov)
    db.commit()
    db.refresh(db_mov)
    # Actualizar el monto de la inversión según el tipo de movimiento
    if db_mov.tipo.lower() == "compra":
        inv.monto += db_mov.monto
    elif db_mov.tipo.lower() == "venta":
        inv.monto -= db_mov.monto
    db.commit()
    db.refresh(inv)
    return db_mov


# Endpoint para actualizar un movimiento
@router.put("/{inversion_id}/movimientos/{movimiento_id}", response_model=MovimientoSchema)
def actualizar_movimiento(inversion_id: int, movimiento_id: int, movimiento: MovimientoBase, db: Session = Depends(get_db)):
    db_mov = db.query(Movimiento).filter(Movimiento.id == movimiento_id, Movimiento.inversion_id == inversion_id).first()
    if not db_mov:
        raise HTTPException(status_code=404, detail="Movimiento no encontrado")
    # Antes de actualizar, revertir el efecto anterior en la inversión
    inv = db.query(Inversion).filter(Inversion.id == inversion_id).first()
    if db_mov.tipo.lower() == "compra":
        inv.monto -= db_mov.monto
    elif db_mov.tipo.lower() == "venta":
        inv.monto += db_mov.monto

    # Actualizar el movimiento
    for key, value in movimiento.dict().items():
        setattr(db_mov, key, value)
    db.commit()
    db.refresh(db_mov)

    # Aplicar el nuevo efecto del movimiento actualizado
    if db_mov.tipo.lower() == "compra":
        inv.monto += db_mov.monto
    elif db_mov.tipo.lower() == "venta":
        inv.monto -= db_mov.monto
    db.commit()
    db.refresh(inv)
    return db_mov
