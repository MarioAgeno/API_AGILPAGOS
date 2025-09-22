from fastapi import FastAPI, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.schemas import TransaccionNotificada
from app.database import SessionLocal, AUTH_TOKEN
from app.models import Transaccion
from app.sg import router as sg_router
from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler

app = FastAPI()
security = HTTPBearer()
app.include_router(sg_router, prefix="/sg", tags=["SG"])

# Configuración del logging para registrar errores 
handler = RotatingFileHandler(
    "errores.log",
    maxBytes=1_000_000,  # 1 MB
    backupCount=5        # hasta 5 archivos .log antiguos
)
logging.basicConfig(
    handlers=[handler],
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


# Dependencia para obtener la sesión de la base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Endpoint para recibir transacciones notificadas
@app.post("/transacciones")
def recibir_transaccion(
    data: TransaccionNotificada,
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials
    if token != AUTH_TOKEN:
        return {"status": "error", "mensaje": "Token inválido"}

    try:
        # Validar duplicado
        transaccion_existente = db.query(Transaccion).filter_by(id_transaccion=data.idTransaccion).first()
        if transaccion_existente:
            return {"status": "duplicado", "mensaje": "La transacción ya existe"}

        # Registrar nueva transacción
        nueva = Transaccion(
            id_transaccion=data.idTransaccion,
            tipo=data.idTipoTransaccion,
            numero_cuenta=data.numeroCuenta,
            importe=data.importe,
            fecha_operacion=datetime.fromisoformat(data.fechaOperacion),
            cvu=data.cvu,
            observaciones=data.observaciones
        )

        db.add(nueva)
        db.commit()

        return {"status": "ok", "mensaje": "Transacción registrada correctamente"}

    except Exception as e:
        logging.error(f"Error al procesar transacción {data.idTransaccion}: {str(e)}")
        return {"status": "error_interno", "mensaje": "Error inesperado al procesar la transacción"}



# Endpoint para verificar el estado del servicio
@app.get("/status")
def status():
    return {"status": "ok"}


@app.get('/', response_class=HTMLResponse, tags=['Inicio'])
async def mensage():
    return '''
        <h1><a href='http://www.maasoft.com.ar'>MAASoft WEB</a></h1>
        <a href='http://186.189.231.237:6868/docs'>Documentacion</a>
    '''
