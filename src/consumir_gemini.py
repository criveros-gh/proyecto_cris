import os
import requests
from dotenv import load_dotenv

load_dotenv()

# El error de las responsabilidades de esta función de armar petición, es que el usuario no haya indicado ninguna pregunta.
def armar_peticion(pregunta):
    if not pregunta:
        raise ValueError("La pregunta no puede estar vacía.")
    api_key = os.getenv("GEMINI_API_KEY")
    modelo = "gemini-3.1-flash-lite"
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
    pregunta = "Confirma en una frase corta que esta conexión funciona."
    try:
        resultado, costo = obtener_dato_de_prueba(pregunta)
        print(resultado)
        print(f"Costo de esta petición: US$ {costo:.6f}")
    except (ValueError, RuntimeError) as error:
        print("No se pudo completar la operación:", error)