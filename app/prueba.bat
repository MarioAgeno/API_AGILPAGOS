 $body = @{
     "nombre": "Marcela",
     "apellido": "ROJAS",
     "razonSocial": null,
     "sexo": "F",
     "idEntidadTipoDocumento": "CAE2882B-493C-4E1A-A6E7-B5E2BD25F808",
     "numeroDocumento": "24567401",
     "fechaNacimiento": "1975-05-30T19:36:05.735Z",
     "cuit": 27245674010,
     "email": "marioageno@gmaol.com",
     "caracteristicaPaisTelefono": "54",
     "codigoAreaTelefono": "3498",
     "numeroTelefono": "620582",
     "idTipoPersona": "20EB9127-7CA8-49E0-9E0B-CA8293218ACA",
     "numeroCuentaEntidad": "1001234",
     "idTipoCuenta": "D2483A34-78BE-40A2-B8CB-07AD4BCF6F61"
} | ConvertTo-Json -Depth 5

Invoke-RestMethod `
  -Method POST `
  -Uri "http://186.189.231.237:6868/sg/usuarios" `
  -ContentType "application/json" `
  -Body $body
