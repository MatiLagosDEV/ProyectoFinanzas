from fastapi import APIRouter
import json
import os

router = APIRouter(prefix="/acciones_chile", tags=["Acciones Chile"])

@router.get("/")
def listar_acciones():
    ruta = os.path.join(os.path.dirname(__file__), "../data/acciones_chile_completo.json")
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            acciones = json.load(f)
        return acciones
    except Exception:
        return []
