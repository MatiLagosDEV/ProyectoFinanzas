from sqlalchemy import Column, Integer, Float, Date, ForeignKey
from app.core.database import Base

class HistorialDiario(Base):
    __tablename__ = "historial_diario"
    id = Column(Integer, primary_key=True, index=True)
    inversion_id = Column(Integer, ForeignKey("inversiones.id"))
    fecha = Column(Date)
    valor = Column(Float)
