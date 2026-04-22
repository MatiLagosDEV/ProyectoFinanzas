# Configuración de brokers y comisiones para Chile

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

def calcular_comision(monto: float, broker: str) -> float:
    """Calcula el monto de comisión"""
    porcentaje = obtener_comision_porcentaje(broker)
    return round(monto * (porcentaje / 100), 2)

def calcular_monto_neto(monto: float, broker: str) -> float:
    """Calcula el monto neto después de comisión"""
    comision = calcular_comision(monto, broker)
    return round(monto - comision, 2)
