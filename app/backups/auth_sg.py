# auth_sg.py
import os
import base64
import hashlib
import uuid
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

import httpx

# =========
# Config
# =========
SG_BASE_URL      = os.getenv("SG_BASE_URL", "").rstrip("/")  
SG_USER_NAME     = os.getenv("SG_USER_NAME", "") 
SG_PASSWORD      = os.getenv("SG_PASSWORD", "") 
SG_ID_ENTIDAD    = os.getenv("SG_ID_ENTIDAD", "") 
SG_LOGIN_PATH    = os.getenv("SG_LOGIN_PATH", "/Account/Login")

# Tiempo de seguridad para renovar el token antes de su vencimiento (en segundos)
TOKEN_RENEW_LEEWAY = int(os.getenv("SG_TOKEN_RENEW_LEEWAY", "300"))  # 5 minutos

# =========
# Utilidades digest 
# =========
def ahora_utc_iso_z() -> str:
    # Formato "yyyy-MM-ddTHH:mm:ssZ"
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S") + "Z"

def nonce_base64() -> str:
    rnd = uuid.uuid4().bytes  # 16 bytes
    return base64.b64encode(rnd).decode("utf-8")

def password_digest_b64(nonce_b64: str, created_iso_z: str, raw_password: str) -> str:
    """
    digest = Base64( SHA1( nonceBytes + createdBytes + passwordBytes ) )
    OJO: en tu script original formabas created sin la Z en los bytes y luego concatenabas "Z".
    Si tu backend SG fue sensible a eso, replicamos el mismo criterio:
    """
    nonce_bytes   = base64.b64decode(nonce_b64)
    created_bytes = created_iso_z.replace("Z", "").encode("utf-8")
    digest_input  = nonce_bytes + created_bytes + raw_password.encode("utf-8")
    sha1          = hashlib.sha1(digest_input).digest()
    return base64.b64encode(sha1).decode("utf-8")

# =========
# Cache de token en memoria (por Entidad)
# =========
class TokenCacheItem:
    def __init__(self, token: str, expires_at: datetime):
        self.token = token
        self.expires_at = expires_at

class TokenCache:
    def __init__(self):
        self._lock = asyncio.Lock()
        self._items: Dict[str, TokenCacheItem] = {}  # key = id_entidad

    async def get_valid(self, entidad_id: str) -> Optional[str]:
        async with self._lock:
            item = self._items.get(entidad_id)
            if not item:
                return None
            # renovar si está por vencer
            now = datetime.now(timezone.utc)
            if item.expires_at <= now + timedelta(seconds=TOKEN_RENEW_LEEWAY):
                return None
            return item.token

    async def set(self, entidad_id: str, token: str, expires_at: datetime) -> None:
        async with self._lock:
            self._items[entidad_id] = TokenCacheItem(token, expires_at)

token_cache = TokenCache()

