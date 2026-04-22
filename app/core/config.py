# Configuración de brokers y comisiones para Chile

IVA_PORCENTAJE = 19.0  # IVA en Chile es 19%

BROKERS = {
    "Banco Santander": {
        "comision_porcentaje": 0.35,
        "descripcion": "Corretora tradicional"
    },
    "Itaú": {
        "comision_porcentaje": 0.30,
        "descripcion": "Corretora tradicional"
    },
    "BCI": {
        "comision_porcentaje": 0.25,
        "descripcion": "Corretora tradicional"
    },
    "Banchile en línea": {
        "comision_porcentaje": 0.15,
        "descripcion": "Plataforma moderna"
    },
    "Interactive Brokers": {
        "comision_porcentaje": 0.10,
        "descripcion": "Plataforma internacional"
    }
}

BROKER_DEFAULT = "Banco Santander"

def obtener_comision_porcentaje(broker: str) -> float:
    """Obtiene el porcentaje de comisión para un broker"""
    if broker in BROKERS:
        return BROKERS[broker]["comision_porcentaje"]
    return BROKERS[BROKER_DEFAULT]["comision_porcentaje"]

def calcular_comision_neta(monto: float, broker: str) -> float:
    """Calcula solo la comisión neta (sin IVA)"""
    porcentaje = obtener_comision_porcentaje(broker)
    return round(monto * (porcentaje / 100), 2)

def calcular_iva_comision(monto: float, broker: str) -> float:
    """Calcula el IVA sobre la comisión (19%)"""
    comision_neta = calcular_comision_neta(monto, broker)
    return round(comision_neta * (IVA_PORCENTAJE / 100), 2)

def calcular_comision(monto: float, broker: str) -> float:
    """Calcula el monto total de comisión (incluye IVA)
    Esto es lo que realmente cobra el banco en Chile"""
    comision_neta = calcular_comision_neta(monto, broker)
    iva = calcular_iva_comision(monto, broker)
    return round(comision_neta + iva, 2)

def calcular_monto_neto(monto: float, broker: str) -> float:
    """Calcula el monto neto después de comisión (incluye IVA)"""
    comision_total = calcular_comision(monto, broker)
    return round(monto - comision_total, 2)
