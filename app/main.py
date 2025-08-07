from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from app.schemas import TransaccionNotificada
from app.database import SessionLocal
from app.models import Transaccion
from datetime import datetime

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/transacciones")
def recibir_transaccion(data: TransaccionNotificada, db: Session = Depends(get_db)):
    transaccion = Transaccion(
        id_transaccion=data.idTransaccion,
        tipo=data.idTipoTransaccion,
        numero_cuenta=data.numeroCuenta,
        importe=data.importe,
        fecha_operacion=datetime.fromisoformat(data.fechaOperacion),
        cvu=data.CVU,
        observaciones=data.observaciones
    )

    db.add(transaccion)
    db.commit()
    return {"status": "ok"}
