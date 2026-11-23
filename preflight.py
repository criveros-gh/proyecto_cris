"""B28: chequeo sin API de lo basico del flujo RAG."""
import os


def preflight_check(persist_directory="vectorstore", gitignore_path=".gitignore"):
    """Devuelve la lista de problemas (vacia si todo esta en orden)."""
    problemas = []
    if not os.path.isdir(persist_directory):
        problemas.append(f"{persist_directory} no existe: corriste la indexacion?")

    nombre_carpeta = os.path.basename(persist_directory.rstrip("/\\"))
    if os.path.exists(gitignore_path):
        with open(gitignore_path, encoding="utf-8") as archivo:
            if nombre_carpeta not in archivo.read():
                problemas.append(f"{nombre_carpeta}/ no esta en {gitignore_path}")
    else:
        problemas.append(f"no existe {gitignore_path} en este proyecto")
    return problemas


if __name__ == "__main__":
    problemas = preflight_check("vectorstore")
    if problemas:
        print("Preflight con problemas:")
        for p in problemas:
            print(" -", p)
    else:
        print("Preflight OK: la carpeta del indice existe y esta en .gitignore")
