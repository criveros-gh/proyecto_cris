"""Pruebas offline de B29: dataset, balance y validador. Sin API."""
import json

from google.genai import types

import dataset_tuning as dt
import verificar_entorno as ve


def test_hay_al_menos_10_ejemplos_y_mas_de_una_categoria():
    assert len(dt.EJEMPLOS_RAW) >= 10
    assert len(dt.chequear_balance(dt.EJEMPLOS_RAW)) >= 2


def test_el_dataset_propio_valida_sin_problemas():
    assert dt.validar_dataset(dt.construir_examples()) == []


def test_las_categorias_coinciden_con_las_del_enrutamiento():
    usadas = set(dt.chequear_balance(dt.EJEMPLOS_RAW))
    assert usadas == dt.CATEGORIAS_VALIDAS


def test_el_balance_no_es_extremo():
    assert dt.razon_max_min(dt.chequear_balance(dt.EJEMPLOS_RAW)) <= 2.0


def test_los_textos_son_todos_distintos():
    textos = [t for t, _ in dt.EJEMPLOS_RAW]
    assert len(textos) == len(set(textos))


def test_el_output_es_json_con_comillas_dobles():
    for ej in dt.construir_examples():
        assert isinstance(json.loads(ej.output), dict)


def test_el_validador_detecta_cada_tipo_de_error():
    base = dt.construir_examples()
    rotos = base + [
        types.TuningExample(text_input="", output='{"categoria": "consulta", "prioridad": "baja"}'),
        types.TuningExample(text_input=dt.EJEMPLOS_RAW[0][0], output="no es json"),
        types.TuningExample(text_input="otro", output="{'categoria': 'consulta', 'prioridad': 'baja'}"),
        types.TuningExample(text_input="sin clave", output='{"categoria": "consulta"}'),
        types.TuningExample(text_input="valor raro", output='{"categoria": "paseo", "prioridad": "baja"}'),
    ]
    problemas = " | ".join(dt.validar_dataset(rotos))
    for esperado in ["text_input vacio", "duplicado", "no es JSON valido",
                     'no tiene la clave "prioridad"', 'categoria "paseo" no permitida']:
        assert esperado in problemas


def test_dataset_desbalanceado_se_nota_en_la_razon():
    raw = [("a", {"categoria": "emergencia"})] * 9 + [("b", {"categoria": "consulta"})]
    assert dt.razon_max_min(dt.chequear_balance(raw)) == 9.0


def test_verificar_entorno_no_imprime_la_clave(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "VALOR-SECRETO-123")
    _, lineas = ve.revisar()
    assert "GEMINI_API_KEY detectada" in lineas
    assert not any("VALOR-SECRETO-123" in l for l in lineas)
