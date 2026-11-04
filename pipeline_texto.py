import re

from cliente import consultar_modelo


def limpiar_texto(texto: str) -> str:
    """Normaliza el texto: minúsculas y sin puntuación."""
    if not isinstance(texto, str):
        tipo = type(texto).__name__
        raise TypeError(f"limpiar_texto espera str, no {tipo}")

    texto = texto.lower()
    texto = re.sub(r"[^\w\s]", "", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


def tokenizar(texto_limpio: str) -> list[str]:
    """Convierte texto limpio en una lista de tokens."""
    return texto_limpio.split()


def procesar_texto(texto: str) -> list[str]:
    """Limpia y tokeniza el texto."""
    texto_limpio = limpiar_texto(texto)
    return tokenizar(texto_limpio)


def proporcion_coincidencia(
    tokens_referencia: list[str], tokens_respuesta: list[str]
) -> float:
    """Proporción de palabras distintas de la referencia que aparecen en la respuesta."""
    palabras_referencia = set(tokens_referencia)
    if not palabras_referencia:
        return 0.0
    comunes = palabras_referencia & set(tokens_respuesta)
    return len(comunes) / len(palabras_referencia)


CASOS = [
    {
        "consulta": "¿Qué comen los gatos callejeros?",
        "referencia": "Los gatos callejeros comen lo que puedan encontrar.",
    },
    {
        "consulta": "¿Cómo ayudar a un gato callejero en invierno?",
        "referencia": "Para ayudar a un gato callejero en invierno hay que darle refugio abrigado, comida y agua.",
    },
    {
        "consulta": "¿Cada cuánto debe ir un gato al veterinario?",
        "referencia": "Un gato debería ir al veterinario al menos una vez al año para vacunas y control.",
    },
]


if __name__ == "__main__":
    for numero, caso in enumerate(CASOS, start=1):
        respuesta = consultar_modelo(caso["consulta"])
        referencia = caso["referencia"]

        pct_crudo = proporcion_coincidencia(referencia.split(), respuesta.split())
        pct_procesado = proporcion_coincidencia(
            procesar_texto(referencia), procesar_texto(respuesta)
        )

        print(f"[Caso {numero}] Consulta: {caso['consulta']}")
        print(f"[Caso {numero}] Respuesta: {respuesta}")
        print(f"[Caso {numero}] Coincidencia texto crudo: {pct_crudo:.1%}")
        print(f"[Caso {numero}] Coincidencia texto procesado: {pct_procesado:.1%}")
        print()