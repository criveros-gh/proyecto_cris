"""Pruebas OFFLINE de herramienta con args_schema y de la memoria.

Para la memoria se envuelve un ejecutor FALSO (no llama a la API) que
solo informa cuantos mensajes previos recibio: asi se prueba que el
historial se guarda y se reinyecta, y que las sesiones no se mezclan.
"""
import pytest
from langchain_core.runnables import RunnableLambda
from pydantic import ValidationError

from agente_con_memoria import (
    GestorSesiones,
    agregar_memoria,
    config_de_sesion,
    consultar_estado_gato,
)


# --- Herramienta -----------------------------------------------------------
def test_herramienta_tiene_el_nombre_explicito():
    assert consultar_estado_gato.name == "consultar_estado_gato_con_historial"


def test_herramienta_sin_historial_da_solo_el_estado_actual():
    resultado = consultar_estado_gato.invoke({"codigo_gato": "MICHI-001"})
    assert "adopcion" in resultado and "historial" not in resultado


def test_herramienta_con_historial_lo_incluye():
    resultado = consultar_estado_gato.invoke(
        {"codigo_gato": "MICHI-001", "incluir_historial": True}
    )
    assert "historial" in resultado and "esterilizado" in resultado


def test_herramienta_gato_inexistente_no_lanza_excepcion():
    resultado = consultar_estado_gato.invoke({"codigo_gato": "NO-EXISTE"})
    assert "No se encontro" in resultado


def test_pydantic_rechaza_un_tipo_incorrecto():
    with pytest.raises(ValidationError):
        consultar_estado_gato.invoke(
            {"codigo_gato": "MICHI-001", "incluir_historial": "tal vez"}
        )


# --- Memoria ---------------------------------------------------------------
def _ejecutor_falso():
    return RunnableLambda(
        lambda x: {"output": f"previos={len(x['chat_history'])}"}
    )


def test_el_historial_se_guarda_y_se_reinyecta():
    gestor = GestorSesiones()
    agente = agregar_memoria(_ejecutor_falso(), gestor)
    sesion = config_de_sesion("s1")

    r1 = agente.invoke({"entrada": "hola"}, sesion)
    r2 = agente.invoke({"entrada": "y ahora?"}, sesion)

    assert r1["output"] == "previos=0"
    assert r2["output"] == "previos=2"          # pregunta1 + respuesta1
    assert gestor.cantidad_mensajes("s1") == 4  # crece cada turno


def test_dos_sesiones_no_se_mezclan():
    gestor = GestorSesiones()
    agente = agregar_memoria(_ejecutor_falso(), gestor)

    agente.invoke({"entrada": "pregunta de A"}, config_de_sesion("A"))
    r = agente.invoke({"entrada": "pregunta de B"}, config_de_sesion("B"))

    assert r["output"] == "previos=0"           # B no ve nada de A
    assert gestor.cantidad_mensajes("A") == 2
    assert gestor.cantidad_mensajes("B") == 2


def test_cerrar_sesion_limpia_y_no_falla_si_no_existe():
    gestor = GestorSesiones()
    agente = agregar_memoria(_ejecutor_falso(), gestor)
    agente.invoke({"entrada": "hola"}, config_de_sesion("s1"))

    gestor.cerrar_sesion("s1")
    gestor.cerrar_sesion("s1")  # segunda vez: no debe fallar

    assert gestor.cantidad_mensajes("s1") == 0


def test_sin_session_id_falla_con_un_error_claro():
    agente = agregar_memoria(_ejecutor_falso(), GestorSesiones())
    with pytest.raises(ValueError):
        agente.invoke({"entrada": "hola"})
