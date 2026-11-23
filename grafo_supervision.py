"""B32: punto de supervision humana con LangGraph.

Desplegar una version nueva de prompt a produccion NO debe ocurrir sola.
El grafo se pausa con interrupt() y solo sigue cuando alguien llama
Command(resume=True/False). Ambos caminos (aprobar y rechazar) terminan
en END: rechazar es una decision real, no un error.

Nota: InMemorySaver vive en la memoria del proceso. Si el proceso se reinicia
mientras se espera la aprobacion, el estado pendiente se pierde. En produccion
se usa un checkpointer durable (p. ej. SqliteSaver); solo cambia compile().
"""
import uuid
from typing import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt


class EstadoDespliegue(TypedDict):
    huella_nueva: str
    aprobado: bool
    resultado: str


def proponer(estado: EstadoDespliegue):
    return {}


def supervisar(estado: EstadoDespliegue):
    decision = interrupt({
        "motivo": "aprobar nueva version de prompt en produccion",
        "huella_propuesta": estado["huella_nueva"],
    })
    return {"aprobado": decision}


def aplicar(estado: EstadoDespliegue):
    if estado["aprobado"]:
        return {"resultado": "activada"}
    return {"resultado": "rechazada: se mantiene la version anterior"}


def construir_grafo(checkpointer=None):
    grafo = StateGraph(EstadoDespliegue)
    grafo.add_node("proponer", proponer)
    grafo.add_node("supervisar", supervisar)
    grafo.add_node("aplicar", aplicar)
    grafo.add_edge(START, "proponer")
    grafo.add_edge("proponer", "supervisar")
    grafo.add_edge("supervisar", "aplicar")
    grafo.add_edge("aplicar", END)
    return grafo.compile(checkpointer=checkpointer or InMemorySaver())


def nuevo_thread_id(prefijo="despliegue"):
    """Un thread_id unico por solicitud: reutilizar uno pisa la solicitud anterior."""
    return f"{prefijo}-{uuid.uuid4().hex[:8]}"


def solicitar_despliegue(app, huella_nueva):
    """Inicia una solicitud y la deja PAUSADA esperando aprobacion.
    Devuelve el config (con su thread_id) para resolverla despues."""
    config = {"configurable": {"thread_id": nuevo_thread_id()}}
    app.invoke({"huella_nueva": huella_nueva, "aprobado": False, "resultado": ""}, config=config)
    return config


def pendiente(app, config):
    """Que esta esperando aprobacion (None si no hay nada pendiente)."""
    snapshot = app.get_state(config)
    if not snapshot.next or not snapshot.interrupts:
        return None
    return snapshot.interrupts[0].value


def resolver(app, config, aprobar, huella_esperada=None):
    """Aprueba o rechaza una solicitud pendiente.
    - aprobar debe ser bool (un texto como "no" seria verdadero y APROBARIA).
    - falla si no hay nada pendiente (evita aprobaciones duplicadas).
    - si se pasa huella_esperada, falla si la pendiente es OTRA version
      (la persona debe aprobar lo mismo que reviso)."""
    if not isinstance(aprobar, bool):
        raise TypeError("aprobar debe ser True o False")
    snapshot = app.get_state(config)
    if not snapshot.next:
        raise ValueError("este thread_id no tiene ninguna aprobacion pendiente")
    if huella_esperada is not None and snapshot.values.get("huella_nueva") != huella_esperada:
        raise ValueError("la version pendiente no es la que la persona reviso")
    return app.invoke(Command(resume=aprobar), config=config)


if __name__ == "__main__":
    app = construir_grafo()
    huella = "ba2bcb4f4f13"  # ejemplo; en el flujo real sale de registro_prompts

    cfg = solicitar_despliegue(app, huella)
    print("1) pendiente:", pendiente(app, cfg))
    print("2) tras aprobar:", resolver(app, cfg, True, huella_esperada=huella))

    cfg2 = solicitar_despliegue(app, huella)
    print("3) tras rechazar:", resolver(app, cfg2, False, huella_esperada=huella))

    try:
        resolver(app, cfg, True)
    except ValueError as e:
        print("4) segundo intento sobre la misma solicitud ->", e)
