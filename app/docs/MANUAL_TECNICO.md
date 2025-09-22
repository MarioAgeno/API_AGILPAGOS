
---

## 📄 `docs/MANUAL_TECNICO.md`

```markdown
# Manual Técnico – API Agilpagos

Este documento describe en detalle la arquitectura, funcionamiento y buenas prácticas para el mantenimiento y extensión de la API.

---

## 🎯 Objetivo

- Recibir **webhooks** de Agilpagos con créditos y reversas.
- Persistir la información en SQL Server.
- Permitir la consulta de transacciones desde el ERP y Home Mutual.

---

## 🏗️ Arquitectura

- **FastAPI** como framework backend.
- **SQL Server** como base de datos (`AGILPAGOS`).
- **Tabla principal:** `transacciones_agilpagos`.
- **Conexión:** definida vía `.env` con parámetros `DB_DRIVER`, `DB_SERVER`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`.
- **ORM:** SQLAlchemy (en `models.py`).
- **Validación:** Pydantic (en `schemas.py`).

---

## 📂 Archivos principales

| Archivo              | Descripción |
|----------------------|-------------|
| `main.py`            | Entrypoint con definición de endpoints |
| `models.py`          | Modelo ORM de `transacciones_agilpagos` |
| `schemas.py`         | Modelos Pydantic para requests/responses |
| `.env`               | Configuración de conexión a BD |
| `requirements.txt`   | Dependencias de Python |

> Nota: `models_actualizado.py` y `main_actualizado.py` son versiones previas.  
> No se utilizan y pueden eliminarse.

---

## 🗄️ Estructura de la tabla `transacciones_agilpagos`

| Campo           | Tipo       | Descripción |
|-----------------|------------|-------------|
| id              | int (PK)   | Identificador autoincremental |
| idTransaccion   | GUID       | ID de la transacción en Agilpagos |
| cvu             | string     | CVU destino |
| cbuCredito      | string     | CBU o CVU destino |
| cuitCredito     | string     | CUIT del destinatario |
| importe         | float      | Monto de la operación |
| descripcion     | string     | Texto descriptivo |
| estado          | string     | Estado de la transacción |
| fechaOperacion  | datetime   | Fecha de la operación |
| fechaContable   | datetime   | Fecha contable |
| idCoelsa        | string     | Identificador interbancario |

---

## 🔌 Endpoints

### 1. `GET /`
- Verifica el estado del servicio.

### 2. `POST /transacciones`
- Recibe notificaciones de créditos y reversas desde Agilpagos.
- Valida con Pydantic.
- Inserta en `transacciones_agilpagos`.
- Devuelve **200 OK**.

### 3. `GET /transacciones/{idTransaccion}`
- Devuelve datos de una transacción registrada.

---

## 🔒 Seguridad

- **Estado actual:** Endpoints abiertos para pruebas en UAT.  
- **Pendiente de implementar:**
  - Autenticación Bearer JWT.
  - Validación de cabeceras (`X-Signature`, `IDWEBUSUARIOFINAL`) según especificaciones de Agilpagos.

---

## 📝 Buenas prácticas

- Confirmar SIEMPRE con **200 OK** a Agilpagos, incluso si la transacción ya fue registrada.
- Registrar en logs todos los requests entrantes.
- Retener saldo hasta que la transacción tenga estado final.
- Implementar workers de conciliación para validar estados de operaciones no confirmadas.

---

## 🚀 Próximos pasos

- Implementar autenticación JWT.
- Integrar validación de cabeceras.
- Agregar logging estructurado (JSON con traceId).
- Crear worker de conciliación automática.
- Integrar con la API principal de Home Mutual.

---
