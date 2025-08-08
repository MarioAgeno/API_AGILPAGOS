# API de Notificaciones de Créditos y Reversas - Agilpagos

Este microservicio en **FastAPI** permite recibir y procesar notificaciones automáticas de **créditos y reversas** realizadas por la red Agilpagos / COINAG sobre cuentas de pago (CVU) de socios.

## 🚀 Funcionalidad

El sistema expone un endpoint `POST /transacciones` que recibe notificaciones en formato JSON según el esquema definido por Agilpagos. Cada transacción es validada y registrada en una base de datos **SQL Server** para su posterior conciliación y auditoría.

## 📌 Características

- Desarrollo en Python 3.x + FastAPI
- Conexión a base de datos **SQL Server** mediante SQLAlchemy + pyODBC
- Validación estricta del esquema de datos con Pydantic
- Registro automático de créditos y reversas
- Soporte para múltiples tipos de transacciones y operaciones bancarias

## 📂 Estructura del Proyecto

api_creditos_agilpagos/
├── app/
│   ├── main.py              # Punto de entrada de la API
│   ├── schemas.py           # Esquemas de validación (Pydantic)
│   ├── models.py            # Modelo de datos SQLAlchemy
│   ├── database.py          # Configuración de conexión a SQL Server
├── .env                     # Variables de entorno (no versionado)
├── requirements.txt         # Dependencias del proyecto
└── README.md


## 🔐 Seguridad

Este microservicio está pensado para ser expuesto por una URL pública y debe protegerse con validación de IPs o autenticación por token (no incluida en esta versión inicial).

## 📬 Ejemplo de uso

### Request `POST /transacciones`

```json
{
  "idTransaccion": "abc123",
  "idTipoTransaccion": 2,
  "numeroCuenta": "110",
  "importe": 1000.0,
  ...
}

{
  "status": "ok"
}
```

## 🧪 Testing

Levantar con:
```
uvicorn app.main:app --reload
```

Probar con Swagger en: [http://localhost:8000/docs](http://localhost:8000/docs)

## 📄 Documentación técnica OpenAPI

Podés encontrar el archivo OpenAPI con el esquema completo del servicio en:
[openapi_agilpagos.yaml](./openapi_agilpagos.yaml)

## 🧑‍💻 Desarrollado por

**MAASoft** — Soluciones Financieras para Entidades Mutualistas