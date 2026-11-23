"""Primer agente con herramientas (Bloque 21).

A diferencia de una chain (camino fijo), aqui el MODELO decide que
herramienta usar, cuantas veces y en que orden (patron ReAct:
razonar -> actuar -> observar). Dominio: ayuda a quien rescata gatos
callejeros.

Dos herramientas con propositos claramente distintos:
    buscar_guia_cuidado     -> busca informacion de cuidado basico.
    calcular_presupuesto    -> hace un calculo de dinero.
"""
import logging

from dotenv import load_dotenv
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI

from cadena_tres_pasos import MODELO

logger = logging.getLogger(__name__)

GUIAS = {
    "alimentacion": (
        "Dar comida para gatos (no leche de vaca), agua limpia siempre y "
        "porciones pequenas repartidas en el dia."
    ),
    "esterilizacion": (
        "La esterilizacion ayuda a controlar la poblacion y mejora la salud; "
        "consulta a un veterinario por la edad y el peso adecuados."
    ),
    "frio": (
        "En invierno ofrece un refugio seco y elevado del suelo, con mantas "
        "o cajas aisladas, lejos del viento."
    ),
}


@tool
def buscar_guia_cuidado(tema: str) -> str:
    """Busca una guia breve de cuidado basico de gatos callejeros.

    Usar cuando la pregunta es sobre COMO cuidar a un gato: alimentacion,
    esterilizacion o frio. No sirve para calculos de dinero.
    """
    tema = tema.lower()
    for clave, texto in GUIAS.items():
        if clave in tema:
            return texto
    return "No encontre una guia para ese tema. Consulta a un veterinario."


@tool
def calcular_presupuesto(
    cantidad_gatos: int, costo_por_gato: float, costos_extra: float = 0.0
) -> str:
    """Calcula el presupuesto total en pesos para atender a varios gatos.

    Usar cuando la pregunta pide CUANTO DINERO cuesta algo (por ejemplo
    esterilizar a varios gatos). Recibe la cantidad de gatos, el costo por
    gato y, opcionalmente, costos extra (traslado, insumos).
    """
    try:
        if cantidad_gatos < 0 or costo_por_gato < 0 or costos_extra < 0:
            return "Los valores no pueden ser negativos."
        total = cantidad_gatos * costo_por_gato + costos_extra
        return f"El presupuesto total es de ${total:,.0f} pesos."
    except Exception as error:  # la herramienta no debe tumbar al agente
        logger.exception("Error en calcular_presupuesto")
        return f"No pude calcular el presupuesto: {error}"


HERRAMIENTAS = [buscar_guia_cuidado, calcular_presupuesto]

PROMPT_AGENTE = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Eres un asistente para personas que ayudan a gatos callejeros. "
            "Usa las herramientas disponibles solo cuando las necesites; si "
            "la pregunta es general, responde directamente.",
        ),
        ("human", "{entrada}"),
        # Aqui LangChain anota cada accion y su observacion en cada vuelta.
        MessagesPlaceholder("agent_scratchpad"),
    ]
)


def construir_agente(modelo):
    """Arma el agente. El modelo llega como parametro (facil de reemplazar)."""
    agente = create_tool_calling_agent(modelo, HERRAMIENTAS, PROMPT_AGENTE)
    return AgentExecutor(
        agent=agente,
        tools=HERRAMIENTAS,
        verbose=True,
        # Permite revisar QUE herramienta eligio, no solo la respuesta final.
        return_intermediate_steps=True,
    )


def herramientas_usadas(resultado):
    """Lista los nombres de las herramientas que uso el agente, en orden."""
    return [accion.tool for accion, _obs in resultado["intermediate_steps"]]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    load_dotenv()
    ejecutor = construir_agente(ChatGoogleGenerativeAI(model=MODELO, temperature=0))

    pruebas = [
        ("Como ayudo a un gato callejero con el frio?", "buscar_guia_cuidado"),
        ("Cuanto cuesta esterilizar 4 gatos a 25000 cada uno, mas 10000 de traslado?",
         "calcular_presupuesto"),
        ("Hola, como estas?", None),  # no deberia usar ninguna herramienta
    ]
    for entrada, esperada in pruebas:
        print("\n=== ENTRADA:", entrada)
        try:
            resultado = ejecutor.invoke({"entrada": entrada})
        except Exception:
            logger.exception("El agente fallo (puede ser un 503 temporal)")
            continue
        usadas = herramientas_usadas(resultado)
        print("RESPUESTA:", resultado["output"])
        print("HERRAMIENTAS USADAS:", usadas, "| esperada:", esperada)
