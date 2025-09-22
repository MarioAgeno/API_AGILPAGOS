# API Reference – Agilpagos Integration

Referencia rápida de los endpoints expuestos por la API.

---

## Healthcheck

`GET /`

- **Descripción:** Verifica disponibilidad del servicio.
- **Response (200):**
```json
{ "message": "API Agilpagos funcionando" }


## Webhook de transacciones

POST /transacciones

Descripción: Endpoint que recibe notificaciones de Agilpagos por créditos y reversas.

Request (ejemplo):

{
  "idTransaccion": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "cvu": "0000000000111222334454",
  "cbuCredito": "2850590940090418135201",
  "cuitCredito": "20123456789",
  "importe": 1500.50,
  "descripcion": "Transferencia recibida",
  "estado": "Procesado",
  "fechaOperacion": "2025-09-20T12:30:00",
  "fechaContable": "2025-09-20T12:30:00",
  "idCoelsa": "123456"
}

Response (200):

{ "message": "Transacción registrada correctamente" }

## Consulta de transacciones

GET /transacciones/{idTransaccion}

Descripción: Devuelve los detalles de una transacción almacenada en la BD.

Response (ejemplo):

{
  "id": 1,
  "idTransaccion": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "cvu": "0000000000111222334454",
  "cbuCredito": "2850590940090418135201",
  "cuitCredito": "20123456789",
  "importe": 1500.50,
  "descripcion": "Transferencia recibida",
  "estado": "Procesado",
  "fechaOperacion": "2025-09-20T12:30:00",
  "fechaContable": "2025-09-20T12:30:00",
  "idCoelsa": "123456"
}

Status codes comunes
| Código | Significado                                   |
| ------ | --------------------------------------------- |
| 200    | OK – Operación realizada correctamente        |
| 400    | Request inválido (datos faltantes o erróneos) |
| 404    | Transacción no encontrada                     |
| 500    | Error interno del servidor                    |
