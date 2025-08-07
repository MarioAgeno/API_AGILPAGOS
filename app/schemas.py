from pydantic import BaseModel, Field
from typing import Optional, List

class Impuesto(BaseModel):
    idTransaccion: str
    importe: float
    idTipoTransaccion: int
    tipoImporte: str
    idTipoImporte: str

class Contraparte(BaseModel):
    cuentaContraparte: str
    cuitContraparte: int
    titularContraparte: str

class TransaccionNotificada(BaseModel):
    idTransaccion: str
    idTransaccionAnulada: Optional[str]
    idTipoTransaccion: int
    numeroCuenta: str
    importe: float
    idMoneda: int
    fechaOperacion: str
    fechaContable: str
    observaciones: Optional[str]
    CVU: str
    idTransaccionOriginante: Optional[str]
    idTransaccionEntidad: str
    idEntidad: str
    idWebOperacion: str
    cuentaBloqueada: Optional[bool]
    total: float
    idCoelsa: Optional[str]
    transaccionCuentaContraparte: Contraparte
    impuestos: List[Impuesto]
