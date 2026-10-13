# Evidencia: primera petición autenticada

- **Fecha:** 13 de octubre de 2026
- **Herramienta:** Thunder Client (VS Code)
- **Proveedor:** Google Gemini API
- **Método:** POST
- **Endpoint:** https://generativelanguage.googleapis.com/v1beta/interactions
- **Autenticación:** header `x-goog-api-key` (llave cargada desde `.env`, no incluida aquí)

## Petición 1

**Body enviado:**
​```json
{
  "model": "gemini-3.8-flash",
  "input": "Hola, ¿puedes confirmar que esta conexión funciona?"
}
​```

**Código de estado:** 200 OK

**Respuesta del modelo (fragmento):**
text": "¡Hola! Sí, te confirmo que la conexión funciona perfectamente. Te recibo y respondo sin problemas. \n\n¿En qué te puedo ayudar hoy?",



## Peticion 2

input: ¿Qué es una variable de entorno? Responde en una frase.
Primero me indico: error 429 por exceder la cuota de uso. 

## 2do intento Peticion 2

**Código de estado:** 200 OK

respuesta del modelo: t": "Una variable de entorno es un valor dinámico del sistema operativo que almacena información de configuración accesible para los programas y procesos en ejecución.",
