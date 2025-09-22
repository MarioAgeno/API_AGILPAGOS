# API Agilpagos – Integración Home Mutual

Microservicio en **FastAPI** que actúa como puente entre:

- El sistema de gestión de la Mutual (ERP/Home Mutual).
- La plataforma **Agilpagos / Coinag**.

Se encarga de:

- Registrar en SQL Server las notificaciones de **créditos y reversas** enviadas por Agilpagos.  
- Permitir la **consulta y validación de esas transacciones** por parte de la Mutual.

---

## ⚙️ Arquitectura General

- **Framework:** FastAPI  
- **Base de datos:** SQL Server (`AGILPAGOS`)  
- **Driver:** ODBC (`SQL Server Native Client 11.0`)  
- **Configuración sensible:** archivo `.env` (driver, servidor, usuario, contraseña, base)  
- **Tabla principal:** `transacciones_agilpagos`  
- **Autenticación:** por ahora sin token Bearer (para pruebas). Se planea agregar.  

---

## 📂 Estructura de Archivos

- `main.py`: Punto de entrada del API. Define los endpoints.  
- `models.py`: Clase ORM de `transacciones_agilpagos`.  
- `schemas.py`: Modelos Pydantic (validación de request/response).  
- `.env`: Configuración de conexión a SQL Server.  
- `requirements.txt`: Dependencias (FastAPI, pyodbc, pydantic, python-dotenv).  

---

## 🗄️ Tabla `transacciones_agilpagos`

Campos principales:

| Campo           | Tipo        | Descripción                                   |
|-----------------|-------------|-----------------------------------------------|
| id              | int (PK)    | Autoincremental                               |
| idTransaccion   | GUID        | Identificador en Agilpagos                    |
| cvu             | string      | CVU destino                                   |
| cbuCredito      | string      | CBU o CVU destino                             |
| cuitCredito     | string      | CUIT del destinatario                         |
| importe         | float       | Monto de la operación                         |
| descripcion     | string      | Texto descriptivo                             |
| estado          | string      | Estado de la transacción                      |
| fechaOperacion  | datetime    | Fecha de ejecución                            |
| fechaContable   | datetime    | Fecha contable                                |
| idCoelsa        | string      | Identificador interbancario                   |

---

## 🔌 Endpoints Implementados

### 1. Webhook de notificación  
`POST /transacciones`

Consumido por **Agilpagos** para notificar:

- Créditos (carga de saldo a CVU)  
- Reversas (de débitos/créditos)  

**Lógica:**
1. Valida el request contra el esquema Pydantic.  
2. Inserta el registro en `transacciones_agilpagos`.  
3. Devuelve **200 OK** (requisito de Agilpagos).  

---

### 2. Consulta de transacciones (interna)  
`GET /transacciones/{idTransaccion}`

- Uso interno por la Mutual/Home.  
- Devuelve detalles de una transacción registrada.  

---

### 3. Health Check  
`GET /`

- Devuelve `"API Agilpagos funcionando"`.  
- Para verificar conectividad y disponibilidad del servicio.  

---

## 🔄 Flujo de Uso

1. La Mutual da de alta un socio en Home Mutual.  
2. El alta genera también una CVU en Agilpagos (Onboarding).  
3. Cuando un socio recibe una transferencia o reversa, **Agilpagos llama a `POST /transacciones`**.  
4. El microservicio guarda la operación en `transacciones_agilpagos`.  
5. El ERP/Home consulta las transacciones vía `GET /transacciones/{id}`.  

---

## 🔒 Seguridad (pendiente de implementar)

- Actualmente los endpoints están **abiertos** (modo desarrollo).  
- Próximamente se agregará:
  - Autenticación **Bearer JWT**.  
  - Validación de **headers de seguridad** (`X-Signature`, `IDWEBUSUARIOFINAL`, etc.) según especificación de Agilpagos.  

---

## ✅ Buenas prácticas aplicadas

- Separación clara entre modelos (ORM) y esquemas (Pydantic).  
- Uso de `.env` para configuración sensible.  
- Confirmación a Agilpagos siempre con **200 OK**.  
- Manejo básico de errores con `HTTPException`.  

---

## 🚀 Próximos pasos recomendados

1. Implementar autenticación con Bearer Token.  
2. Agregar logs de auditoría para trazabilidad.  
3. Crear workers automáticos para conciliación y validación de estados.  
4. Evaluar unificación con la API principal de Home Mutual (o mantener como microservicio separado).  

---
