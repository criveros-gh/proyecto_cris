import json
import os
import sys
import time

# Permite importar tu módulo, que está en la carpeta src/
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from banco import BANCO_DE_PROMPTS
from consumir_gemini import armar_peticion, enviar_peticion, extraer_texto, parsear_respuesta_json

registro = {}

for prompt in BANCO_DE_PROMPTS:
    exitos = 0
    intentos = 3
    for intento in range(intentos):
        url, body = armar_peticion(
            prompt["ejemplo_usuario"],
            prompt["system_instruction"],
            prompt.get("response_schema"),
        )
        respuesta = enviar_peticion(url, body)
        if "error" in respuesta:
            print(f"  intento {intento + 1} falló: Gemini respondió con error: {respuesta['error']['message']}")
            time.sleep(3)
            continue
        try:
            texto = extraer_texto(respuesta)
            datos = parsear_respuesta_json(texto, prompt["claves_esperadas"])
            if all(clave in datos for clave in prompt["claves_esperadas"]):
                exitos += 1
        except (ValueError, RuntimeError) as error:
            print(f"  intento {intento + 1} falló: {error}")
        time.sleep(3)
    print(f"{prompt['nombre']}: {exitos}/{intentos} respuestas válidas")
    registro[prompt["nombre"]] = {"exitos": exitos, "intentos": intentos}

with open("prompts/registro_resultados.json", "w", encoding="utf-8") as archivo:
    json.dump(registro, archivo, indent=2, ensure_ascii=False)