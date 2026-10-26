import time
from consumir_gemini import armar_peticion, enviar_peticion, extraer_texto, calcular_costo

# ---------------------------------------------------------------
# Bloque 9 · Cómo elegir entre dos modelos candidatos, con criterio
# Código de la lección: repetir la prueba, guardar cada resultado
# y promediar al final.
# ---------------------------------------------------------------

# Paso 1: el precio real de la página de precios del proveedor
# (https://ai.google.dev/gemini-api/docs/pricing), POR TOKEN.
# Cambia estos dos valores según el modelo que estés probando.
PRECIO_ENTRADA = 0.00000075  # gemini-3.8-flash: 0.75 USD por millón gemini-3.1-flash-lite: 0.25 USD por millón
PRECIO_SALIDA = 0.00000375   # gemini-3.8-flash: 3.75 USD por millón gemini-3.1-flash-lite: 1.50 USD por millón

# Paso 2: la latencia, con la MISMA pregunta de prueba en las 4 repeticiones
pregunta = "Describe en una frase a un gato callejero naranjo atigrado con una mancha blanca en el pecho."

latencias = []
respuesta_valida = None
for i in range(4):
    time.sleep(20)  # esperar entre intentos para no chocar con el límite de uso (error 429)
    url, body = armar_peticion(pregunta)
    inicio = time.perf_counter()
    respuesta_json = enviar_peticion(url, body)
    fin = time.perf_counter()
    if "error" in respuesta_json:
        print(f"Intento {i + 1}: Gemini respondió con error: {respuesta_json['error']['message']}")
        continue
    latencias.append(fin - inicio)
    respuesta_valida = respuesta_json
    print(f"Intento {i + 1}: {latencias[-1]:.2f} segundos")

if latencias:
    latencia_promedio = sum(latencias) / len(latencias)
    print(f"Latencia promedio: {latencia_promedio:.2f} segundos")
    costo = calcular_costo(respuesta_valida, PRECIO_ENTRADA, PRECIO_SALIDA)
    print(f"Costo de la última petición: {costo}")
else:
    print("Ningún intento terminó bien: no hay latencia ni costo que promediar.")



# Paso 3: la calidad, con 2 o 3 preguntas representativas de tu miniaplicación
preguntas_calidad = [
    "Describe en una frase a un gato callejero naranjo atigrado con una mancha blanca en el pecho.",
    "Inventa un nombre y un poder especial para un gato negro de ojos amarillos que vive en una plaza.",
    "Describe en una frase a un gato tricolor (blanco, negro y naranjo) con un ojo de cada color.",
]

for numero, pregunta_calidad in enumerate(preguntas_calidad, start=1):
    time.sleep(20)  # esperar antes de cada petición, para no chocar con el límite de uso (error 429)
    url, body = armar_peticion(pregunta_calidad)
    respuesta_json = enviar_peticion(url, body)
    print(f"\nPregunta {numero}: {pregunta_calidad}")
    if "error" in respuesta_json:
        print("Gemini respondió con error:", respuesta_json["error"]["message"])
        continue
    print(f"Respuesta: {extraer_texto(respuesta_json)}")