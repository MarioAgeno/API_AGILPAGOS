from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas import TransaccionNotificada
from app.database import SessionLocal
from app.models import Transaccion
from datetime import datetime
import logging
from fastapi import Header
from app.database import AUTH_TOKEN
from fastapi.security import HTTPBearer
from fastapi import Security
from fastapi.security import HTTPAuthorizationCredentials

app = FastAPI()
security = HTTPBearer()

# Configuración del logging para registrar errores 
logging.basicConfig(
    filename="errores.log",
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
        raise HTTPException(status_code=401, detail="Token inválido")
    try:
        # Validar duplicado
        transaccion_existente = db.query(Transaccion).filter_by(id_transaccion=data.idTransaccion).first()
        if transaccion_existente:
            return { "status": "duplicado", "mensaje": "La transacción ya fue recibida anteriormente" }


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

        return {"status": "ok"}

    except Exception as e:
        logging.error(f"Error al procesar transacción {data.idTransaccion}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno")


# Endpoint para verificar el estado del servicio
@app.get("/status")
def status():
    return {"status": "ok"}
