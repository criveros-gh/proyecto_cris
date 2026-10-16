import os
import requests
from dotenv import load_dotenv

load_dotenv()

# El error de las responsabilidades de esta función de armar petición, es que el usuario no haya indicado ninguna pregunta.
def armar_peticion(pregunta):
    if not pregunta:
        raise ValueError("La pregunta no puede estar vacía.")
    api_key = os.getenv("GEMINI_API_KEY")
    modelo = "gemini-3.8-flash"
    url =  f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={api_key}"
    body = {"contents": [{"parts": [{"text": pregunta}]}]}
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


def obtener_dato_de_prueba(pregunta):
    url, body = armar_peticion(pregunta)
    datos = enviar_peticion(url, body)
    return extraer_texto(datos)


pregunta = "Confirma en una frase corta que esta conexión funciona."
try:
    resultado = obtener_dato_de_prueba(pregunta)
    print(resultado)
except (ValueError, RuntimeError) as error:
    print("No se pudo completar la operación:", error)