"""B32: versionado de prompts.

Un prompt cambia con el tiempo. Sin historial, la pregunta "que prompt exacto
genero esta respuesta?" no tiene respuesta. Este registro guarda, por cada
version: huella del texto exacto, autor, fecha, nota del cambio y el modelo
contra el que se probo. No hay infraestructura nueva: libreria estandar.
"""
import difflib
import hashlib
import json
from datetime import date


def huella_prompt(texto):
    """Huella corta (sha256) del texto EXACTO. Una letra distinta -> otra huella."""
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()[:12]


class RegistroDePrompts:
    def __init__(self):
        self.versiones = []

    def registrar(self, nombre, texto, autor, nota, modelo=None):
        """Agrega una version nueva. Falla si no hay texto o si no cambio nada
        respecto de la ultima version del mismo prompt (seria ruido en el historial)."""
        if not isinstance(texto, str) or not texto.strip():
            raise ValueError("el texto del prompt no puede estar vacio")
        if not nota or not nota.strip():
            raise ValueError("toda version necesita una nota que explique el cambio")
        huella = huella_prompt(texto)
        anterior = self.ultima(nombre)
        if anterior is not None and anterior["huella"] == huella:
            raise ValueError(f"'{nombre}' no cambio: ya existe la huella {huella}")
        version = {
            "nombre": nombre,
            "huella": huella,
            "texto": texto,
            "autor": autor,
            "fecha": str(date.today()),
            "nota": nota,
            "modelo": modelo,
        }
        self.versiones.append(version)
        return version

    def ultima(self, nombre):
        candidatas = [v for v in self.versiones if v["nombre"] == nombre]
        return candidatas[-1] if candidatas else None

    def buscar_por_huella(self, huella):
        """Responde "que prompt genero esta respuesta?" a partir de la huella
        que quedo registrada junto a ella."""
        for v in self.versiones:
            if v["huella"] == huella:
                return v
        return None

    def guardar(self, archivo):
        with open(archivo, "w", encoding="utf-8") as f:
            json.dump(self.versiones, f, ensure_ascii=False, indent=2)

    @classmethod
    def cargar(cls, archivo):
        registro = cls()
        with open(archivo, encoding="utf-8") as f:
            registro.versiones = json.load(f)
        return registro


def diff_prompts(anterior, nueva):
    """Diff palabra por palabra (mismo mecanismo que git diff):
    '+' agregado, '-' quitado, sin marca es contexto."""
    return list(difflib.unified_diff(
        anterior.split(), nueva.split(),
        fromfile="version_anterior", tofile="version_nueva", lineterm="",
    ))


def registrar_prompts_del_proyecto(modelo=None):
    """Registra las dos versiones REALES del prompt de este proyecto:
    v1 = plantilla unica del B26; v2 = prompt de sistema + plantilla con
    contexto delimitado del B31."""
    from recuperacion import PROMPT_TEMPLATE
    from seguridad_prompt import PLANTILLA_USUARIO, PROMPT_SISTEMA

    registro = RegistroDePrompts()
    registro.registrar(
        "prompt_rag", PROMPT_TEMPLATE, "cris",
        "version original del B26: una sola plantilla que exige citar [n]",
        modelo=modelo,
    )
    registro.registrar(
        "prompt_rag", PROMPT_SISTEMA + "\n---\n" + PLANTILLA_USUARIO, "cris",
        "B31: separa rol de sistema, delimita el contexto como dato "
        "y agrega instruccion anti-inyeccion",
        modelo=modelo,
    )
    return registro


if __name__ == "__main__":
    from cadena_tres_pasos import MODELO

    registro = registrar_prompts_del_proyecto(modelo=MODELO)
    for v in registro.versiones:
        print(v["huella"], "-", v["nota"])
    v1, v2 = registro.versiones
    print("huellas distintas?", v1["huella"] != v2["huella"])
    print("ultima version activa:", registro.ultima("prompt_rag")["huella"])
    print("--- diff (primeras 25 lineas) ---")
    for linea in diff_prompts(v1["texto"], v2["texto"])[:25]:
        print(linea)
    registro.guardar("registro_prompts.json")
    print("guardado en registro_prompts.json")
