import os
import secrets

# Ruta al archivo .env
ENV_PATH = ".env"

# Generar un token aleatorio de 32 caracteres (letras + números)
nuevo_token = secrets.token_urlsafe(24)  # ~32 caracteres legibles

# Leer y reemplazar el token en el .env
if os.path.exists(ENV_PATH):
    with open(ENV_PATH, "r") as file:
        lines = file.readlines()

    with open(ENV_PATH, "w") as file:
        for line in lines:
            if line.startswith("AUTH_TOKEN="):
                file.write(f"AUTH_TOKEN={nuevo_token}\n")
            else:
                file.write(line)

    print(f"✅ Token actualizado en {ENV_PATH}")
    print(f"🔐 Nuevo token: {nuevo_token}")
else:
    print("❌ No se encontró el archivo .env")
