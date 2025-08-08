from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas import TransaccionNotificada
from app.database import SessionLocal
from app.models import Transaccion
from datetime import datetime
import logging, json
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Security
from fastapi.responses import HTMLResponse
from app.database import AUTH_TOKEN
from logging.handlers import RotatingFileHandler

app = FastAPI()
security = HTTPBearer()

# Logging rotativo para evitar crecimiento indefinido
handler = RotatingFileHandler(
    "errores.log", maxBytes=1_000_000, backupCount=5
)
logging.basicConfig(
    handlers=[handler],
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# DB Session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/transacciones")
def recibir_transaccion(
    data: TransaccionNotificada,
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials
    if token != AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="Token inválido")
    try:
        transaccion_existente = db.query(Transaccion).filter_by(id_transaccion=data.idTransaccion).first()
        if transaccion_existente:
            return {"status": "duplicado"}

        nueva = Transaccion(
            id_transaccion=data.idTransaccion,
            tipo=data.idTipoTransaccion,
            numero_cuenta=data.numeroCuenta,
            importe=data.importe,
            fecha_operacion=datetime.fromisoformat(data.fechaOperacion),
            cvu=data.cvu,
            observaciones=data.observaciones,
            payload_raw=json.dumps(data.dict(by_alias=True))
        )

        db.add(nueva)
        db.commit()

        return {"status": "ok"}
    except Exception as e:
        logging.error(f"Error al procesar transacción {data.idTransaccion}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno")

@app.get("/", response_class=HTMLResponse, tags=["Inicio"])
async def mensaje():
    return '''
        <h1><a href='http://www.maasoft.com.ar'>MAASoft WEB</a></h1>
        <a href='/docs'>Documentación Swagger</a>
    '''

@app.get("/status")
def status():
    return {"status": "ok"}