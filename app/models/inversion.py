from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class Inversion(Base):
    __tablename__ = "inversiones"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, index=True)
    tipo = Column(String)
    monto = Column(Float)
    fecha = Column(Date)
    moneda = Column(String)
    movimientos = relationship("Movimiento", back_populates="inversion")

class Movimiento(Base):
    __tablename__ = "movimientos"
    id = Column(Integer, primary_key=True, index=True)
    inversion_id = Column(Integer, ForeignKey("inversiones.id"))
    tipo = Column(String)
    monto = Column(Float)
    acciones_compradas = Column(Float, nullable=True)
    fecha = Column(Date)
    comision = Column(Float, nullable=True)
    broker = Column(String, default="Banco Santander")
    comision_porcentaje = Column(Float, nullable=True)
    inversion = relationship("Inversion", back_populates="movimientos")
