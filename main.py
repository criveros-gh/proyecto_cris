"""Punto de entrada de la miniaplicación: app de michis (Gate 1).

Recibe la descripción de un gato callejero y genera su carta de colección
(nombre y poder) usando Gemini, junto con el costo de la petición.

Uso:
    python3 main.py
    python3 main.py "Un gato blanco con una oreja negra que duerme en un auto"
"""
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from consumir_gemini import crear_carta

DESCRIPCION_DE_EJEMPLO = "Un gato negro de ojos amarillos que vive en una plaza."


def main():
    descripcion = " ".join(sys.argv[1:]) or DESCRIPCION_DE_EJEMPLO
    print(f"Gato: {descripcion}")
    try:
        carta, costo = crear_carta(descripcion)
    except (ValueError, RuntimeError) as error:
        print(f"No se pudo crear la carta: {error}")
        sys.exit(1)
    print(f"Nombre: {carta['nombre']}")
    print(f"Poder: {carta['poder']}")
    print(f"Costo de la petición: {costo:.8f} USD")
    print("Proceso terminado sin errores.")


if __name__ == "__main__":
    main()
