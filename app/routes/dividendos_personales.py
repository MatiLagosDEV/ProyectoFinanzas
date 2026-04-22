from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.inversion import Inversion
import yfinance as yf

router = APIRouter(prefix="/dividendos_personales", tags=["Dividendos Personales"])

def format_pesos(n):
    if n is None:
        return None
    # Mantener precisión interna con decimales, pero mostrar sin decimales (formato chileno)
    rounded = round(float(n), 0)  # Redondear a entero para mostrar
    formatted = f"{int(rounded):,}".replace(",", ".")
    return "$" + formatted + " CLP"

@router.get("/{inversion_id}")
def dividendos_personales(inversion_id: int, db: Session = Depends(get_db)):
    inversion = db.query(Inversion).filter(Inversion.id == inversion_id).first()
    if not inversion:
        return {"error": "Inversión no encontrada"}
    
    ticker = inversion.nombre
    total_dividendos = 0.0
    detalle = []
    
    # Obtener dividendos históricos
    try:
        data = yf.Ticker(ticker)
        dividendos = data.dividends
        if dividendos is None or dividendos.empty:
            return {
                "ticker": ticker,
                "total_dividendos": format_pesos(0.0),
                "detalle": []
            }
    except Exception:
        return {
            "ticker": ticker,
            "total_dividendos": format_pesos(0.0),
            "detalle": []
        }
    
    # Obtener movimientos ordenados por fecha
    movimientos = sorted(inversion.movimientos, key=lambda m: m.fecha)
    
    # Calcular dividendos para cada fecha de pago
    for fecha_pago, dividendo_por_accion in dividendos.items():
        if isinstance(fecha_pago, str):
            from datetime import datetime
            fecha_pago_dt = datetime.strptime(fecha_pago, "%Y-%m-%d").date()
        else:
            fecha_pago_dt = fecha_pago.date()
        
        acciones = 0
        for mov in movimientos:
            if mov.fecha <= fecha_pago_dt:
                if mov.tipo.lower() == "compra":
                    acciones += int(mov.acciones_compradas or 0)
                elif mov.tipo.lower() == "venta":
                    acciones -= int(mov.acciones_compradas or 0)
        
        recibido = round(acciones * float(dividendo_por_accion), 2)
        if acciones > 0:
            detalle.append({
                "fecha_pago": str(fecha_pago_dt),
                "acciones": acciones,
                "dividendo_por_accion": round(float(dividendo_por_accion), 2),
                "recibido": recibido
            })
            total_dividendos += recibido
    
    return {
        "ticker": ticker,
        "total_dividendos": format_pesos(total_dividendos),
        "detalle": detalle
    }
