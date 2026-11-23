"""Pruebas offline de B30: el metodo de decision y la coherencia del documento."""
import re

import pytest

import decision as d

DOC = open("decision_personalizacion.md", encoding="utf-8").read()


def _r(**kw):
    base = dict(informacion_cambia_seguido=False, problema_de_formato_o_tono=False,
                dataset_grande_y_de_calidad=False, presupuesto_limitado_o_iterar_rapido=False,
                necesita_multiples_variantes=False)
    base.update(kw)
    return base


def test_caso_de_la_clase_con_empate_se_reporta_completo():
    puntos, ganadoras = d.recomendar_estrategia(
        _r(problema_de_formato_o_tono=True, dataset_grande_y_de_calidad=True))
    assert puntos == {"RAG": 0, "Fine-tuning completo": 3, "PEFT": 3}
    assert ganadoras == ["Fine-tuning completo", "PEFT"]


def test_caso_de_la_clase_sin_empate():
    puntos, ganadoras = d.recomendar_estrategia(
        _r(informacion_cambia_seguido=True, problema_de_formato_o_tono=True,
           presupuesto_limitado_o_iterar_rapido=True))
    assert puntos == {"RAG": 5, "Fine-tuning completo": 1, "PEFT": 3}
    assert ganadoras == ["RAG"]


def test_un_texto_en_lugar_de_booleano_falla_en_vez_de_contar_como_verdadero():
    with pytest.raises(TypeError):
        d.recomendar_estrategia(_r(informacion_cambia_seguido="si"))


def test_cada_respuesta_del_proyecto_tiene_su_evidencia():
    for caso in (d.CASO_SERVICIO, d.CASO_CLASIFICADOR):
        assert set(caso["respuestas"]) == set(caso["evidencia"])
        assert all(len(e) > 20 for e in caso["evidencia"].values())


def test_el_documento_tiene_las_cuatro_secciones_en_orden():
    posiciones = [DOC.index(t) for t in ("## 1. El problema", "## 2. Resultado",
                                         "## 3. Técnica elegida", "## 4. Qué se necesitaría")]
    assert posiciones == sorted(posiciones)


def test_el_documento_no_deja_marcadores_sin_completar():
    assert "[COMPLETAR" not in DOC


@pytest.mark.parametrize("caso", [d.CASO_SERVICIO, d.CASO_CLASIFICADOR])
def test_los_puntajes_del_documento_coinciden_con_el_metodo(caso):
    puntos, _ = d.recomendar_estrategia(caso["respuestas"])
    for tecnica, p in puntos.items():
        assert f"- {tecnica}: {p} punto" in DOC


def test_el_documento_declara_la_ventaja_artificial_de_rag_en_el_clasificador():
    assert "solo de la pregunta del plazo" in DOC


def test_la_seccion_4_tiene_numeros():
    seccion = DOC.split("## 4. Qué se necesitaría")[1].split("## Limitaciones")[0]
    assert len(re.findall(r"\d+", seccion)) >= 5


def test_costo_de_etiquetar_los_188_que_faltan():
    horas, costo = d.estimar_costo_de_etiquetar(188, 5)
    assert round(horas, 1) == 15.7 and costo is None
