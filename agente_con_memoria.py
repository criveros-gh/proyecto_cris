"""Herramienta personalizada + memoria entre interacciones (Bloque 22).

Tres bloques, cada uno con una responsabilidad:
    1. Herramienta con varios parametros (args_schema con Pydantic).
    2. Agente + ejecutor, con historial en el prompt.
    3. Memoria por sesion (RunnableWithMessageHistory).

Dominio: seguimiento de gatos rescatados (datos de ejemplo inventados).
"""
import logging

from dotenv import load_dotenv
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

from agente_con_herramientas import calcular_presupuesto
from cadena_tres_pasos import MODELO

logger = logging.getLogger(__name__)

# --- 1. Herramienta con args_schema ----------------------------------------
GATOS = {
    "MICHI-001": {
        "actual": "en tratamiento veterinario, listo para adopcion en 1 semana",
        "historial": ["rescatado en la calle", "esterilizado", "en tratamiento"],
    },
    "MICHI-002": {
        "actual": "adoptado",
        "historial": ["rescatado en la calle", "vacunado", "adoptado"],
    },
}


class ArgumentosConsultaGato(BaseModel):
    """Cada campo lleva su descripcion: el modelo sabe que se espera en cada uno."""

    codigo_gato: str = Field(
        description="Codigo del gato rescatado, por ejemplo 'MICHI-001'.",
    )
    incluir_historial: bool = Field(
        default=False,
        description="Si es True, incluye el historial completo, no solo el estado actual.",
    )


@tool("consultar_estado_gato_con_historial", args_schema=ArgumentosConsultaGato)
def consultar_estado_gato(codigo_gato: str, incluir_historial: bool = False) -> str:
    """Consulta el estado de un gato rescatado, con la opcion de incluir
    su historial. Usar cuando preguntan como esta o por donde ha pasado
    un gato en particular."""
    gato = GATOS.get(codigo_gato.upper())
    if gato is None:
        return f"No se encontro un gato con el codigo {codigo_gato}."
    if not incluir_historial:
        return gato["actual"]
    return f"{gato['actual']} (historial: {', '.join(gato['historial'])})"


HERRAMIENTAS = [consultar_estado_gato, calcular_presupuesto]

# --- 2. Agente con historial en el prompt ----------------------------------
PROMPT_AGENTE = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Eres un asistente para personas que rescatan gatos callejeros. "
            "Usa las herramientas cuando las necesites y recuerda lo hablado "
            "antes en la conversacion.",
        ),
        # El orden importa: historial ANTES del mensaje actual...
        MessagesPlaceholder("chat_history"),
        ("human", "{entrada}"),
        # ...y el scratchpad (razonamiento de ESTA consulta) despues.
        MessagesPlaceholder("agent_scratchpad"),
    ]
)


def construir_ejecutor(modelo):
    agente = create_tool_calling_agent(modelo, HERRAMIENTAS, PROMPT_AGENTE)
    return AgentExecutor(
        agent=agente,
        tools=HERRAMIENTAS,
        verbose=True,
        return_intermediate_steps=True,
    )


# --- 3. Memoria por sesion -------------------------------------------------
class GestorSesiones:
    """Un historial por session_id. Vive en memoria: se pierde al reiniciar.

    En un servicio real se reemplazaria SOLO obtener_historial por una base
    de datos; el resto del codigo no cambia.
    """

    def __init__(self):
        self._historiales = {}

    def obtener_historial(self, session_id: str):
        if session_id not in self._historiales:
            self._historiales[session_id] = InMemoryChatMessageHistory()
        return self._historiales[session_id]

    def cantidad_mensajes(self, session_id: str) -> int:
        return len(self.obtener_historial(session_id).messages)

    def cerrar_sesion(self, session_id: str) -> None:
        """No falla si la sesion ya no existe; evita acumular historiales."""
        self._historiales.pop(session_id, None)


def agregar_memoria(ejecutor, gestor: GestorSesiones):
    """Envuelve (no reemplaza) al ejecutor con un historial por sesion."""
    return RunnableWithMessageHistory(
        ejecutor,
        gestor.obtener_historial,
        input_messages_key="entrada",      # debe coincidir con la clave al invocar
        history_messages_key="chat_history",  # debe coincidir con el prompt
    )


def config_de_sesion(session_id: str) -> dict:
    return {"configurable": {"session_id": session_id}}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    load_dotenv()
    gestor = GestorSesiones()
    agente = agregar_memoria(
        construir_ejecutor(ChatGoogleGenerativeAI(model=MODELO, temperature=0)),
        gestor,
    )

    try:
        sesion = config_de_sesion("rescatista_1")
        r1 = agente.invoke({"entrada": "Como esta MICHI-001? Incluye su historial."}, sesion)
        print("TURNO 1:", r1["output"])
        r2 = agente.invoke({"entrada": "Y ese mismo gato, ya fue adoptado?"}, sesion)
        print("TURNO 2:", r2["output"])
        print("Mensajes en el historial:", gestor.cantidad_mensajes("rescatista_1"))

        # Dos sesiones NO deben mezclarse.
        agente.invoke({"entrada": "Te pregunto por MICHI-002."}, config_de_sesion("a"))
        r3 = agente.invoke({"entrada": "De que gato te pregunte?"}, config_de_sesion("b"))
        print("SESION B (no deberia saberlo):", r3["output"])
    except Exception:
        logger.exception("El agente fallo (puede ser un 503 temporal)")
