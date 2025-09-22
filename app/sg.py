# sg.py
import os
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Body, Query
from app.auth_sg import auth_headers, SG_BASE_URL, login_debug, cache_status, get_or_refresh_token
from pydantic import BaseModel, EmailStr, constr
import os, httpx


router = APIRouter()

# Endpoints reales de SG (ajustar según tu PDF 1.8.6/ambiente)
SG_ENDPOINT_CVU         = os.getenv("SG_ENDPOINT_CVU", "/api/cuentas-pago/cvu")           # EJEMPLO de path
SG_ENDPOINT_TRANSFER    = os.getenv("SG_ENDPOINT_TRANSFER", "/api/transferencias")        # EJEMPLO de path
SG_TIMEOUT_SECS         = float(os.getenv("SG_HTTP_TIMEOUT", "20.0"))

SG_BASE_URL = os.getenv("SG_BASE_URL", "").rstrip("/")

def _full_url(path: str) -> str:
    base = SG_BASE_URL.rstrip("/")
    return f"{base}{path}"

async def _post_to_sg(path: str, payload: Dict[str, Any], entidad_id: Optional[str] = None) -> Dict:
    """
    Plantilla genérica para POST → SG con token automático.
    """
    if not SG_BASE_URL:
        raise HTTPException(500, detail="Falta SG_BASE_URL en .env")

    headers = await auth_headers(entidad_id)
    url     = _full_url(path)
    timeout = httpx.Timeout(SG_TIMEOUT_SECS, connect=min(10.0, SG_TIMEOUT_SECS))
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(url, json=payload, headers=headers)
        # Dejar pasar 4xx/5xx a un mensaje claro para el front
        if resp.status_code >= 400:
            # Propaga texto/JSON de SG para diagnosticar
            try:
                raise HTTPException(resp.status_code, detail=resp.json())
            except Exception:
                raise HTTPException(resp.status_code, detail=resp.text)
        try:
            return resp.json()
        except Exception:
            return {"ok": True, "raw": resp.text}

async def _usuario_by_cuit_core(cuit: str, entidad_id: Optional[str] = None) -> Dict[str, Any]:
    SG_BASE_URL = os.getenv("SG_BASE_URL", "").rstrip("/")
    if not SG_BASE_URL:
        raise HTTPException(500, "Falta SG_BASE_URL")

    token = await get_or_refresh_token(entidad_id)
    url = f"{SG_BASE_URL}/Usuarios/{cuit}/UsuarioByCuit"
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(timeout=30) as cli:
        r = await cli.get(url, headers=headers)

    if r.status_code == 404:
        return {"existe": False, "idUsuario": None, "cuentas": [], "rawCount": 0}
    if r.status_code >= 400:
        try:
            detail = r.json()
        except Exception:
            detail = r.text
        raise HTTPException(status_code=r.status_code, detail=detail)

    try:
        data = r.json()
    except Exception:
        raise HTTPException(status_code=502, detail="Respuesta no JSON desde SG")

    items = data if isinstance(data, list) else [data]
    first = next((it for it in items if isinstance(it, dict)), None)

    id_usuario, cuentas = None, []
    if first:
        usuario_list = first.get("usuario") or []
        if isinstance(usuario_list, list) and usuario_list:
            id_usuario = usuario_list[0]
        cuentas = first.get("cuentas") or []

    return {"existe": bool(id_usuario or cuentas), "idUsuario": id_usuario, "cuentas": cuentas, "rawCount": len(items)}


# =========================================================
# 1) CVU - Ejemplo: crear u obtener CVU para un socio/cuenta
# =========================================================
@router.post("/cvu")
async def crear_o_obtener_cvu(
    payload: Dict[str, Any] = Body(..., description="Datos requeridos por SG para CVU (cuit/cuil, titular, etc.)"),
    entidad_id: Optional[str] = Query(None, description="GUID entidad si difiere del por defecto"),
):
    """
    Proxy seguro hacia SG para crear/obtener CVU.
    - Django llama a este endpoint con los datos del socio.
    - Este servicio adjunta el Bearer válido y reenvía a SG.
    """
    # TODO: si necesitás validar negocio local (existencia de socio, etc.), hazlo aquí
    data = await _post_to_sg(SG_ENDPOINT_CVU, payload, entidad_id=entidad_id)
    return data

# =========================================================
# 2) Transferencias - Ejemplo: iniciar transferencia
# =========================================================
@router.post("/transferencias")
async def iniciar_transferencia(
    payload: Dict[str, Any] = Body(..., description="Datos de transferencia: origen, destino (CVU/Alias), importe, concepto"),
    entidad_id: Optional[str] = Query(None, description="GUID entidad si difiere del por defecto"),
):
    """
    Proxy seguro para crear una transferencia en SG.
    """
    # TODO: validaciones locales (límites, KYC, fraude, etc.) antes de enviar a SG
    data = await _post_to_sg(SG_ENDPOINT_TRANSFER, payload, entidad_id=entidad_id)
    return data

# ===================================================
# 3) Debug - Forzar login y ver estado del token
# ===================================================
@router.get("/auth/test")
async def auth_test(entidad_id: Optional[str] = Query(None, description="GUID entidad opcional")):
    """
    Fuerza Account/Login en SG y devuelve un resumen seguro con el estado del token.
    """
    try:
        result = await login_debug(entidad_id=entidad_id, force_refresh=True)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.get("/auth/ensure")
