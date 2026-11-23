"""Pruebas offline de B23: aprobacion humana y trazas. Sin API ni teclado."""
import json
import os
import sys
from types import SimpleNamespace

import pytest

import agente_supervision as sup
import trazas_agente as tr


@pytest.fixture(autouse=True)
def limpiar_registro():
    sup.registro_aprobaciones.clear()


def _stdin_con(monkeypatch, texto):
    """Reemplaza stdin por una tuberia real (select necesita un descriptor)."""
    lectura, escritura = os.pipe()
    if texto is not None:
        os.write(escritura, texto.encode())
    monkeypatch.setattr(sys, "stdin", os.fdopen(lectura))
    return escritura


def test_aprueba_con_s(monkeypatch):
    _stdin_con(monkeypatch, "s\n")
    assert sup.esperar_aprobacion("¿ok?", 1) is True


def test_rechaza_con_n(monkeypatch):
    _stdin_con(monkeypatch, "n\n")
    assert sup.esperar_aprobacion("¿ok?", 1) is False


def test_sin_respuesta_a_tiempo_no_aprueba(monkeypatch):
    _stdin_con(monkeypatch, None)
    assert sup.esperar_aprobacion("¿ok?", 0.2) is False


def test_reembolso_aprobado_ejecuta_y_registra(monkeypatch):
    monkeypatch.setattr(sup, "esperar_aprobacion", lambda m, *a, **k: True)
    r = sup.generar_reembolso.invoke({"numero_pedido": "P1", "monto": 100.0})
    assert "generado" in r
    assert sup.registro_aprobaciones[0]["aprobado"] is True


def test_reembolso_rechazado_no_ejecuta_pero_registra(monkeypatch):
    monkeypatch.setattr(sup, "esperar_aprobacion", lambda m, *a, **k: False)
    r = sup.generar_reembolso.invoke({"numero_pedido": "P1", "monto": 100.0})
    assert "no aprobado" in r.lower()
    assert sup.registro_aprobaciones[0]["aprobado"] is False


def _resultado(herramientas, salida="listo"):
    pasos = [(SimpleNamespace(tool=h, tool_input={"x": 1}), "obs") for h in herramientas]
    return {"intermediate_steps": pasos, "output": salida}


def test_traza_guarda_acciones_y_acentos(tmp_path):
    archivo = str(tmp_path / "t.jsonl")
    tr.registrar_traza("c1", "¿Cuánto cuesta?", _resultado(["calcular_presupuesto"]), archivo)
    linea = json.loads(open(archivo, encoding="utf-8").readline())
    assert linea["acciones"][0]["herramienta"] == "calcular_presupuesto"
    assert linea["entrada"] == "¿Cuánto cuesta?"


def test_traza_sin_intermediate_steps_no_falla(tmp_path):
    archivo = str(tmp_path / "t.jsonl")
    tr.registrar_traza("c1", "hola", {"output": "hola"}, archivo)
    assert json.loads(open(archivo, encoding="utf-8").readline())["acciones"] == []


def test_marca_solo_repeticiones_consecutivas(tmp_path):
    archivo = str(tmp_path / "t.jsonl")
    tr.registrar_traza("a", "q", _resultado(["buscar", "buscar"]), archivo)
    tr.registrar_traza("b", "q", _resultado(["buscar", "calcular", "buscar"]), archivo)
    tr.registrar_traza("c", "q", _resultado(["buscar"]), archivo)
    avisos = tr.marcar_repeticiones_sospechosas(archivo)
    assert len(avisos) == 1 and "a" in avisos[0]


def test_archivo_inexistente_no_revienta(tmp_path):
    assert tr.marcar_repeticiones_sospechosas(str(tmp_path / "no.jsonl")) == []
