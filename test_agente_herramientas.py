"""Pruebas OFFLINE de las herramientas del agente (sin llamar a la API).

Las dos validaciones con el modelo real (que el agente ELIJA bien la
herramienta) se hacen a mano corriendo agente_con_herramientas.py y
mirando intermediate_steps, como pide el Bloque 21.
"""
from agente_con_herramientas import (
    HERRAMIENTAS,
    buscar_guia_cuidado,
    calcular_presupuesto,
)


def test_guia_devuelve_texto_para_tema_conocido():
    assert "refugio" in buscar_guia_cuidado.invoke("frio en invierno").lower()


def test_guia_tema_desconocido_no_rompe():
    resultado = buscar_guia_cuidado.invoke("astronomia")
    assert "veterinario" in resultado.lower()


def test_presupuesto_calcula_bien():
    resultado = calcular_presupuesto.invoke(
        {"cantidad_gatos": 4, "costo_por_gato": 25000, "costos_extra": 10000}
    )
    assert "110,000" in resultado


def test_presupuesto_rechaza_negativos_sin_excepcion():
    resultado = calcular_presupuesto.invoke(
        {"cantidad_gatos": -1, "costo_por_gato": 100}
    )
    assert "negativos" in resultado


def test_las_herramientas_devuelven_str_y_tienen_docstring():
    # Sin docstring claro el agente elige mal; sin str falla al revisar pasos.
    for herramienta in HERRAMIENTAS:
        assert herramienta.description.strip()
    assert isinstance(buscar_guia_cuidado.invoke("frio"), str)
