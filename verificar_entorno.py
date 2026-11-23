"""Verifica el entorno sin llamar a la API (entregable del Gate 2)."""
import os
import sys
from importlib.metadata import PackageNotFoundError, version

from dotenv import load_dotenv

PAQUETES = ["google-genai", "langchain", "langchain-google-genai",
            "langchain-chroma", "chromadb", "python-dotenv", "pytest"]


def revisar():
    """Devuelve (ok, lineas) con el resultado de cada chequeo."""
    lineas, ok = [], True
    if sys.version_info < (3, 10):
        lineas.append(f"FALTA: Python 3.10 o superior (tienes {sys.version.split()[0]})")
        ok = False
    else:
        lineas.append(f"Python {sys.version.split()[0]} OK")

    for paquete in PAQUETES:
        try:
            lineas.append(f"{paquete} {version(paquete)} OK")
        except PackageNotFoundError:
            lineas.append(f"FALTA: {paquete}  ->  pip install -r requirements.txt")
            ok = False

    load_dotenv(".env")
    if os.environ.get("GEMINI_API_KEY"):
        lineas.append("GEMINI_API_KEY detectada")   # nunca se imprime su valor
    else:
        lineas.append('FALTA: GEMINI_API_KEY (agrégala al archivo ".env")')
        ok = False
    return ok, lineas


if __name__ == "__main__":
    ok, lineas = revisar()
    print("\n".join(lineas))
    print("\nEntorno OK" if ok else "\nEntorno con problemas: corrige las líneas FALTA")
    raise SystemExit(0 if ok else 1)
