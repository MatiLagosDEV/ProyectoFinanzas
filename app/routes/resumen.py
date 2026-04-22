
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.inversion import Inversion
from app.models.historial_diario import HistorialDiario
from datetime import date, timedelta
import yfinance as yf

router = APIRouter(prefix="/resumen", tags=["Resumen"])

@router.get("/")
def resumen_general(db: Session = Depends(get_db)):
    inversiones = db.query(Inversion).all()
    def format_pesos(n):
        if n is None:
            return None
        return "$" + format(int(round(float(n), 0)), ",").replace(",", ".") + " CLP"

    def format_precio(n):
        if n is None:
            return None
        return f"{n:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")

    import math
    
    # Diccionario para agrupar por ticker
    acciones_dict = {}
    total_invertido_general = 0.0
    total_valor_actual_general = 0.0
    total_ganancia_general = 0.0
    total_dividendos_general = 0.0
    total_comisiones_general = 0.0
    
    # Procesar todas las inversiones y movimientos
    for inv in inversiones:
        ticker = inv.nombre
        
        if ticker not in acciones_dict:
            acciones_dict[ticker] = {
                "total_acciones": 0,
                "total_monto_comprado": 0.0,
                "precio_actual": None,
                "total_dividendos": 0.0
            }
        
        # Obtener precio actual del ticker
        precio_actual = None
        try:
            data = yf.Ticker(ticker)
            hist = data.history(period="max")
            if not hist.empty:
                precio_actual = float(hist["Close"].iloc[-1])
        except Exception:
            precio_actual = None
        
        acciones_dict[ticker]["precio_actual"] = precio_actual
        
        # Procesar movimientos
        movimientos = sorted(inv.movimientos, key=lambda m: m.fecha)
        for mov in movimientos:
            if mov.tipo.lower() == "compra":
                acciones_mov = int(mov.acciones_compradas or 0)
                acciones_dict[ticker]["total_acciones"] += acciones_mov
                acciones_dict[ticker]["total_monto_comprado"] += mov.monto or 0
                total_invertido_general += mov.monto or 0
                total_comisiones_general += mov.comision or 0
            elif mov.tipo.lower() == "venta":
                acciones_mov = int(mov.acciones_compradas or 0)
                acciones_dict[ticker]["total_acciones"] -= acciones_mov
        
        # Calcular dividendos por la fecha de pago
        try:
            data_ticker = yf.Ticker(ticker)
            dividendos = data_ticker.dividends
            if dividendos is not None and not dividendos.empty:
                for fecha_pago, dividendo_por_accion in dividendos.items():
                    if isinstance(fecha_pago, str):
                        from datetime import datetime
                        fecha_pago_dt = datetime.strptime(fecha_pago, "%Y-%m-%d").date()
                    else:
                        fecha_pago_dt = fecha_pago.date()
                    
                    acciones_en_fecha = 0
                    for mov in movimientos:
                        if mov.fecha <= fecha_pago_dt:
                            if mov.tipo.lower() == "compra":
                                acciones_en_fecha += mov.acciones_compradas or 0
                            elif mov.tipo.lower() == "venta":
                                acciones_en_fecha -= mov.acciones_compradas or 0
                    
                    recibido = round(acciones_en_fecha * float(dividendo_por_accion), 2)
                    acciones_dict[ticker]["total_dividendos"] += recibido
                    total_dividendos_general += recibido
        except Exception:
            pass
    
    # Construir array por acción (agrupado)
    por_accion = []
    for ticker, datos in acciones_dict.items():
        total_acciones = datos["total_acciones"]
        total_monto = datos["total_monto_comprado"]
        precio_act = datos["precio_actual"]
        total_divs = datos["total_dividendos"]
        
        precio_compra_promedio = None
        if total_acciones > 0:
            precio_compra_promedio = total_monto / total_acciones
            # Si el precio actual existe y es cercano al calculado (diferencia < 1%), 
            # usa el precio actual para evitar inconsistencias de redondeo
            if precio_act is not None and abs(precio_compra_promedio - precio_act) / precio_act < 0.01:
                precio_compra_promedio = precio_act
        
        # Si no hay precio actual de yfinance, usar precio de compra promedio
        precio_para_calculo = precio_act if precio_act is not None else precio_compra_promedio
        valor_actual = total_acciones * precio_para_calculo if precio_para_calculo is not None else 0
        total_valor_actual_general += valor_actual
        
        ganancia = valor_actual - (total_acciones * precio_compra_promedio if precio_compra_promedio else 0) + total_divs
        total_ganancia_general += ganancia
        
        por_accion.append({
            "ticker": ticker,
            "cantidad_acciones": total_acciones,
            "precio_compra_promedio": format_precio(precio_compra_promedio),
            "precio_actual": format_precio(precio_act),
            "valor_actual": format_pesos(valor_actual),
            "dividendos_recibidos": format_pesos(total_divs),
            "ganancia_perdida": format_pesos(ganancia)
        })
    
    # Construir array con cada compra por separado
    compras_detalladas = []
    # Primero calcular promedios por ticker usando TODAS las compras de cada ticker
    promedios_por_ticker = {}
    for inv in inversiones:
        ticker = inv.nombre
        if ticker not in promedios_por_ticker:
            promedios_por_ticker[ticker] = {"total_monto": 0, "total_acciones": 0}
        
        for mov in inv.movimientos:
            if mov.tipo.lower() == "compra":
                promedios_por_ticker[ticker]["total_monto"] += mov.monto or 0
                promedios_por_ticker[ticker]["total_acciones"] += mov.acciones_compradas or 0
    
    # Calcular el promedio final para cada ticker
    for ticker in promedios_por_ticker:
        if promedios_por_ticker[ticker]["total_acciones"] > 0:
            promedios_por_ticker[ticker] = promedios_por_ticker[ticker]["total_monto"] / promedios_por_ticker[ticker]["total_acciones"]
        else:
            promedios_por_ticker[ticker] = None
    
    for inv in inversiones:
        ticker = inv.nombre
        precio_actual = None
        try:
            data = yf.Ticker(ticker)
            hist = data.history(period="max")
            if not hist.empty:
                precio_actual = float(hist["Close"].iloc[-1])
        except Exception:
            precio_actual = None
        
        for mov in sorted(inv.movimientos, key=lambda m: m.fecha):
            if mov.tipo.lower() == "compra":
                # Obtener precio histórico de la fecha de compra desde yfinance
                precio_compra_real = None
                try:
                    data = yf.Ticker(ticker)
                    hist = data.history(start=mov.fecha, end=mov.fecha + timedelta(days=1))
                    if not hist.empty:
                        precio_compra_real = float(hist["Close"].iloc[-1])
                except Exception:
                    precio_compra_real = None
                
                # Si yfinance falla, usar precio calculado como fallback
                if precio_compra_real is None and mov.acciones_compradas and mov.acciones_compradas > 0:
                    precio_compra_real = (mov.monto or 0) / mov.acciones_compradas
                
                valor_actual_compra = (mov.acciones_compradas * precio_actual) if precio_actual and mov.acciones_compradas else 0
                ganancia_compra = valor_actual_compra - (mov.monto or 0)
                
                # Calcular dividendos recibidos desde esta compra hasta hoy
                dividendos_compra = 0.0
                try:
                    data_ticker = yf.Ticker(ticker)
                    dividendos = data_ticker.dividends
                    if dividendos is not None and not dividendos.empty:
                        for fecha_pago, dividendo_por_accion in dividendos.items():
                            if isinstance(fecha_pago, str):
                                from datetime import datetime
                                fecha_pago_dt = datetime.strptime(fecha_pago, "%Y-%m-%d").date()
                            else:
                                fecha_pago_dt = fecha_pago.date()
                            
                            # Solo contar dividendos después de esta compra
                            if fecha_pago_dt >= mov.fecha:
                                dividendos_compra += mov.acciones_compradas * float(dividendo_por_accion)
                except Exception:
                    dividendos_compra = 0.0
                
                compras_detalladas.append({
                    "ticker": ticker,
                    "fecha": str(mov.fecha),
                    "cantidad_acciones": mov.acciones_compradas,
                    "broker": mov.broker or "No especificado",
                    "comision": format_pesos(mov.comision),
                    "comision_porcentaje": f"{mov.comision_porcentaje}%" if mov.comision_porcentaje else "0%",
                    "monto_bruto": format_pesos(mov.monto),
                    "monto_neto": format_pesos((mov.monto or 0) - (mov.comision or 0)),
                    "precio_compra": format_precio(precio_compra_real),
                    "precio_compra_promedio": format_precio(promedios_por_ticker.get(ticker)),
                    "precio_actual": format_precio(precio_actual),
                    "valor_actual": format_pesos(valor_actual_compra),
                    "dividendos_recibidos": format_pesos(dividendos_compra),
                    "ganancia_perdida": format_pesos(ganancia_compra)
                })
    
    return {
        "resumen_general": {
            "total_invertido": format_pesos(total_invertido_general),
            "valor_portafolio_actual": format_pesos(total_valor_actual_general),
            "dividendos_recibidos": format_pesos(total_dividendos_general),
            "ganancia_perdida": format_pesos(total_ganancia_general),
            "cantidad_inversiones": len(inversiones)
        },
        "por_accion": por_accion,
        "compras_detalladas": compras_detalladas
    }

