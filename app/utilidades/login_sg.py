# archivo: crear_login.py
'''
Crea un payload JSON para el endpoint de login de SG.
El payload incluye userName, password (codificado), nonce, created e idEntidad.
El password se codifica usando SHA1 y Base64, siguiendo el esquema WS-Security.
El nonce es un valor aleatorio en Base64 y created es la fecha actual en UTC en formato ISO 8601.
El payload se imprime en consola y se guarda en 'login_payload.json' para usar en Swagger.
'''
import os, base64, hashlib, uuid, json
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv() 

# === Config (usa .env o setea directo) ===
ID_ENTIDAD = os.getenv("SG_ID_ENTIDAD")
USER_NAME  = os.getenv("SG_USER_NAME")
PASSWORD   = os.getenv("SG_PASSWORD")

def ahora_utc_iso_z():
    # Formato ISO sin timezone + 'Z' (como en el ejemplo .NET "s" + Z)
    # e.g. 2025-09-08T18:20:02Z (o con milisegundos si preferís)
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S") + "Z"

def nonce_base64():
    # 16 bytes aleatorios -> Base64 (URL-safe quitando "=" opcional)
    rnd = uuid.uuid4().bytes  # 16 bytes
    b64 = base64.b64encode(rnd).decode("utf-8")
    return b64

def password_digest_b64(nonce_b64: str, created_iso_z: str, raw_password: str) -> str:
    # Emula el ejemplo .NET:
    # digest = Base64( SHA1( nonceBytes + createdBytes + passwordBytes ) )
    nonce_bytes   = base64.b64decode(nonce_b64)
    created_bytes = created_iso_z.replace("Z","")  .encode("utf-8")  # el ejemplo usa ToString("s") y después concatena "Z"
    # Si preferís incluir la "Z" en los bytes, usá created_iso_z.encode("utf-8")
    # pero el ejemplo muestra created = fecha + "Z" al final (concatenación textual).
    digest_input  = nonce_bytes + created_bytes + raw_password.encode("utf-8")
    sha1 = hashlib.sha1(digest_input).digest()
    return base64.b64encode(sha1).decode("utf-8")

if __name__ == "__main__":
    created = ahora_utc_iso_z()
    nonce   = nonce_base64()
    password_enc = password_digest_b64(nonce, created, PASSWORD)

    payload = {
        "userName":  USER_NAME,
        "password":  password_enc,   # << encriptado como pide la doc
        "nonce":     nonce,
        "created":   created,
        "idEntidad": ID_ENTIDAD
    }

    # Mostrar con comillas dobles
    print(json.dumps(payload, indent=2, ensure_ascii=False))

    # Guardar archivo para pegar en Swagger
    with open("login_payload.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print("\n✅ Archivo 'login_payload.json' generado correctamente.")
