"""Pruebas de la chain de tres pasos, con el modelo reemplazado por un mock
(no se llama a la API real ni se gastan tokens)."""
from unittest.mock import MagicMock

from langchain_core.messages import AIMessage

from cadena_tres_pasos import construir_cadena


def test_cadena_conecta_los_tres_pasos():
    modelo_falso = MagicMock()
    # side_effect con lista: una respuesta distinta por cada llamada, en orden.
    modelo_falso.side_effect = [
        AIMessage(content="dato 1\ndato 2\ndato 3"),
        AIMessage(content="consejo amable"),
        AIMessage(content="- viñeta 1\n- viñeta 2"),
    ]
    cadena = construir_cadena(modelo_falso)
    resultado = cadena.invoke({"texto": "texto de prueba"})

    assert modelo_falso.call_count == 3
    assert "viñeta" in resultado


def test_cada_paso_recibe_la_salida_del_anterior():
    modelo_falso = MagicMock()
    modelo_falso.side_effect = [
        AIMessage(content="DATOS_PASO_1"),
        AIMessage(content="CONSEJO_PASO_2"),
        AIMessage(content="- final"),
    ]
    cadena = construir_cadena(modelo_falso)
    cadena.invoke({"texto": "x"})

    # El prompt que recibio el 2do paso debe contener la salida del 1ro.
    prompt_paso_2 = modelo_falso.call_args_list[1].args[0].to_string()
    prompt_paso_3 = modelo_falso.call_args_list[2].args[0].to_string()
    assert "DATOS_PASO_1" in prompt_paso_2
    assert "CONSEJO_PASO_2" in prompt_paso_3
