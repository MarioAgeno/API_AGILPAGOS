from sqlalchemy import Column, String, Float, Integer, DateTime
from app.database import Base
from datetime import datetime

class Transaccion(Base):
    __tablename__ = "transacciones_agilpagos"

    id_transaccion = Column(String, primary_key=True, index=True)
    tipo = Column(Integer)  # 1=Débito, 2=Crédito, etc.
    numero_cuenta = Column(String)
    importe = Column(Float)
    fecha_operacion = Column(DateTime)
    cvu = Column(String)
    observaciones = Column(String)
    fecha_registro = Column(DateTime, default=datetime.now)
