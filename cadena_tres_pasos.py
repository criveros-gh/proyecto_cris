"""Chain de tres pasos con LangChain (Bloque 18).

Caso: a partir de la descripcion libre de un avistamiento de un gato
callejero, el flujo arma una ficha corta y clara.

    Paso 1 (extraer):  saca los datos clave del avistamiento.
    Paso 2 (redactar): convierte esos datos en un consejo de cuidado.
    Paso 3 (formato):  deja el consejo como lista de viñetas.

Cada paso usa la salida del anterior, por eso no se pueden reemplazar
por una sola llamada al modelo.
"""
from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

# Mismo modelo que elegimos en docs/decision-arquitectura.md (Bloque 9).
MODELO = "gemini-3.1-flash-lite"


def construir_cadena(modelo):
    """Arma la chain sin ejecutarla.

    El modelo llega como parametro (no se crea aqui adentro) para poder
    reemplazarlo por un mock en las pruebas.
    """
    # Paso 1: extraer los datos clave (una responsabilidad: resumir hechos).
    plantilla_extraccion = PromptTemplate.from_template(
        "Lee la descripcion de este avistamiento de un gato callejero y "
        "devuelve solo 3 datos clave (aspecto, lugar, estado aparente), "
        "uno por linea, sin inventar nada:\n\n{texto}"
    )

    # Paso 2: redactar un consejo de cuidado (responsabilidad: dar consejo).
    plantilla_consejo = PromptTemplate.from_template(
        "Con estos datos de un gato callejero, escribe un consejo breve "
        "y amable para alguien que quiere ayudarlo, en lenguaje simple:"
        "\n\n{datos}"
    )

    # Paso 3: dar formato (responsabilidad: presentacion).
    plantilla_formato = PromptTemplate.from_template(
        "Convierte este consejo en una lista de viñetas markdown, de "
        "maximo 3 lineas, sin introduccion:\n\n{consejo}"
    )

    # Cada lambda convierte el string que sale de un paso en el
    # diccionario que espera la plantilla siguiente. Los nombres de las
    # claves ("datos", "consejo") deben coincidir EXACTO con las
    # variables de cada plantilla.
    return (
        plantilla_extraccion
        | modelo
        | StrOutputParser()
        | (lambda datos: {"datos": datos})
        | plantilla_consejo
        | modelo
        | StrOutputParser()
        | (lambda consejo: {"consejo": consejo})
        | plantilla_formato
        | modelo
        | StrOutputParser()
    )


if __name__ == "__main__":
    load_dotenv()
    modelo = ChatGoogleGenerativeAI(model=MODELO, temperature=0.3)
    cadena = construir_cadena(modelo)

    avistamiento = (
        "Ayer en la tarde vi un gato gris, bastante flaco, cerca de la "
        "feria de mi barrio en Santiago. Estaba comiendo restos de "
        "verduras y se escondia cuando alguien se acercaba. Tenia una "
        "oreja con un corte antiguo."
    )
    print(cadena.invoke({"texto": avistamiento}))
