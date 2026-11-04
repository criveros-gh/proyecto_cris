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