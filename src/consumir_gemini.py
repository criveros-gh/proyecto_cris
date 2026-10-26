import os
import requests
import json
import re
from dotenv import load_dotenv

load_dotenv()

MODELO = "gemini-3.1-flash-lite"  # elegido en docs/decision-arquitectura.md (Bloque 9)

# Prompt de sistema por defecto: se usa cuando quien llama no entrega uno propio.
SYSTEM_INSTRUCTION_POR_DEFECTO = (
    "Eres un asistente experto en gatos callejeros. Responde en español, "
    "de forma breve y en una sola frase."
)

# El error de las responsabilidades de esta función de armar petición, es que el usuario no haya indicado ninguna pregunta.
def armar_peticion(pregunta_usuario, system_instruction=SYSTEM_INSTRUCTION_POR_DEFECTO, response_schema=None):
    if not pregunta_usuario:
        raise ValueError("La pregunta no puede estar vacía.")
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "tu_llave_aqui":
        raise RuntimeError("Falta GEMINI_API_KEY: copia .env.example como .env y pon ahí tu llave real.")
    modelo = MODELO
    modelo = "gemini-3.1-flash-lite"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={api_key}"
    body = {
        "systemInstruction": {
            "parts": [{"text": system_instruction}]
        },
        "contents": [
            {"parts": [{"text": pregunta_usuario}]}
        ]
    }
    if response_schema is not None:
        body["generationConfig"] = {
            "responseMimeType": "application/json",
            "responseSchema": response_schema
        }
    return url, body

#Hacer esto significa: intenta esto, pero si falla esta forma específica, haz esto
def enviar_peticion(url, body):
    try:
        respuesta = requests.post(url, json=body, timeout=60)
    except requests.exceptions.Timeout:
        raise RuntimeError("El servicio tardó demasiado en responder (más de 60 segundos).")
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Error de conexión. Por favor, verifica tu conexión a internet.")
    try:
        return respuesta.json()
    except requests.exceptions.JSONDecodeError:
        raise RuntimeError("La respuesta del servicio no llegó en el formato esperado (JSON)")


def extraer_texto(datos):
    # Si Gemini respondió con un error (401, 429, 503...), lo mostramos tal cual.
    if "error" in datos:
        raise RuntimeError(f"Gemini respondió con error: {datos['error'].get('message', datos['error'])}")
    try:
        return datos["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        raise RuntimeError("La respuesta no trae el texto generado en el lugar esperado. Revisa tu API key en el archivo .env.")


def parsear_respuesta_json(texto, claves_esperadas=("nombre", "poder")):
    texto_limpio = texto.strip()
    texto_limpio = re.sub(r"^```(?:json)?\s*", "", texto_limpio)
    texto_limpio = re.sub(r"\s*```$", "", texto_limpio)
    try:
        datos = json.loads(texto_limpio)
    except json.JSONDecodeError:
        raise ValueError("La respuesta del modelo no es JSON válido.")
    if not all(clave in datos for clave in claves_esperadas):
        raise ValueError("La respuesta no tiene la estructura esperada.")
    return datos


# Precios en dólares POR TOKEN de gemini-3.1-flash-lite (0,25 y 1,50 USD por millón),
# los mismos de docs/decision-arquitectura.md. Fuente: https://ai.google.dev/gemini-api/docs/pricing
PRECIO_ENTRADA = 0.00000025
PRECIO_SALIDA = 0.00000150

# Función hermana de extraer_texto: lee la misma respuesta cruda (datos),
# pero en vez del texto busca usageMetadata para calcular el costo de la petición.
def calcular_costo(datos, precio_entrada, precio_salida):
    try:
        uso = datos["usageMetadata"]
        tokens_entrada = uso["promptTokenCount"]
        tokens_salida = uso["candidatesTokenCount"]
    except KeyError:
        raise RuntimeError("La respuesta no trae usageMetadata: la petición falló o llegó incompleta.")
    return (tokens_entrada * precio_entrada) + (tokens_salida * precio_salida)


def obtener_dato_de_prueba(pregunta):
    url, body = armar_peticion(pregunta)
    datos = enviar_peticion(url, body)
    texto = extraer_texto(datos)
    costo = calcular_costo(datos, PRECIO_ENTRADA, PRECIO_SALIDA)
    return texto, costo


SYSTEM_INSTRUCTION_CARTA = (
    "Eres un creador de cartas de colección de gatos callejeros. "
    "Responde únicamente con un objeto JSON válido, sin texto adicional "
    "y sin usar bloques de markdown. El JSON debe tener exactamente estas "
    "claves: 'nombre' (string) y 'poder' (string)."
)

SCHEMA_CARTA = {
    "type": "OBJECT",
    "properties": {
        "nombre": {"type": "STRING"},
        "poder": {"type": "STRING"}
    },
    "required": ["nombre", "poder"]
}


# Flujo completo de la miniaplicación: descripción del gato -> carta (nombre y poder) + costo.
def crear_carta(descripcion_gato):
    url, body = armar_peticion(descripcion_gato, SYSTEM_INSTRUCTION_CARTA, SCHEMA_CARTA)
    respuesta_json = enviar_peticion(url, body)
    texto = extraer_texto(respuesta_json)
    carta = parsear_respuesta_json(texto)
    costo = calcular_costo(respuesta_json, PRECIO_ENTRADA, PRECIO_SALIDA)
    return carta, costo


if __name__ == "__main__":
    carta, costo = crear_carta("Un gato negro de ojos amarillos que vive en una plaza.")
    print(carta)
    print(f"Costo de la petición: {costo:.8f} USD")