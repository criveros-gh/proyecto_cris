import time
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
    espera_segundos: int = 2,
) -> Any:
    for intento in range(1, intentos + 1):
        try:
            return funcion()
        except TimeoutError:
            if intento == intentos:
                raise
            print(f"Intento {intento} de {intentos} falló por límite de uso. Reintentando...")
            time.sleep(espera_segundos)