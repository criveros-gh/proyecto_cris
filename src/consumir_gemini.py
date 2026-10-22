import os
import requests
import json
import re
from dotenv import load_dotenv

load_dotenv()

# El error de las responsabilidades de esta función de armar petición, es que el usuario no haya indicado ninguna pregunta.
def armar_peticion(pregunta_usuario, system_instruction, response_schema=None):
    if not pregunta_usuario:
        raise ValueError("La pregunta no puede estar vacía.")
    api_key = os.getenv("GEMINI_API_KEY")
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
        respuesta = requests.post(url, json=body)
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Error de conexión. Por favor, verifica tu conexión a internet.")
    try:
        return respuesta.json()
    except requests.exceptions.JSONDecodeError:
        raise RuntimeError("La respuesta del servicio no llegó en el formato esperado (JSON)")
    return respuesta.json()


def extraer_texto(datos):
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


# Precios en dólares POR TOKEN. Son valores de ejemplo de la lección (inventados):
# los reales se confirman en la página de precios vigente de Gemini.
PRECIO_ENTRADA = 0.00000010
PRECIO_SALIDA = 0.00000040

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


if __name__ == "__main__":
    system_instruction = (
        "Eres un creador de cartas de colección de gatos callejeros. "
        "Responde únicamente con un objeto JSON válido, sin texto adicional "
        "y sin usar bloques de markdown. El JSON debe tener exactamente estas "
        "claves: 'nombre' (string) y 'poder' (string)."
    )
    response_schema = {
        "type": "OBJECT",
        "properties": {
            "nombre": {"type": "STRING"},
            "poder": {"type": "STRING"}
        },
        "required": ["nombre", "poder"]
    }
    pregunta_usuario = "Un gato negro de ojos amarillos que vive en una plaza."
    url, body = armar_peticion(pregunta_usuario, system_instruction, response_schema)
    respuesta_json = enviar_peticion(url, body)
    texto = extraer_texto(respuesta_json)
    datos = parsear_respuesta_json(texto)
    print(datos)
    print(type(datos))