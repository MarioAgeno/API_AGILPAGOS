from sqlalchemy import Column, Integer, String, Numeric, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Transaccion(Base):
    __tablename__ = "transacciones_agilpagos"

    id_transaccion = Column(String, primary_key=True, index=True)
    tipo = Column(Integer)
    numero_cuenta = Column(String)
    importe = Column(Numeric(18, 2))
    fecha_operacion = Column(DateTime)
    cvu = Column(String)
    observaciones = Column(String, nullable=True)
    fecha_registro = Column(DateTime, default=datetime.now)
    payload_raw = Column(Text, nullable=True)