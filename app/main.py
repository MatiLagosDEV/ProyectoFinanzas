from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import engine, Base
from app.routes import inversion, movimiento, historial_diario, rendimiento, resumen, historial_semanal, precios, acciones_chile, dividendos, dividendos_personales

app = FastAPI()

# Configurar CORS para permitir peticiones desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Crea las tablas en la base de datos
Base.metadata.create_all(bind=engine)

@app.get("/")
def read_root():
    return {"mensaje": "API de Inversiones funcionando"}

app.include_router(inversion.router)
app.include_router(movimiento.router)
app.include_router(historial_diario.router)
app.include_router(rendimiento.router)
app.include_router(resumen.router)
app.include_router(historial_semanal.router)
app.include_router(precios.router)
app.include_router(acciones_chile.router)
app.include_router(dividendos.router)
app.include_router(dividendos_personales.router)
