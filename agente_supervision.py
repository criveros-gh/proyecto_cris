"""B23: supervision humana para herramientas de riesgo alto.

Idea: el agente decide CUANDO conviene actuar, pero un humano decide
SI se ejecuta una accion irreversible. Siempre queda un registro.
"""
import select
import sys
from datetime import datetime

from langchain_core.tools import tool

# En memoria (como los historiales del B22). En un caso real: base de datos.
registro_aprobaciones = []


def esperar_aprobacion(mensaje: str, tiempo_limite_segundos: int = 300) -> bool:
    """Pregunta por consola y espera una respuesta con limite de tiempo.

    Devuelve True solo si la persona responde "s" a tiempo.
    Sin respuesta (timeout) o cualquier otra cosa -> False (opcion segura).
    Nota: select sobre stdin funciona en Linux y macOS, no en Windows.
    """
    print(mensaje)
    listo, _, _ = select.select([sys.stdin], [], [], tiempo_limite_segundos)
    if not listo:
        return False
    respuesta = sys.stdin.readline()
    return respuesta.strip().lower() == "s"


def registrar_aprobacion(herramienta: str, argumentos: dict, aprobado: bool) -> None:
    """Deja constancia de la decision humana, se apruebe o no."""
    registro_aprobaciones.append({
        "herramienta": herramienta,
        "argumentos": argumentos,
        "aprobado": aprobado,
        "momento": datetime.now().isoformat(),
    })


@tool
def generar_reembolso(numero_pedido: str, monto: float) -> str:
    """Genera un reembolso para un pedido. Accion irreversible:
    requiere aprobacion humana antes de ejecutarse."""
    mensaje = (
        f"El agente quiere reembolsar ${monto} para el pedido "
        f"{numero_pedido}. ¿Aprobar? (s/n): "
    )
    aprobado = esperar_aprobacion(mensaje)
    registrar_aprobacion(
        herramienta="generar_reembolso",
        argumentos={"numero_pedido": numero_pedido, "monto": monto},
        aprobado=aprobado,
    )
    if not aprobado:
        return "Reembolso no aprobado por el supervisor humano."
    return f"Reembolso de ${monto} generado para el pedido {numero_pedido}."


if __name__ == "__main__":
    resultado = generar_reembolso.invoke({"numero_pedido": "PED789", "monto": 1500.0})
    print(resultado)
    print("registro:", registro_aprobaciones)
