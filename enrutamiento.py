"""Enrutamiento condicional con LangChain (Bloque 19).

Caso: llega un mensaje sobre un gato callejero y el flujo decide, segun
su tipo, que camino tomar (cada camino tiene su propio prompt):

    emergencia -> gato herido o en peligro: pasos urgentes.
    adopcion   -> alguien quiere adoptar o dar en adopcion.
    consulta   -> cualquier otra cosa (ruta por defecto).

Estructura (una responsabilidad por bloque):
    1. Clasificacion de la entrada.
    2. Las rutas posibles.
    3. La bifurcacion que las conecta.
"""
import logging

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import (
    RunnableBranch,
    RunnableLambda,
    RunnablePassthrough,
)
from langchain_google_genai import ChatGoogleGenerativeAI

from cadena_tres_pasos import MODELO

# --- 1. Clasificacion de la entrada ---------------------------------------
plantilla_clasificacion = PromptTemplate.from_template(
    "Clasifica el siguiente mensaje sobre un gato callejero en una sola "
    "palabra: emergencia, adopcion o consulta. Responde solo con esa "
    "palabra.\n\n{mensaje}"
)


def construir_paso_clasificacion(modelo):
    """Paso que devuelve la categoria ya normalizada.

    El modelo puede responder "Emergencia", "emergencia." o " emergencia \n";
    el strip().lower() evita que la comparacion falle en silencio.
    """
    return (
        plantilla_clasificacion
        | modelo
        | StrOutputParser()
        | (lambda texto: texto.strip().lower())
    )


# --- 2. Las tres rutas posibles -------------------------------------------
def construir_rutas(modelo):
    """Devuelve una cadena por categoria, cada una con un prompt distinto."""
    cadena_emergencia = (
        PromptTemplate.from_template(
            "Un gato callejero esta herido o en peligro. Da maximo 4 pasos "
            "urgentes y concretos, en orden, para quien lo encontro (sin "
            "reemplazar a un veterinario):\n\n{mensaje}"
        )
        | modelo
        | StrOutputParser()
    )
    cadena_adopcion = (
        PromptTemplate.from_template(
            "Responde con calidez a esta consulta de adopcion de un gato "
            "callejero y explica que hay que considerar antes de adoptar "
            "(esterilizacion, vacunas, adaptacion):\n\n{mensaje}"
        )
        | modelo
        | StrOutputParser()
    )
    cadena_consulta = (
        PromptTemplate.from_template(
            "Responde esta consulta sobre gatos callejeros de forma clara "
            "y breve:\n\n{mensaje}"
        )
        | modelo
        | StrOutputParser()
    )
    return cadena_emergencia, cadena_adopcion, cadena_consulta


# --- 3. La bifurcacion que las conecta ------------------------------------
def construir_cadena_con_enrutamiento(
    paso_clasificacion,
    cadena_emergencia=None,
    cadena_adopcion=None,
    cadena_consulta=None,
):
    """Conecta clasificacion + bifurcacion.

    Cada ruta es opcional para poder probar una sola con mocks; la que no
    se pasa nunca se ejecuta si no es la elegida.
    """
    cadena_emergencia = cadena_emergencia or RunnablePassthrough()
    cadena_adopcion = cadena_adopcion or RunnablePassthrough()
    cadena_consulta = cadena_consulta or RunnablePassthrough()

    # El orden importa: prueba de arriba hacia abajo y se detiene en la
    # primera verdadera. La ultima (sin condicion) es la ruta por defecto.
    bifurcacion = RunnableBranch(
        (lambda x: x["categoria"] == "emergencia", cadena_emergencia),
        (lambda x: x["categoria"] == "adopcion", cadena_adopcion),
        cadena_consulta,
    )
    # assign agrega "categoria" al diccionario SIN perder "mensaje".
    return RunnablePassthrough.assign(categoria=paso_clasificacion) | bifurcacion


# --- 4. Manejo de errores (Bloque 20) --------------------------------------
logger = logging.getLogger(__name__)

# Respaldo para la ruta de emergencia: NO es solo "hubo un error". Entrega
# pasos seguros y utiles aunque el modelo no responda.
respuesta_generica_emergencia = RunnableLambda(
    lambda x: (
        "No pudimos generar una respuesta automatica ahora. Mientras tanto: "
        "mantén la calma, no muevas bruscamente al gato, abrigalo con una "
        "toalla y llama a una clinica veterinaria o a un rescatista de "
        "animales de tu zona lo antes posible."
    )
)


def construir_cadena_emergencia_segura(cadena_emergencia):
    """Protege la ruta de emergencia: si el modelo falla, usa el respaldo."""
    return cadena_emergencia.with_fallbacks([respuesta_generica_emergencia])


def procesar_mensaje_seguro(cadena, mensaje):
    """Red de seguridad final: ningun fallo deja al usuario sin respuesta.

    La cadena llega como parametro (no se lee de una variable global) para
    poder inyectar una cadena falsa en las pruebas.
    Manejar un error no es ocultarlo: queda registrado con su traceback.
    """
    try:
        return cadena.invoke({"mensaje": mensaje})
    except Exception:
        logger.exception("Error procesando mensaje")
        return (
            "No pudimos procesar tu mensaje en este momento. "
            "Intenta de nuevo mas tarde."
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    load_dotenv()
    modelo = ChatGoogleGenerativeAI(model=MODELO, temperature=0)
    emergencia, adopcion, consulta = construir_rutas(modelo)
    cadena = construir_cadena_con_enrutamiento(
        construir_paso_clasificacion(modelo),
        construir_cadena_emergencia_segura(emergencia),
        adopcion,
        consulta,
    )

    mensajes = [
        "Hay un gatito en la calle con una pata sangrando y no se mueve.",
        "Me gustaria adoptar un gato callejero, que debo saber?",
        "Cada cuanto debo darle comida a un gato callejero?",
    ]
    for mensaje in mensajes:
        print("MENSAJE:", mensaje)
        print(procesar_mensaje_seguro(cadena, mensaje))
        print("-" * 60)
