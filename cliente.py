import time
import random
from typing import Callable, Any

from src.consumir_gemini import (
    armar_peticion,
    enviar_peticion,
    extraer_texto,
    SYSTEM_INSTRUCTION_POR_DEFECTO,
)


def con_reintento(
    funcion: Callable[[], Any],
    intentos: int = 3,
    espera_base: float = 2,
    espera_maxima: float = 30,
) -> Any:
    for intento in range(1, intentos + 1):
        try:
            return funcion()
        except TimeoutError:
            if intento == intentos:
                raise
            espera = min(espera_base * (2 ** (intento - 1)), espera_maxima)
            espera_con_jitter = espera + random.uniform(0, espera * 0.1)
            print(f"Intento {intento} de {intentos} falló. Reintentando en {espera_con_jitter:.1f}s...")
            time.sleep(espera_con_jitter)



COSTO_POR_1000_TOKENS = 0.0015
costo_total_sesion = 0.0


def registrar_costo(respuesta: dict) -> float:
    global costo_total_sesion
    uso = respuesta.get("usageMetadata", {})
    total_tokens = uso.get("totalTokenCount", 0)
    costo_estimado = (total_tokens / 1000) * COSTO_POR_1000_TOKENS
    costo_total_sesion += costo_estimado
    print(f"Operación: {total_tokens} tokens, costo estimado: ${costo_estimado:.5f} (acumulado: ${costo_total_sesion:.5f})")
    return costo_estimado







def consultar_modelo(
    pregunta: str,
    system_instruction: str = SYSTEM_INSTRUCTION_POR_DEFECTO,
) -> str:
    url, body = armar_peticion(pregunta, system_instruction)
    try:
        datos = con_reintento(lambda: enviar_peticion(url, body))
    except TimeoutError:
        raise RuntimeError("El servicio no respondió tras varios intentos. Intenta más tarde.")
    return extraer_texto(datos)