async def auth_ensure(entidad_id: Optional[str] = Query(None, description="GUID entidad opcional")):
    """
    Fuerza obtención/renovación de token vía get_or_refresh_token y devuelve el estado del cache.
    """
    try:
        await get_or_refresh_token(entidad_id)
        return await cache_status(entidad_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"auth_ensure: {e}")

@router.get("/auth/cache")
async def auth_cache(entidad_id: Optional[str] = Query(None, description="GUID entidad opcional")):
    return await cache_status(entidad_id)


SG_BASE_URL = os.getenv("SG_BASE_URL", "").rstrip("/")
SG_ID_DOC_DNI = os.getenv("SG_ID_DOC_DNI")  # <- completar en .env
SG_ID_TIPO_PERSONA = os.getenv("SG_ID_TIPO_PERSONA", "20EB9127-7CA8-49E0-9E0B-CA8293218ACA")
SG_ID_TIPO_CUENTA = os.getenv("SG_ID_TIPO_CUENTA", "D2483A34-78BE-40A2-B8CB-07AD4BCF6F61")


class AltaUsuarioIn(BaseModel):
    nombre: constr(min_length=1, max_length=40)
    apellido: constr(min_length=1, max_length=40)
    razonSocial: Optional[str] = None
    sexo: constr(min_length=1, max_length=1) 
    idEntidadTipoDocumento: Optional[str] = None 
    numeroDocumento: constr(min_length=1, max_length=20)
    fechaNacimiento: constr(min_length=8, max_length=30) 
    cuit: int | constr(min_length=8, max_length=20) 
    email: EmailStr
    caracteristicaPaisTelefono: constr(min_length=1, max_length=3) = "54"
    codigoAreaTelefono: constr(min_length=1, max_length=6)
    numeroTelefono: constr(min_length=1, max_length=20)
    idTipoPersona: Optional[str] = None 
    numeroCuentaEntidad: constr(min_length=1, max_length=50)
    idTipoCuenta: Optional[str] = None 

class AltaUsuarioOut(BaseModel):
    idUsuario: str
    cvu: Optional[str] = None
    alias: Optional[str] = None
    yaExistia: bool = False


# ---------------------------
# 1) Usuarios por CUIT (RAW)
# ---------------------------
@router.get("/usuarios/{cuit}/by-cuit")
async def usuario_by_cuit(cuit: str, entidad_id: Optional[str] = Query(None, description="GUID entidad opcional")):
    return await _usuario_by_cuit_core(cuit, entidad_id)

@router.get("/usuarios/{cuit}/raw")
async def usuario_raw(cuit: str, entidad_id: Optional[str] = Query(None, description="GUID entidad opcional")):
    from os import getenv
    SG_BASE_URL = getenv("SG_BASE_URL", "").rstrip("/")
    token = await get_or_refresh_token(entidad_id)
    url = f"{SG_BASE_URL}/Usuarios/{cuit}/UsuarioByCuit"
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(timeout=30) as cli:
        r = await cli.get(url, headers=headers)
    try:
        body = r.json()
    except Exception:
        body = r.text
    return {"status_code": r.status_code, "content_type": r.headers.get("content-type", ""), "body": body}


@router.post("/usuarios", response_model=AltaUsuarioOut)
async def crear_usuario(req: AltaUsuarioIn):
    # 0) sanity SG
    if not SG_BASE_URL:
        raise HTTPException(500, "Falta SG_BASE_URL")
    if not (req.idEntidadTipoDocumento or SG_ID_DOC_DNI):
        raise HTTPException(500, "Falta idEntidadTipoDocumento (en body o en SG_ID_DOC_DNI)")
    # 1) evitar duplicados por CUIT
    existe = await _usuario_by_cuit_core(str(req.cuit))
    if existe.get("existe") and existe.get("idUsuario"):
        return AltaUsuarioOut(idUsuario=existe["idUsuario"], yaExistia=True)

    token = await get_or_refresh_token()
    url = f"{SG_BASE_URL}/Usuarios"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # Normalizaciones
    def _to_int_cuit(v: Any) -> int:
        s = str(v).replace("-", "").strip()
        if not s.isdigit():
            raise HTTPException(400, f"cuit inválido: {v}")
        return int(s)

    payload = {
        "nombre": req.nombre,
        "apellido": req.apellido,
        "razonSocial": req.razonSocial,  # puede ser null
        "sexo": req.sexo,
        "idEntidadTipoDocumento": req.idEntidadTipoDocumento or SG_ID_DOC_DNI,
        "numeroDocumento": req.numeroDocumento,
        "fechaNacimiento": req.fechaNacimiento,   # ISO, SG acepta con hora (como tu ejemplo)
        "cuit": _to_int_cuit(req.cuit),
        "email": req.email,
        "caracteristicaPaisTelefono": req.caracteristicaPaisTelefono,
        "codigoAreaTelefono": req.codigoAreaTelefono,
        "numeroTelefono": req.numeroTelefono,
        "idTipoPersona": req.idTipoPersona or SG_ID_TIPO_PERSONA,
        "numeroCuentaEntidad": req.numeroCuentaEntidad,
        "idTipoCuenta": req.idTipoCuenta or SG_ID_TIPO_CUENTA,
    }

    async with httpx.AsyncClient(timeout=30) as cli:
        r = await cli.post(url, headers=headers, json=payload)

    if r.status_code >= 400:
        try:
            detail = r.json()
        except Exception:
            detail = r.text
        raise HTTPException(status_code=r.status_code, detail=detail)

    data = r.json()  # {"idUsuario": "...", "alias": "...", "cvu": "..."}
    return AltaUsuarioOut(**data, yaExistia=False)