# =========
# Login a SG (Account/Login)
# =========
async def _login_sg(entidad_id: str) -> Dict:
    """
    Llama a Account/Login y devuelve el json completo para que el caller lo procese.
    """
    if not (SG_BASE_URL and SG_USER_NAME and SG_PASSWORD and entidad_id):
        raise RuntimeError("Faltan variables de entorno SG_BASE_URL, SG_USER_NAME, SG_PASSWORD o entidad_id")

    created = ahora_utc_iso_z()
    nonce   = nonce_base64()
    pwd_enc = password_digest_b64(nonce, created, SG_PASSWORD)

    payload = {
        "userName":  SG_USER_NAME,
        "password":  pwd_enc,
        "nonce":     nonce,
        "created":   created,
        "idEntidad": entidad_id,
    }

    url = f"{SG_BASE_URL}{SG_LOGIN_PATH}"
    timeout = httpx.Timeout(15.0, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(url, json=payload)
        # Si SG usa status diferentes a 200 para errores de credenciales, con esto te enterás
        resp.raise_for_status()
        return resp.json()

# =========
# Obtener/renovar token
# =========
async def get_or_refresh_token(entidad_id: Optional[str] = None) -> str:
    """
    Devuelve un Bearer token válido para la entidad.
    Usa cache interna; si no hay o está por vencer, reloguea.
    """
    entidad_id = entidad_id or SG_ID_ENTIDAD
    if not entidad_id:
        raise RuntimeError("SG_ID_ENTIDAD no definido y no se pasó entidad_id")

    # 1) cache hit
    cached = await token_cache.get_valid(entidad_id)
    if cached:
        return cached

    # 2) login
    data = await _login_sg(entidad_id)

    # *** OJO ***
    # La respuesta exacta de SG puede variar. Ajustar aquí los nombres
    access_token = (
        data.get("accessToken")
        or data.get("token")
        or data.get("bearerToken")
    )

    # SG UAT devuelve típicamente: token, expiration, refreshToken
    expires_in   = data.get("expiresIn")
    expires_at_s = data.get("expiresAt") or data.get("expiration")

    if not access_token:
        raise RuntimeError(f"Login SG sin token en respuesta: {data}")

    now = datetime.now(timezone.utc)

    def _parse_iso_utc(s: str) -> datetime:
        s = (s or "").strip()
        if not s:
            raise ValueError("fecha vacía")
        if s.endswith("Z"):
            s = s.replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    if expires_at_s:
        try:
            expires_at = _parse_iso_utc(expires_at_s)
        except Exception:
            expires_at = now + timedelta(minutes=50)
    elif isinstance(expires_in, int):
        expires_at = now + timedelta(seconds=max(expires_in, 60))
    else:
        expires_at = now + timedelta(minutes=50)

    await token_cache.set(entidad_id, access_token, expires_at)
    return access_token


# =========
# Helper para headers
# =========
async def auth_headers(entidad_id: Optional[str] = None) -> Dict[str, str]:
    token = await get_or_refresh_token(entidad_id)
    return {"Authorization": f"bearer {token}"}

# === DEBUG / Test de autenticación ===
async def login_debug(entidad_id: Optional[str] = None, force_refresh: bool = True) -> Dict:
    """
    Fuerza login a SG y devuelve un resumen seguro (sin exponer el token completo).
    Útil para smoke test del Account/Login.
    """
    ent = entidad_id or SG_ID_ENTIDAD
    if not ent:
        raise RuntimeError("Falta SG_ID_ENTIDAD o entidad_id")

    # llamamos al login "crudo" para ver la respuesta tal cual
    data = await _login_sg(ent)

    # normalizamos campos comunes sin depender de nombres exactos
    access_token = data.get("accessToken") or data.get("token") or data.get("bearerToken")
    expires_in   = data.get("expiresIn")
    expires_at   = data.get("expiresAt")  # suele venir ISO

    return {
        "ok": bool(access_token),
        "token_prefix": (access_token[:16] + "…") if access_token else None,
        "expires_in": expires_in,
        "expires_at": expires_at,
        "raw_keys": list(data.keys()),   # para ver campos reales devueltos por SG
        "raw_sample": {                  # pequeña muestra sin secretos
            k: (v if k.lower() not in {"token", "accesstoken", "bearertoken"} else "***redacted***")
            for k, v in list(data.items())[:6]
        }
    }

def _iso_z(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# Método de introspección del cache
async def cache_status(entidad_id: Optional[str] = None) -> dict:
    ent = entidad_id or SG_ID_ENTIDAD
    if not ent:
        raise RuntimeError("Falta SG_ID_ENTIDAD o entidad_id")
    async with token_cache._lock:  # uso interno, OK
        item = token_cache._items.get(ent)
        if not item:
            return {"exists": False, "entidad_id": ent}
        now = datetime.now(timezone.utc)
        return {
            "exists": True,
            "entidad_id": ent,
            "expires_at": _iso_z(item.expires_at),
            "seconds_left": int((item.expires_at - now).total_seconds())
        }

# Opcional: mejorar el /sg/auth/test para mostrar "expiration" si existe
async def login_debug(entidad_id: Optional[str] = None, force_refresh: bool = True) -> dict:
    ent = entidad_id or SG_ID_ENTIDAD
    data = await _login_sg(ent)
    access_token = data.get("accessToken") or data.get("token") or data.get("bearerToken")
    return {
        "ok": bool(access_token),
        "token_prefix": (access_token[:16] + "…") if access_token else None,
        "expires_in": data.get("expiresIn"),
        "expires_at": data.get("expiresAt") or data.get("expiration"),  # <<— ahora refleja 'expiration'
        "raw_keys": list(data.keys()),
        "raw_sample": {
            k: ("***redacted***" if k.lower() in {"token","accesstoken","bearertoken"} else data[k])
            for k in list(data.keys())[:6]
        }
    }