# Nuevo endpoint para resumen de dividendos
@router.get("/dividendos")
def resumen_dividendos(db: Session = Depends(get_db)):
    inversiones = db.query(Inversion).all()
    total_dividendos = 0.0
    detalle = []
    import requests
    for inv in inversiones:
        ticker = inv.nombre  # Asumimos que el nombre es el ticker
        dividendos = None
        # Intentar obtener dividendos con yfinance
        try:
            data = yf.Ticker(ticker)
            dividendos = data.dividends
        except Exception:
            dividendos = None

        # Si yfinance falla o está vacío, intenta con el endpoint interno
        if dividendos is None or dividendos.empty:
            try:
                url = f"http://localhost:8000/precios/{ticker}/dividendos"
                r = requests.get(url)
                if r.status_code == 200:
                    data = r.json()
                    if "dividendos" in data and isinstance(data["dividendos"], list):
                        dividendos = {d["fecha"]: d["dividendo"] for d in data["dividendos"]}
            except Exception:
                dividendos = None

        if dividendos is None or (hasattr(dividendos, 'empty') and dividendos.empty) or (isinstance(dividendos, dict) and not dividendos):
            detalle.append({"ticker": ticker, "dividendos": 0.0, "detalle": []})
            continue

        # Obtener movimientos ordenados por fecha
        movimientos = sorted(inv.movimientos, key=lambda m: m.fecha)
        pagos = []
        total_real = 0.0
        for fecha_pago, dividendo_por_accion in (dividendos.items() if isinstance(dividendos, dict) else dividendos.items()):
            # Si la fecha es string, conviértela a date
            if isinstance(fecha_pago, str):
                from datetime import datetime
                fecha_pago_dt = datetime.strptime(fecha_pago, "%Y-%m-%d").date()
            else:
                fecha_pago_dt = fecha_pago.date()
            acciones = 0
            for mov in movimientos:
                if mov.fecha <= fecha_pago_dt:
                    if mov.tipo.lower() == "compra":
                        acciones += mov.acciones_compradas or 0
                    elif mov.tipo.lower() == "venta":
                        acciones -= mov.acciones_compradas or 0
            recibido = round(acciones * float(dividendo_por_accion), 2)
            pagos.append({
                "fecha": str(fecha_pago_dt),
                "acciones": acciones,
                "dividendo_por_accion": round(float(dividendo_por_accion), 2),
                "recibido": recibido
            })
            total_real += recibido
        total_real = round(total_real, 2)
        total_dividendos += total_real
        detalle.append({"ticker": ticker, "dividendos": total_real, "moneda": "CLP", "detalle": pagos})
        # Guardar en historial diario
        hist = HistorialDiario(
            inversion_id=inv.id,
            fecha=date.today(),
            valor=total_real
        )
        db.add(hist)
    db.commit()
    return {"total_dividendos": round(total_dividendos, 2), "moneda": "CLP", "detalle": detalle}

