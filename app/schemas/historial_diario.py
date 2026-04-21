from pydantic import BaseModel
from datetime import date

class HistorialDiarioBase(BaseModel):
    fecha: date
    valor: float

class HistorialDiarioCreate(HistorialDiarioBase):
    inversion_id: int

class HistorialDiario(HistorialDiarioBase):
    id: int
    inversion_id: int
    class Config:
        orm_mode = True
