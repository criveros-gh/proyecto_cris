"""Verificacion de extremo a extremo (checklist del Bloque 20).

Tabla del checklist -> pruebas:
  Clasificacion  : normaliza; no rompe con texto raro.
  Bifurcacion    : cada ruta + ruta por defecto (ver test_enrutamiento.py).
  Cada ruta      : with_fallbacks probado con un fallo REAL simulado.
  Flujo completo : un fallo en cualquier paso igual entrega respuesta,
                   y el error queda registrado (no se oculta).
"""
import logging
from unittest.mock import MagicMock

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

from enrutamiento import (
    construir_cadena_con_enrutamiento,
    construir_cadena_emergencia_segura,
    construir_paso_clasificacion,
    procesar_mensaje_seguro,
)


def _fallar(x):
    raise ConnectionError("simulado")


# --- Clasificacion ---------------------------------------------------------
def test_clasificacion_normaliza_antes_de_comparar():
    modelo_falso = MagicMock()
    modelo_falso.return_value = AIMessage(content=" Emergencia \n")
    resultado = construir_paso_clasificacion(modelo_falso).invoke(
        {"mensaje": "algo salio mal"}
    )
    assert resultado == "emergencia"


def test_clasificacion_con_respuesta_vacia_no_rompe():
    modelo_falso = MagicMock()
    modelo_falso.return_value = AIMessage(content="")
    resultado = construir_paso_clasificacion(modelo_falso).invoke(
        {"mensaje": ""}
    )
    assert resultado == ""  # no explota; la bifurcacion lo manda al default


# --- Camino normal (una suite solo de fallos no probaria nada) -------------
def test_camino_normal_devuelve_la_respuesta_de_la_ruta():
    clasificacion_falsa = MagicMock(return_value="emergencia")
    ruta_ok = RunnableLambda(lambda x: "respuesta normal")
    cadena = construir_cadena_con_enrutamiento(
        paso_clasificacion=clasificacion_falsa,
        cadena_emergencia=construir_cadena_emergencia_segura(ruta_ok),
    )
    assert procesar_mensaje_seguro(cadena, "gato herido") == "respuesta normal"


# --- Fallback de una ruta --------------------------------------------------
def test_cadena_emergencia_usa_fallback_ante_fallo_del_modelo():
    cadena_segura = construir_cadena_emergencia_segura(RunnableLambda(_fallar))
    resultado = cadena_segura.invoke({"mensaje": "gato herido"})
    # El respaldo es util: da pasos concretos, no solo "error".
    assert "veterinaria" in resultado.lower()


# --- Flujo completo --------------------------------------------------------
def test_procesar_mensaje_seguro_no_propaga_excepciones():
    clasificacion_falsa = MagicMock()
    clasificacion_falsa.side_effect = ConnectionError("simulado")
    cadena_falsa = construir_cadena_con_enrutamiento(
        paso_clasificacion=clasificacion_falsa,
    )
    resultado = procesar_mensaje_seguro(cadena_falsa, "mensaje de prueba")
    assert "no pudimos procesar" in resultado.lower()


def test_el_error_queda_registrado_no_se_oculta(caplog):
    clasificacion_falsa = MagicMock()
    clasificacion_falsa.side_effect = ConnectionError("simulado")
    cadena_falsa = construir_cadena_con_enrutamiento(
        paso_clasificacion=clasificacion_falsa,
    )
    with caplog.at_level(logging.ERROR):
        procesar_mensaje_seguro(cadena_falsa, "mensaje de prueba")
    assert "Error procesando mensaje" in caplog.text
    assert "ConnectionError" in caplog.text  # traceback incluido
