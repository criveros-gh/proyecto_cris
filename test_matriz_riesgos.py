import pytest

import matriz_riesgos as mr


def test_puntaje_y_cortes_de_categoria():
    assert mr.puntaje_riesgo(4, 4) == 16
    casos = {1: "BAJO", 3: "BAJO", 4: "MEDIO", 8: "MEDIO", 9: "ALTO", 14: "ALTO", 15: "CRITICO", 25: "CRITICO"}
    for puntaje, esperada in casos.items():
        assert mr.categoria_riesgo(puntaje) == esperada


def test_al_limite_distingue_cerca_y_lejos():
    assert mr.esta_en_el_limite(4, 4) is True    # 16 CRITICO; con 3x4=12 seria ALTO
    assert mr.esta_en_el_limite(1, 1) is False   # 1 BAJO; ningun vecino cambia


def _fila(**cambios):
    base = {"riesgo": "r", "probabilidad": 3, "impacto": 3, "mitigacion": "algo (Bloque 1)",
            "estado": "construida", "supervision": "persona revisa"}
    base.update(cambios)
    return base


def test_validar_riesgo_detecta_problemas():
    assert mr.validar_riesgo(_fila()) == []
    assert any("impacto" in p for p in mr.validar_riesgo(_fila(impacto="4")))
    assert any("probabilidad" in p for p in mr.validar_riesgo(_fila(probabilidad=6)))
    assert any("probabilidad" in p for p in mr.validar_riesgo(_fila(probabilidad=True)))
    assert any("estado" in p for p in mr.validar_riesgo(_fila(estado="hecho")))
    fila = _fila()
    del fila["supervision"]
    assert any("supervision" in p for p in mr.validar_riesgo(fila))


def test_evaluar_matriz_ordena_no_muta_y_falla_con_fila_invalida():
    entrada = [_fila(riesgo="a", probabilidad=1, impacto=1), _fila(riesgo="b", probabilidad=5, impacto=5)]
    filas = mr.evaluar_matriz(entrada)
    assert [f["riesgo"] for f in filas] == ["b", "a"]
    assert "puntaje" not in entrada[0]
    with pytest.raises(ValueError, match="fila invalida"):
        mr.evaluar_matriz([_fila(probabilidad="3")])


def test_verificar_matriz_detecta_alto_sin_supervision_y_pocas_filas():
    filas = mr.evaluar_matriz([_fila(riesgo=str(i), probabilidad=4, impacto=4, supervision="") for i in range(5)])
    fallas = mr.verificar_matriz(filas)
    assert any("no tiene punto de supervision" in f for f in fallas)
    assert any("misma categoria" in f for f in fallas)
    assert any("menos de 5" in f for f in mr.verificar_matriz(mr.evaluar_matriz([_fila()])))


def test_la_matriz_real_cumple_las_reglas_de_la_actividad():
    filas = mr.evaluar_matriz(mr.RIESGOS)
    assert len(filas) >= 5
    assert mr.verificar_matriz(filas) == []
    assert any(f["categoria"] == "CRITICO" for f in filas)
    for f in filas:
        if f["categoria"] in ("ALTO", "CRITICO"):
            assert f["supervision"].strip()


def test_markdown_incluye_todas_las_filas():
    filas = mr.evaluar_matriz(mr.RIESGOS)
    md = mr.a_markdown(filas)
    for f in filas:
        assert f["riesgo"] in md
