"""Pruebas del enrutamiento. La clasificacion se mockea para FORZAR cada
ruta: si dependieran del modelo real, la prueba no controlaria nada."""
from unittest.mock import MagicMock

from langchain_core.messages import AIMessage

from enrutamiento import (
    construir_cadena_con_enrutamiento,
    construir_paso_clasificacion,
)


def test_enrutamiento_va_a_cadena_emergencia():
    clasificacion_falsa = MagicMock()
    clasificacion_falsa.return_value = "emergencia"
    cadena_emergencia_falsa = MagicMock()
    cadena_emergencia_falsa.return_value = "respuesta de emergencia"

    cadena = construir_cadena_con_enrutamiento(
        paso_clasificacion=clasificacion_falsa,
        cadena_emergencia=cadena_emergencia_falsa,
    )
    resultado = cadena.invoke({"mensaje": "gato herido en la calle"})

    assert cadena_emergencia_falsa.called
    assert resultado == "respuesta de emergencia"


def test_enrutamiento_va_a_cadena_adopcion():
    clasificacion_falsa = MagicMock()
    clasificacion_falsa.return_value = "adopcion"
    cadena_adopcion_falsa = MagicMock()
    cadena_adopcion_falsa.return_value = "respuesta de adopcion"

    cadena = construir_cadena_con_enrutamiento(
        paso_clasificacion=clasificacion_falsa,
        cadena_adopcion=cadena_adopcion_falsa,
    )
    resultado = cadena.invoke({"mensaje": "quiero adoptar un gato"})

    assert cadena_adopcion_falsa.called
    assert resultado == "respuesta de adopcion"


def test_enrutamiento_usa_default_ante_categoria_desconocida():
    clasificacion_falsa = MagicMock()
    clasificacion_falsa.return_value = "categoria_inventada"
    cadena_consulta_falsa = MagicMock()
    cadena_consulta_falsa.return_value = "respuesta por defecto"

    cadena = construir_cadena_con_enrutamiento(
        paso_clasificacion=clasificacion_falsa,
        cadena_consulta=cadena_consulta_falsa,
    )
    resultado = cadena.invoke({"mensaje": "mensaje ambiguo"})

    assert cadena_consulta_falsa.called
    assert resultado == "respuesta por defecto"


def test_clasificacion_normaliza_antes_de_comparar():
    modelo_falso = MagicMock()
    modelo_falso.return_value = AIMessage(content=" Emergencia \n")

    resultado = construir_paso_clasificacion(modelo_falso).invoke(
        {"mensaje": "algo salio mal"}
    )

    assert resultado == "emergencia"


def test_el_mensaje_original_llega_a_la_ruta_elegida():
    """assign debe conservar 'mensaje' junto a 'categoria'."""
    clasificacion_falsa = MagicMock()
    clasificacion_falsa.return_value = "emergencia"
    cadena_emergencia_falsa = MagicMock(return_value="ok")

    cadena = construir_cadena_con_enrutamiento(
        paso_clasificacion=clasificacion_falsa,
        cadena_emergencia=cadena_emergencia_falsa,
    )
    cadena.invoke({"mensaje": "texto original"})

    recibido = cadena_emergencia_falsa.call_args.args[0]
    assert recibido["mensaje"] == "texto original"
    assert recibido["categoria"] == "emergencia"
