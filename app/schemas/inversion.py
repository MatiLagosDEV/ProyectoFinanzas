from pydantic import BaseModel
from typing import Optional, List
from datetime import date


class MovimientoBase(BaseModel):
    tipo: str
    monto: float
    acciones_compradas: Optional[float] = None
    fecha: date
    comision: Optional[float] = None
    broker: Optional[str] = "Banco Santander"
    comision_porcentaje: Optional[float] = None


class MovimientoCreate(MovimientoBase):
    pass


class Movimiento(MovimientoBase):
    id: int
    class Config:
        orm_mode = True

class InversionBase(BaseModel):
    nombre: str
    tipo: str
    monto: float
    fecha: date
    moneda: str

class InversionCreate(InversionBase):
    pass

class Inversion(InversionBase):
    id: int
    movimientos: List[Movimiento] = []
    class Config:
        orm_mode = True
